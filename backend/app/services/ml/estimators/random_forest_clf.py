"""RandomForest classifier."""

import time
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult


@ModelRegistry.register
class RandomForestClf(BaseEstimator):
    name = "random_forest_classifier"
    task = "classification"

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        defaults = {"n_estimators": 200, "random_state": 42, "n_jobs": -1}
        defaults.update(self.hyperparams)
        model = RandomForestClassifier(**defaults)
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
                "accuracy": float(accuracy_score(y_val, preds)),
                "f1_macro": float(f1_score(y_val, preds, average="macro")),
            },
            feature_importance=importances,
            train_time_sec=time.time() - t0,
        )
