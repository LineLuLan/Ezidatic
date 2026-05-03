"""Auto-train — iterate every registered estimator and rank them."""

import logging
from typing import Any

from sklearn.model_selection import train_test_split

from app.services.ml.base_estimator import ModelRegistry

log = logging.getLogger(__name__)


async def auto_train(
    X: Any,
    y: Any,
    task: str = "classification",
    test_size: float = 0.2,
    random_state: int = 42,
) -> list[dict[str, Any]]:
    """Train every registered estimator for `task`, return ranked leaderboard."""
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    results: list[dict[str, Any]] = []
    for estimator_cls in ModelRegistry.list_for_task(task):
        try:
            result = estimator_cls().fit(X_tr, y_tr, X_val, y_val)
            results.append(
                {
                    "name": estimator_cls.name,
                    "metrics": result.metrics,
                    "train_time_sec": result.train_time_sec,
                    "feature_importance": result.feature_importance,
                }
            )
        except Exception as e:  # noqa: BLE001
            log.warning("estimator %s failed: %s", estimator_cls.name, e)

    primary = "accuracy" if task == "classification" else "r2"
    return sorted(
        results,
        key=lambda r: r["metrics"].get(primary, float("-inf")),
        reverse=True,
    )
