"""BaseEstimator + ModelRegistry — every ML algorithm plugs in here."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrainResult:
    model: Any
    metrics: dict[str, float]
    feature_importance: dict[str, float] | None = None
    train_time_sec: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)


class BaseEstimator(ABC):
    name: str = "unnamed"
    task: str = "classification"  # "classification" | "regression"

    def __init__(self, **hyperparams: Any):
        self.hyperparams = hyperparams

    @abstractmethod
    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        ...


class ModelRegistry:
    _registry: dict[str, type[BaseEstimator]] = {}

    @classmethod
    def register(cls, estimator_cls: type[BaseEstimator]) -> type[BaseEstimator]:
        cls._registry[estimator_cls.name] = estimator_cls
        return estimator_cls

    @classmethod
    def get(cls, name: str) -> type[BaseEstimator]:
        return cls._registry[name]

    @classmethod
    def list_for_task(cls, task: str) -> list[type[BaseEstimator]]:
        return [c for c in cls._registry.values() if c.task == task]

    @classmethod
    def all_names(cls) -> list[str]:
        return sorted(cls._registry.keys())
