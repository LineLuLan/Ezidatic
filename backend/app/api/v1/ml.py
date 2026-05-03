"""ML endpoints — Sprint 3 (M4)."""

from fastapi import APIRouter

from app.schemas.ml import TrainRequest, TrainResponse

router = APIRouter()


@router.post("/train", response_model=TrainResponse)
async def train(_payload: TrainRequest) -> TrainResponse:
    raise NotImplementedError("Sprint 3 / M4_AUTOML: implement auto_train")


@router.get("/leaderboard/{dataset_id}")
async def leaderboard(dataset_id: str) -> list[dict]:
    raise NotImplementedError("Sprint 3 / M4_AUTOML: implement leaderboard")
