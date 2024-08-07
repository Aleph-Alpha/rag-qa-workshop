from pathlib import Path

from intelligence_layer.evaluation import (
    FileAggregationRepository,
    FileDatasetRepository,
    FileEvaluationRepository,
    FileRunRepository,
    Runner,
)
from pydantic import BaseModel, ConfigDict

REPO_ROOT_PATH = Path("repositories")


class Repositories(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    dataset_repo: FileDatasetRepository
    run_repo: FileRunRepository
    evaluation_repo: FileEvaluationRepository
    aggregation_repo: FileAggregationRepository


def init_repos() -> Repositories:
    dataset_repo = FileDatasetRepository(REPO_ROOT_PATH)
    run_repo = FileRunRepository(REPO_ROOT_PATH)
    evaluation_repo = FileEvaluationRepository(REPO_ROOT_PATH)
    aggregation_repo = FileAggregationRepository(REPO_ROOT_PATH)

    return Repositories(
        dataset_repo=dataset_repo,
        evaluation_repo=evaluation_repo,
        run_repo=run_repo,
        aggregation_repo=aggregation_repo,
    )
