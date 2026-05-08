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
    # Q5-ML-05: randomized-search candidates.
    param_distributions = {
        "n_estimators": [100, 200, 400],
        "learning_rate": [0.03, 0.05, 0.1, 0.2],
        "num_leaves": [15, 31, 63],
        "min_child_samples": [5, 10, 20],
    }

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        # Q5-ML-05: defaults dict so tuned hyperparams override cleanly.
        defaults = {"verbose": -1, "random_state": 42}
        defaults.update(self.hyperparams)
        model = LGBMClassifier(**defaults)
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
