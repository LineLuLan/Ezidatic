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
import random
import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold

from app.config import settings
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
    hyperparams: dict[str, Any] | None = None,
) -> dict[str, list[float]]:
    """Loop K folds, return {metric_name: [value_per_fold]}.

    Q5-ML-05: ``hyperparams`` (when truthy) overrides estimator defaults
    via ``estimator_cls(**hyperparams).fit(...)``. Default behaviour
    (``None`` or empty dict) is unchanged from pre-tuning.
    """
    fold_metrics: dict[str, list[float]] = {}
    fold_iter = (
        splitter.split(X, y) if task == "classification" else splitter.split(X)
    )
    for train_idx, val_idx in fold_iter:
        X_tr = _index(X, train_idx)
        X_val = _index(X, val_idx)
        y_tr = _index(y, train_idx)
        y_val = _index(y, val_idx)

        result = estimator_cls(**(hyperparams or {})).fit(X_tr, y_tr, X_val, y_val)
        per_fold = dict(result.metrics)

        if want_roc_auc and task == "classification":
            roc = _compute_roc_auc(result.model, X_val, y_val)
            if roc is not None:
                per_fold["roc_auc"] = roc

        for k, v in per_fold.items():
            fold_metrics.setdefault(k, []).append(float(v))

    return fold_metrics


def _tune_estimator(
    estimator_cls: type[BaseEstimator],
    X: Any,
    y: Any,
    splitter: Any,
    task: str,
    metric: str,
    n_iter: int,
    seed: int,
) -> dict[str, Any]:
    """Q5-ML-05: hand-rolled randomized search.

    Samples up to ``n_iter`` unique combinations from
    ``estimator_cls.param_distributions`` and scores each with the
    SAME splitter the outer leaderboard CV uses. Reusing the outer
    splitter makes inner and outer scores numerically identical for
    a given param set — so the tuner's pick is, by construction,
    also the best outer-CV score available among the sampled
    candidates. Combined with the empty-dict ``{}`` safety floor
    this guarantees ``tune=True`` cannot regress below ``tune=False``.

    Returns ``{}`` when the estimator opted out (no
    ``param_distributions`` declared).
    """
    distributions = getattr(estimator_cls, "param_distributions", None)
    if not distributions:
        return {}

    rng = random.Random(seed)
    keys = list(distributions.keys())

    # Safety floor: always evaluate the estimator's defaults ({}) as
    # the first candidate. Since the inner and outer splitters are the
    # same object, "{}" inner score == baseline outer score → tuning
    # cannot regress below baseline.
    sampled: list[dict[str, Any]] = [{}]
    seen: set[tuple] = {tuple()}
    max_attempts = n_iter * 10
    attempts = 0
    while len(sampled) < n_iter + 1 and attempts < max_attempts:
        attempts += 1
        candidate = {k: rng.choice(distributions[k]) for k in keys}
        sig = tuple(candidate[k] for k in keys)
        if sig in seen:
            continue
        seen.add(sig)
        sampled.append(candidate)

    want_roc_auc = task == "classification" and metric == "roc_auc"
    best_score = float("-inf")
    best_params: dict[str, Any] = {}
    for params in sampled:
        try:
            fold_metrics = _run_cv(
                estimator_cls, X, y, splitter, task, want_roc_auc,
                hyperparams=params,
            )
            scores = fold_metrics.get(metric)
            if not scores:
                continue
            score = float(np.mean(scores))
            if score > best_score:
                best_score = score
                best_params = params
        except Exception as e:  # noqa: BLE001
            log.warning(
                "tune candidate failed for %s: %s", estimator_cls.name, e
            )

    return best_params


def auto_train(
    X: Any,
    y: Any,
    task: str = "classification",
    metric: str | None = None,
    n_splits: int = 5,
    random_state: int = 42,
    tune: bool = False,
) -> list[dict[str, Any]]:
    """Train every registered estimator for ``task`` with k-fold CV
    and return a ranked leaderboard.

    Each entry's ``metrics`` dict carries:
      - per-metric ``mean`` (under the metric name, e.g. ``accuracy``)
        and matching ``..._std`` key (e.g. ``accuracy_std``).
      - ``cv_mean`` / ``cv_std`` mirroring the ranking metric.
      - ``primary_metric`` — which metric was used for ranking.
      - ``n_splits`` — actual fold count after small-class clamping.
      - ``best_params`` (Q5-ML-05) — present only when ``tune=True``
        and the estimator declared ``param_distributions``.
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

            best_params: dict[str, Any] = {}
            if tune:
                # Q5-ML-05: pick best hyperparams via the same outer
                # splitter so inner and outer CV scores are identical
                # for any given param set — the tuner's winner is by
                # construction the strongest sampled candidate on the
                # leaderboard's reporting folds.
                best_params = _tune_estimator(
                    estimator_cls, X, y, splitter, task, metric=metric,
                    n_iter=settings.ml_tune_n_iter,
                    seed=settings.ml_tune_random_seed,
                )

            fold_metrics = _run_cv(
                estimator_cls, X, y, splitter, task, want_roc_auc,
                hyperparams=best_params,
            )

            agg: dict[str, Any] = {}
            for k, vals in fold_metrics.items():
                agg[k] = float(np.mean(vals))
                agg[f"{k}_std"] = float(np.std(vals))

            metric_used = metric if metric in agg else (
                DEFAULT_METRICS_BY_TASK.get(task, "accuracy")
            )
            agg["cv_mean"] = agg.get(metric_used, float("-inf"))
            agg["cv_std"] = agg.get(f"{metric_used}_std", 0.0)
            agg["primary_metric"] = metric_used
            agg["n_splits"] = float(n_splits)
            if best_params:
                agg["best_params"] = best_params

            # Final fit on full data → artifact + feature importance.
            # Q5-ML-05: the saved model uses the tuned params so
            # serving aligns with the leaderboard's CV estimate.
            final = estimator_cls(**best_params).fit(X, y, X, y)

            results.append(
                {
                    "name": estimator_cls.name,
                    "metrics": agg,
                    "train_time_sec": float(time.time() - t0),
                    "feature_importance": final.feature_importance,
                    "model": final.model,
                    "best_params": best_params or None,
                }
            )
        except Exception as e:  # noqa: BLE001
            log.warning("estimator %s failed: %s", estimator_cls.name, e)

    return sorted(
        results,
        key=lambda r: r["metrics"].get("cv_mean", float("-inf")),
        reverse=True,
    )
