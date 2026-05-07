"""Auto-train — iterate every registered estimator and rank them.

Sprint 5 Q5-ML-03 + Q5-ML-04 refactor:

- Replaced the single ``train_test_split(test_size=0.2)`` with k-fold
  cross-validation (``StratifiedKFold`` for classification, ``KFold``
  for regression). Default k=5; auto-shrinks for tiny minority classes.
- Each estimator's per-fold metrics are aggregated into mean + std and
  exposed under both the metric name (e.g. ``accuracy``) and the
  paired ``..._std`` key, plus a uniform ``cv_mean`` / ``cv_std`` pair
  for the ranking metric.
- ``auto_train(metric=...)`` lets callers rank by accuracy, f1_macro,
  roc_auc (classification) or r2 (regression). Falls back to the
  task default if the requested metric isn't computable.
- The artifact + feature_importance come from a final fit on the full
  dataset, so the saved model isn't just one of the CV folds.
"""

import logging
import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold

from app.services.ml.base_estimator import BaseEstimator, ModelRegistry

log = logging.getLogger(__name__)

DEFAULT_METRICS_BY_TASK: dict[str, str] = {
    "classification": "accuracy",
    "regression": "r2",
}


def _compute_roc_auc(model: Any, X_val: Any, y_val: Any) -> float | None:
    """Best-effort roc_auc on a fitted model. Returns None on failure.

    Logistic regression saves a ``(scaler, classifier)`` tuple — unpack
    so we can call ``predict_proba`` on the scaled features.
    """
    if isinstance(model, tuple) and len(model) == 2:
        scaler, clf = model
        try:
            X_val = scaler.transform(X_val)
        except Exception:  # noqa: BLE001
            return None
    else:
        clf = model
    if not hasattr(clf, "predict_proba"):
        return None
    try:
        probas = clf.predict_proba(X_val)
        n_classes = probas.shape[1]
        if n_classes == 2:
            return float(roc_auc_score(y_val, probas[:, 1]))
        if n_classes > 2:
            return float(
                roc_auc_score(y_val, probas, multi_class="ovr")
            )
    except Exception:  # noqa: BLE001
        return None
    return None


def _index(arr: Any, idx: np.ndarray) -> Any:
    if hasattr(arr, "iloc"):
        return arr.iloc[idx]
    return arr[idx]


def _pick_n_splits(y: Any, n_splits: int, task: str) -> int:
    if task != "classification":
        return n_splits
    counts = pd.Series(y).value_counts()
    if counts.empty:
        return n_splits
    min_count = int(counts.min())
    return max(2, min(n_splits, min_count))


def _run_cv(
    estimator_cls: type[BaseEstimator],
    X: Any,
    y: Any,
    splitter: Any,
    task: str,
    want_roc_auc: bool,
) -> dict[str, list[float]]:
    """Loop K folds, return {metric_name: [value_per_fold]}."""
    fold_metrics: dict[str, list[float]] = {}
    fold_iter = (
        splitter.split(X, y) if task == "classification" else splitter.split(X)
    )
    for train_idx, val_idx in fold_iter:
        X_tr = _index(X, train_idx)
        X_val = _index(X, val_idx)
        y_tr = _index(y, train_idx)
        y_val = _index(y, val_idx)

        result = estimator_cls().fit(X_tr, y_tr, X_val, y_val)
        per_fold = dict(result.metrics)

        if want_roc_auc and task == "classification":
            roc = _compute_roc_auc(result.model, X_val, y_val)
            if roc is not None:
                per_fold["roc_auc"] = roc

        for k, v in per_fold.items():
            fold_metrics.setdefault(k, []).append(float(v))

    return fold_metrics


def auto_train(
    X: Any,
    y: Any,
    task: str = "classification",
    metric: str | None = None,
    n_splits: int = 5,
    random_state: int = 42,
) -> list[dict[str, Any]]:
    """Train every registered estimator for ``task`` with k-fold CV
    and return a ranked leaderboard.

    Each entry's ``metrics`` dict carries:
      - per-metric ``mean`` (under the metric name, e.g. ``accuracy``)
        and matching ``..._std`` key (e.g. ``accuracy_std``).
      - ``cv_mean`` / ``cv_std`` mirroring the ranking metric.
      - ``primary_metric`` — which metric was used for ranking.
      - ``n_splits`` — actual fold count after small-class clamping.
    """
    if metric is None:
        metric = DEFAULT_METRICS_BY_TASK.get(task, "accuracy")

    n_splits = _pick_n_splits(y, n_splits, task)
    if task == "classification":
        splitter = StratifiedKFold(
            n_splits=n_splits, shuffle=True, random_state=random_state
        )
    else:
        splitter = KFold(
            n_splits=n_splits, shuffle=True, random_state=random_state
        )

    want_roc_auc = task == "classification" and metric == "roc_auc"

    results: list[dict[str, Any]] = []
    for estimator_cls in ModelRegistry.list_for_task(task):
        try:
            t0 = time.time()
            fold_metrics = _run_cv(
                estimator_cls, X, y, splitter, task, want_roc_auc
            )

            agg: dict[str, float] = {}
            for k, vals in fold_metrics.items():
                agg[k] = float(np.mean(vals))
                agg[f"{k}_std"] = float(np.std(vals))

            metric_used = metric if metric in agg else (
                DEFAULT_METRICS_BY_TASK.get(task, "accuracy")
            )
            agg["cv_mean"] = agg.get(metric_used, float("-inf"))
            agg["cv_std"] = agg.get(f"{metric_used}_std", 0.0)
            agg["primary_metric"] = metric_used  # type: ignore[assignment]
            agg["n_splits"] = float(n_splits)

            # Final fit on full data → artifact + feature importance.
            final = estimator_cls().fit(X, y, X, y)

            results.append(
                {
                    "name": estimator_cls.name,
                    "metrics": agg,
                    "train_time_sec": float(time.time() - t0),
                    "feature_importance": final.feature_importance,
                    "model": final.model,
                }
            )
        except Exception as e:  # noqa: BLE001
            log.warning("estimator %s failed: %s", estimator_cls.name, e)

    return sorted(
        results,
        key=lambda r: r["metrics"].get("cv_mean", float("-inf")),
        reverse=True,
    )
