"""Chat schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Role = Literal["user", "assistant", "tool", "system"]


class ChatMessageIn(BaseModel):
    content: str
    dataset_id: str | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: Role
    content: str | None
    tool_calls: list[dict[str, Any]] | None = None
    provider_used: str | None = None
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    dataset_id: str | None
    created_at: datetime
