"""BaseTool + ToolRegistry — agent function-calling layer."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    name: str = "unnamed"
    description: str = ""
    args_schema: type[BaseModel]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        ...

    def to_openai_function(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }


class ToolRegistry:
    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> BaseTool:
        cls._tools[tool.name] = tool
        return tool

    @classmethod
    def get(cls, name: str) -> BaseTool:
        return cls._tools[name]

    @classmethod
    def all_schemas(cls) -> list[dict[str, Any]]:
        return [t.to_openai_function() for t in cls._tools.values()]

    @classmethod
    def all_names(cls) -> list[str]:
        return sorted(cls._tools.keys())
