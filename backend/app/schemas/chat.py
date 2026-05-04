"""Chat schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

Role = Literal["user", "assistant", "tool", "system"]


class ChatSessionCreate(BaseModel):
    dataset_id: UUID | None = None
    title: str | None = None


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    dataset_id: UUID | None
    created_at: datetime

    @field_serializer("id")
    def _serialize_id(self, value: UUID) -> str:
        return str(value)

    @field_serializer("dataset_id", when_used="unless-none")
    def _serialize_dataset_id(self, value: UUID | None) -> str | None:
        return str(value) if value else None


class ChatMessageIn(BaseModel):
    content: str
    dataset_id: UUID | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: Role
    content: str | None
    tool_calls: list[dict[str, Any]] | None = None
    token_usage: dict[str, Any] | None = None
    provider_used: str | None = None
    created_at: datetime

    @field_serializer("id", "session_id")
    def _serialize_uuid(self, value: UUID) -> str:
        return str(value)
