"""LightGBM classifier — sample BaseEstimator implementation."""

import time
from typing import Any

from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, f1_score

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult


@ModelRegistry.register
class LightGBMClassifier(BaseEstimator):
    name = "lightgbm_classifier"
    task = "classification"

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        model = LGBMClassifier(verbose=-1, **self.hyperparams)
        model.fit(X_train, y_train)
        preds = model.predict(X_val)

        importances = None
        try:
            cols = list(X_train.columns)  # pandas / polars w/ columns attr
            importances = dict(zip(cols, [float(v) for v in model.feature_importances_]))
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
