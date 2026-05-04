"""Logistic regression classifier."""

import time
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry, TrainResult


@ModelRegistry.register
class LogisticReg(BaseEstimator):
    """Logistic regression with built-in StandardScaler — sklearn requires
    scaled features for LBFGS to converge reliably on real data."""

    name = "logistic_regression"
    task = "classification"

    def fit(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainResult:
        t0 = time.time()
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)

        defaults = {"max_iter": 1000, "random_state": 42}
        defaults.update(self.hyperparams)
        model = LogisticRegression(**defaults)
        model.fit(X_train_s, y_train)
        preds = model.predict(X_val_s)

        importances: dict[str, float] | None = None
        try:
            cols = list(X_train.columns)
            # Use mean absolute coefficient across classes as importance.
            coefs = np.asarray(model.coef_)
            if coefs.ndim == 1:
                magnitudes = np.abs(coefs)
            else:
                magnitudes = np.abs(coefs).mean(axis=0)
            importances = dict(
                zip(cols, [float(v) for v in magnitudes.tolist()])
            )
        except Exception:  # noqa: BLE001
            pass

        return TrainResult(
            model=(scaler, model),
            metrics={
                "accuracy": float(accuracy_score(y_val, preds)),
                "f1_macro": float(f1_score(y_val, preds, average="macro")),
            },
            feature_importance=importances,
            train_time_sec=time.time() - t0,
        )
