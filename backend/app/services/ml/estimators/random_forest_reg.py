"""RandomForest regressor."""

import math
import time
from typing import Any

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult


@ModelRegistry.register
class RandomForestReg(BaseEstimator):
    name = "random_forest_regressor"
    task = "regression"
    # Q5-ML-05: randomized-search candidates (same as the classifier
    # — RF tree-knob space is identical for regression).
    param_distributions = {
        "n_estimators": [100, 200, 400],
        "max_depth": [None, 8, 16, 32],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2", None],
    }

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        defaults = {"n_estimators": 200, "random_state": 42, "n_jobs": -1}
        defaults.update(self.hyperparams)
        model = RandomForestRegressor(**defaults)
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
