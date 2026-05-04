"""Preprocessing step registry.

Adding a new step = (1) write a new file under steps/, (2) import it here,
(3) add one entry to STEP_REGISTRY. The endpoint resolves by name via
build_step().
"""

from typing import Any

from app.core.exceptions import ValidationError
from app.services.preprocessing.steps.base import BaseStep, StepResult
from app.services.preprocessing.steps.encode_categorical import EncodeCategorical
from app.services.preprocessing.steps.handle_missing import HandleMissingValues
from app.services.preprocessing.steps.remove_outliers import RemoveOutliers

STEP_REGISTRY: dict[str, type[BaseStep]] = {
    HandleMissingValues.name: HandleMissingValues,
    RemoveOutliers.name: RemoveOutliers,
    EncodeCategorical.name: EncodeCategorical,
}


def build_step(name: str, params: dict[str, Any] | None = None) -> BaseStep:
    cls = STEP_REGISTRY.get(name)
    if cls is None:
        raise ValidationError(f"Unknown step: {name}", code="unknown_step")
    return cls(**(params or {}))


__all__ = [
    "BaseStep",
    "StepResult",
    "HandleMissingValues",
    "RemoveOutliers",
    "EncodeCategorical",
    "STEP_REGISTRY",
    "build_step",
]
