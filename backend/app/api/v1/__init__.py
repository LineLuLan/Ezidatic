"""v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, chat, datasets, eda, ml

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(eda.router, prefix="/eda", tags=["eda"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
