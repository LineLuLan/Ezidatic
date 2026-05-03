"""EDA endpoints — Sprint 2 (M3)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{dataset_id}/profile")
async def get_profile(dataset_id: str) -> dict:
    raise NotImplementedError("Sprint 2 / M3_EDA_CHARTS: implement profile")


@router.get("/{dataset_id}/charts")
async def list_charts(dataset_id: str) -> list[dict]:
    raise NotImplementedError("Sprint 2 / M3_EDA_CHARTS: implement chart list")
