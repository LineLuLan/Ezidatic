"""Dataset endpoints — Sprint 1 (M1)."""

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("")
async def upload_dataset(_file: UploadFile) -> dict:
    raise NotImplementedError("Sprint 1 / M1_INGESTION: implement upload")


@router.get("")
async def list_datasets() -> list[dict]:
    raise NotImplementedError("Sprint 1 / M1_INGESTION: implement list")


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str) -> dict:
    raise NotImplementedError("Sprint 1 / M1_INGESTION: implement detail")
