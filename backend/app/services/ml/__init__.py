"""ML subsystem — importing triggers estimator registry population."""

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult
from app.services.ml.estimators import lightgbm_clf  # noqa: F401  (registers)

__all__ = ["BaseEstimator", "ModelRegistry", "TrainResult"]
