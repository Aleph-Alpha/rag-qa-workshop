import os
from typing import Iterator
from intelligence_layer.core.model import LuminousControlModel
from intelligence_layer.core.text_highlight import ScoredTextHighlight
from intelligence_layer.core.tracer.tracer import NoOpTracer
from intelligence_layer.examples import (
    MultipleChunkRetrieverQa,
    MultipleChunkRetrieverQaOutput,
    RetrieverBasedQaInput,
)
import streamlit as st

from intelligence_layer.connectors import (
    CollectionPath,
    DocumentIndexClient,
    DocumentIndexRetriever,
)
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv(), override=True)

AA_TOKEN = os.getenv("AA_TOKEN")
NAMESPACE = os.getenv("AA_NAMESPACE")

if AA_TOKEN is None or NAMESPACE is None:
    raise Exception("No AA_TOKEN or NAMESPACE provided.")

di_client = DocumentIndexClient(token=os.getenv("AA_TOKEN"))


def run_task(
    collection_name: str, index_name: str, user_prompt: str
) -> MultipleChunkRetrieverQaOutput:
    raise Exception("Not implemented")


HTML_HIGHLIGHT_START = '<span style="background: yellow;">'
HTML_HIGHLIGHT_END = "</span>"


def text_ranges(
    source_text: str, highlights: list[ScoredTextHighlight]
) -> Iterator[str]:
    def wrap_highlights(text: str) -> str:
        return HTML_HIGHLIGHT_START + text + HTML_HIGHLIGHT_END

    if not highlights:
        yield source_text

    current_pos = 0
    highlights.sort(key=lambda x: x.start)
    for highlight in highlights:
        if current_pos < highlight.start:
            yield source_text[current_pos : highlight.start]
        current_pos = highlight.end
        if highlight.start >= current_pos:
            raise ValueError("Overlapping Highlights detected")
        yield wrap_highlights(source_text[max(0, highlight.start) : current_pos])
    last_highlight = highlights[-1] if highlights else None
    if last_highlight and last_highlight.end < len(source_text):
        yield wrap_highlights(source_text[last_highlight.end :])


def display_response(task_output: MultipleChunkRetrieverQaOutput):
    answer = task_output.answer

    st.write(answer)
    st.divider()

    for source in task_output.sources:
        text = source.chunk.chunk

        highlights = sorted(source.highlights, key=lambda highlight: highlight.start)

        highlighted_text = "".join(text_ranges(text, highlights))

        st.write(
            highlighted_text,
            unsafe_allow_html=True,
        )
        st.divider()


def main():
    st.title("Frage & Antwort")

    with st.sidebar:
        st.write("### Collection")
        collections = []

        collections = di_client.list_collections(NAMESPACE)  # type: ignore

        collection_name = st.selectbox(
            label="Collection auswählen",
            options=[collection.collection for collection in collections],
        )

        if collection_name is None:
            raise Exception("No collection selected.")

        st.write("### Index")
        indexes = []
        collection_path = CollectionPath(
            namespace=NAMESPACE,  # type: ignore
            collection=collection_name,
        )
        indexes = di_client.list_assigned_index_names(collection_path)
        index_name = st.selectbox(label="Index auswählen", options=indexes)

        if index_name is None:
            raise Exception("No index selected.")

    user_prompt = st.text_input(
        "Frage", placeholder="Warum ist der Himmel blau?", label_visibility="hidden"
    )

    if st.button("Antwort finden", use_container_width=True):
        with st.spinner("Lädt..."):
            task_output = run_task(collection_name, index_name, user_prompt)
        display_response(task_output)


if __name__ == "__main__":
    main()
