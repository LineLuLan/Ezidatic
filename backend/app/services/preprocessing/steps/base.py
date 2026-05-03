"""BaseStep — every preprocessing step inherits from this."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import polars as pl


@dataclass
class StepResult:
    df: pl.DataFrame
    log: dict[str, Any] = field(default_factory=dict)


class BaseStep(ABC):
    name: str = "unnamed"

    def __init__(self, **params: Any):
        self.params = params

    @abstractmethod
    def apply(self, df: pl.DataFrame) -> StepResult:
        ...
