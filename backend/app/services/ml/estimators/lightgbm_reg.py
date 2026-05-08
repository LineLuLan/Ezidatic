"""LightGBM regressor."""

import math
import time
from typing import Any

from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult


@ModelRegistry.register
class LightGBMReg(BaseEstimator):
    name = "lightgbm_regressor"
    task = "regression"
    # Q5-ML-05: randomized-search candidates.
    param_distributions = {
        "n_estimators": [100, 200, 400],
        "learning_rate": [0.03, 0.05, 0.1, 0.2],
        "num_leaves": [15, 31, 63],
        "min_child_samples": [5, 10, 20],
    }

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        defaults = {"verbose": -1, "random_state": 42}
        defaults.update(self.hyperparams)
        model = LGBMRegressor(**defaults)
        model.fit(X_train, y_train)
        preds = model.predict(X_val)

        importances: dict[str, float] | None = None
        try:
            cols = list(X_train.columns)
            importances = dict(
                zip(cols, [float(v) for v in model.feature_importances_])
            )
        except Exception:  # noqa: BLE001
            pass

        return TrainResult(
            model=model,
            metrics={
                "r2": float(r2_score(y_val, preds)),
                "mae": float(mean_absolute_error(y_val, preds)),
                "rmse": float(math.sqrt(mean_squared_error(y_val, preds))),
            },
            feature_importance=importances,
            train_time_sec=time.time() - t0,
        )
