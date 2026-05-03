"""Importing this triggers tool registry population."""

from app.services.agents.tools import query_dataset  # noqa: F401  (registers)
from app.services.agents.tools.base import BaseTool, ToolRegistry

__all__ = ["BaseTool", "ToolRegistry"]
