from pathlib import Path
from typing import Iterable, Optional
from statistics import mean
import json

from intelligence_layer.core.model import CompleteInput, ControlModel
from intelligence_layer.evaluation import (
    AggregationLogic,
    AggregationRepository,
    Example,
    FileAggregationRepository,
    SingleOutputEvaluationLogic,
    aggregation_overviews_to_pandas,
)
from intelligence_layer.examples import (
    RetrieverBasedQaInput,
    MultipleChunkRetrieverQaOutput,
)


from intelligence_layer.core import (
    FileTracer,
    Llama3InstructModel,
    NoOpTracer,
    Task,
    TaskSpan,
    TextChunk,
)
from pydantic import BaseModel


class WorldKnowledgeGradingInput(BaseModel):
    reference_text: str
    compare_text: str


class WorldKnowledgeGradingOutput(BaseModel):
    reasoning: str
    contains_world_knowledge: bool


class WorldKnowledgeGrader(
    Task[WorldKnowledgeGradingInput, WorldKnowledgeGradingOutput]
):
    reasoning_key = "explanation"
    no_world_knowledge_key = "only_from_reference_text"

    INSTRUCTION = f"""Deine Aufgabe ist es, nachzuvollziehen, ob alle Informationen in dem Vergleichstext aus dem Referenztext hervorgehen.
Beachte dabei folgende Kriterien:
1. Ein guter Vergleichstext darf nur Informationen enthalten die auch im Referenztext vorkommen.
2. Ein guter Vergleichstext darf weniger Details als der Referenztext enhalten (z.B. den Text vereinfachen), solange er vollständig aus dem Referenztext hervorgeht.

Der Informationsgehalt des Vergleichstextes darf niemals über den Informationsgehalt des Referenztextes hinausgehen.

Gebe die Antwort im folgenden JSON-Format:
{{
    "{reasoning_key}": str (Begründe, ob alle Informationen in dem Vergleichstext auch im Referenztext enthalten sind),
    "{no_world_knowledge_key}": bool ("True" wenn alle informationen aus dem Vergleichstext auch im Referenztext vorkommen, "False" wenn zusätzliche Informationen im Vergleichstext vorkommen)
}}
Antworte ausschließlich mit dem JSON Blob."""

    INPUT_TEMPLATE = """# Referenztext
```
{reference_text}
```

# Vergleichstext
```
{compare_text}
```"""

    def __init__(self, model: ControlModel):
        super().__init__()
        self._model = model

    def do_run(
        self, input: WorldKnowledgeGradingInput, task_span: TaskSpan
    ) -> WorldKnowledgeGradingOutput:
        prompt = self._model.to_instruct_prompt(
            self.INSTRUCTION,
            self.INPUT_TEMPLATE.format(
                reference_text=input.reference_text, compare_text=input.compare_text
            ),
        )
        model_input = CompleteInput(prompt=prompt, maximum_tokens=256)

        response = self._model.complete(model_input, task_span)
        return self._calculate_output(response.completion)

    def _calculate_output(self, message_content: str) -> WorldKnowledgeGradingOutput:
        try:
            json_response = json.loads(message_content)
        except Exception as e:
            print(message_content)
            raise e

        return WorldKnowledgeGradingOutput(
            reasoning=json_response[self.reasoning_key],
            contains_world_knowledge=not json_response[self.no_world_knowledge_key],
        )


class RetrieverQaEvaluation(BaseModel):
    answer_generated: bool
    world_knowledge_grading_output: Optional[WorldKnowledgeGradingOutput]


class RetrieverQaEvaluationLogic(
    SingleOutputEvaluationLogic[
        RetrieverBasedQaInput,
        MultipleChunkRetrieverQaOutput,
        None,
        RetrieverQaEvaluation,
    ],
):
    def __init__(self) -> None:
        self._world_knowledge_grader = WorldKnowledgeGrader(
            Llama3InstructModel("llama-3.1-70b-instruct")
        )

    def do_evaluate_single_output(
        self,
        example: Example[RetrieverBasedQaInput, None],
        output: MultipleChunkRetrieverQaOutput,
    ) -> RetrieverQaEvaluation:
        # tracer = FileTracer(f"eval_tracer/{example.id}")
        tracer = NoOpTracer()
        answer_generated = bool(output.answer)
        if not answer_generated:
            return RetrieverQaEvaluation(
                answer_generated=answer_generated,
                world_knowledge_grading_output=None,
            )

        assert output.answer

        chunk_for_prompt = TextChunk(
            "\n\n".join(source.chunk.chunk for _, source in enumerate(output.sources))
            + "\n\n"
            + example.input.question
        )

        world_knowledge_output = self._world_knowledge_grader.run(
            input=WorldKnowledgeGradingInput(
                reference_text=chunk_for_prompt,
                compare_text=output.answer,
            ),
            tracer=tracer,
        )

        return RetrieverQaEvaluation(
            answer_generated=answer_generated,
            world_knowledge_grading_output=world_knowledge_output,
        )


class AggregatedRetrieverQaEvaluation(BaseModel):
    contains_no_world_knowledge: float
    n_answers_generated: int


class RetrieverQaAggregationLogic(
    AggregationLogic[RetrieverQaEvaluation, AggregatedRetrieverQaEvaluation]
):
    def aggregate(
        self,
        evaluations: Iterable[RetrieverQaEvaluation],
    ) -> AggregatedRetrieverQaEvaluation:
        evaluations = list(evaluations)

        contains_no_world_knowledge = 1 - mean(
            e.world_knowledge_grading_output.contains_world_knowledge
            for e in evaluations
            if e.world_knowledge_grading_output
        )

        n_answers_generated = sum(e.answer_generated for e in evaluations)
        return AggregatedRetrieverQaEvaluation(
            contains_no_world_knowledge=contains_no_world_knowledge,
            n_answers_generated=n_answers_generated,
        )
