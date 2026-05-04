"""ML subsystem — importing triggers estimator registry population.

Every estimator file uses ``@ModelRegistry.register``. Adding a new one =
write the file + import it here. No other change is needed.
"""

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult
from app.services.ml.estimators import (  # noqa: F401  (registers)
    lightgbm_clf,
    lightgbm_reg,
    logistic_reg,
    random_forest_clf,
    random_forest_reg,
)

__all__ = ["BaseEstimator", "ModelRegistry", "TrainResult"]
