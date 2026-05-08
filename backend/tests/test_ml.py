"""AutoML endpoint + registry tests — M4."""

from pathlib import Path

import joblib
import pytest
from httpx import AsyncClient

from app.services.ml import ModelRegistry


# Iris-like 4 numeric features + species target.
# Lift slightly so multiple models actually distinguish classes.
CLASSIFICATION_CSV = (
    "sepal_length,sepal_width,petal_length,petal_width,species\n"
    + "\n".join(
        f"{5.0 + (i % 3) * 0.4},{3.0 + (i % 4) * 0.2},"
        f"{1.5 + (i % 5) * 0.3},{0.3 + (i % 4) * 0.2},"
        f"{'setosa' if i % 3 == 0 else 'versicolor' if i % 3 == 1 else 'virginica'}"
        for i in range(60)
    )
    + "\n"
)

# Synthetic regression: y = 2x1 - x2 + noise
REGRESSION_CSV = (
    "x1,x2,y\n"
    + "\n".join(
        f"{i},{i % 7},{2 * i - (i % 7) + (i % 3 - 1)}" for i in range(80)
    )
    + "\n"
)


def test_registry_lists_all_sprint3_estimators() -> None:
    names = set(ModelRegistry.all_names())
    assert {
        "lightgbm_classifier",
        "lightgbm_regressor",
        "logistic_regression",
        "random_forest_classifier",
        "random_forest_regressor",
    }.issubset(names)


@pytest.mark.asyncio
async def test_train_classification_returns_leaderboard(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert body["task_type"] == "classification"
    assert len(body["leaderboard"]) >= 3  # 3 classifiers registered
    # Leaderboard sorted by accuracy desc.
    accuracies = [e["metrics"]["accuracy"] for e in body["leaderboard"]]
    assert accuracies == sorted(accuracies, reverse=True)
    # Best entry has feature_importance from a tree-based model.
    assert body["best"]["feature_importance"] is not None
    # Artifact persisted on disk.
    assert body["artifact_path"]
    assert Path(body["artifact_path"]).exists()


@pytest.mark.asyncio
async def test_train_regression_returns_r2_sorted(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("reg.csv", REGRESSION_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "y",
            "task_type": "regression",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["task_type"] == "regression"
    assert len(body["leaderboard"]) >= 2
    r2_values = [e["metrics"]["r2"] for e in body["leaderboard"]]
    assert r2_values == sorted(r2_values, reverse=True)
    # Synthetic linear data → top model should fit reasonably well.
    assert body["best"]["metrics"]["r2"] > 0.8


@pytest.mark.asyncio
async def test_leaderboard_endpoint_returns_persisted_runs(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
    )
    response = await auth_client.get(f"/api/v1/ml/leaderboard/{dataset_id}")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 3
    # Exactly one row carries an artifact_path (the best one).
    with_artifact = [r for r in rows if r["artifact_path"]]
    assert len(with_artifact) == 1


@pytest.mark.asyncio
async def test_train_unknown_target_returns_422(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "not_a_real_column",
            "task_type": "classification",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "missing_target"


@pytest.mark.asyncio
async def test_train_404_for_other_workspace(
    auth_client: AsyncClient, client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "other-ml@example.com", "password": "supersecret"},
    )
    other_token = register.json()["access_token"]

    response = await client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404


# ----------------------------- Sprint 5 P0 -----------------------------------
# Q5-ML-01 (median/mode imputation) + Q5-ML-02 (auto-encode categorical).

# Mixed-dtype classification: 2 categorical + 1 numeric → binary target.
def _make_categorical_csv() -> str:
    departments = ["eng", "sales", "hr", "ops", "design"]
    countries = ["VN", "US", "JP"]
    bands = ["low", "high"]
    rows = ["department,country,years_exp,salary_band"]
    for i in range(60):
        dept = departments[i % len(departments)]
        country = countries[i % len(countries)]
        years = i % 15
        # "high" if eng and >5y, or sales and >8y; cheap signal so LightGBM
        # fits something non-trivial.
        band = "high" if (dept == "eng" and years > 5) or (
            dept == "sales" and years > 8
        ) else "low"
        rows.append(f"{dept},{country},{years},{band}")
    return "\n".join(rows) + "\n"


# Regression with NaN injection on x1.
def _make_nan_regression_csv() -> str:
    rows = ["x1,x2,y"]
    for i in range(80):
        # 10% NaN rate in x1.
        x1 = "" if i % 10 == 0 else str(i)
        x2 = i % 7
        y = 2 * i - x2 + (i % 3 - 1)
        rows.append(f"{x1},{x2},{y}")
    return "\n".join(rows) + "\n"


# 250 rows so `email` column has 250 unique values (cardinality > 200 → drop).
# `user_id` column has 50 unique values (in 20..200 → label encode).
def _make_high_card_csv() -> str:
    rows = ["user_id,email,target"]
    for i in range(250):
        user_id = f"u{i % 50}"  # 50 unique
        email = f"user{i}@example.com"  # 250 unique
        target = i % 3  # 3-class
        rows.append(f"{user_id},{email},{target}")
    return "\n".join(rows) + "\n"


@pytest.mark.asyncio
async def test_train_classification_with_categorical_features(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-02: mixed-dtype CSV trains successfully with auto-encoding."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "mixed.csv",
                _make_categorical_csv().encode("utf-8"),
                "text/csv",
            )
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "salary_band",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["leaderboard"]) >= 3
    encoded = body["extras"]["encoded_columns"]
    assert "department" in encoded and encoded["department"].startswith("one_hot")
    assert "country" in encoded and encoded["country"].startswith("one_hot")
    # Best model's feature_importance must include encoded categorical keys.
    importance_keys = set(body["best"]["feature_importance"].keys())
    has_dept_dummy = any(k.startswith("department_") for k in importance_keys)
    assert has_dept_dummy, importance_keys


@pytest.mark.asyncio
async def test_train_with_nan_uses_median_imputation(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-01: NaN-bearing column gets median-imputed by default."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "nanreg.csv",
                _make_nan_regression_csv().encode("utf-8"),
                "text/csv",
            )
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "y",
            "task_type": "regression",
            "imputation": "median",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    imputed = body["extras"]["imputed_columns"]
    assert "x1" in imputed
    assert imputed["x1"].startswith("median(")
    # 10% NaN imputation degrades synthetic linear fit; expect r2 > 0.3
    # (was > 0.8 on the no-NaN regression fixture — drop is expected).
    assert body["best"]["metrics"]["r2"] > 0.3


@pytest.mark.asyncio
async def test_train_high_cardinality_categorical_dropped(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-02: cardinality > 200 → drop; 20<card<=200 → label encode."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "highcard.csv",
                _make_high_card_csv().encode("utf-8"),
                "text/csv",
            )
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "target",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    extras = body["extras"]
    assert "email" in extras["dropped_high_card"]
    assert extras["encoded_columns"]["user_id"].startswith("label(")


# ----------------------------- Sprint 5 P1 -----------------------------------
# Q5-ML-03 (5-fold CV reporting) + Q5-ML-04 (imbalance + metric selection).


def _make_imbalanced_csv() -> str:
    """100-row 90/10 imbalanced binary classification."""
    rows = ["x1,x2,target"]
    for i in range(100):
        target = "high" if i < 10 else "low"
        x1 = i + (5 if target == "high" else 0)
        x2 = (i % 7) + (3 if target == "high" else 0)
        rows.append(f"{x1},{x2},{target}")
    return "\n".join(rows) + "\n"


@pytest.mark.asyncio
async def test_leaderboard_entries_carry_cv_mean_and_std(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-03: every leaderboard entry exposes cv_mean + cv_std."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv"
            )
        },
    )
    dataset_id = upload.json()["id"]
    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for entry in body["leaderboard"]:
        assert "cv_mean" in entry["metrics"], entry["metrics"]
        assert "cv_std" in entry["metrics"], entry["metrics"]
        assert "primary_metric" in entry["metrics"]
        assert entry["metrics"]["primary_metric"] == "accuracy"
        # accuracy_std (per-metric std) surfaces alongside accuracy.
        assert "accuracy_std" in entry["metrics"]
    # Default n_splits = 5 (60-row Iris fixture has 20 per class).
    assert body["best"]["metrics"]["n_splits"] == 5


@pytest.mark.asyncio
async def test_train_with_metric_f1_macro_ranks_by_f1(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-04: explicit metric=f1_macro ranks the leaderboard by f1."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv"
            )
        },
    )
    dataset_id = upload.json()["id"]
    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
            "metric": "f1_macro",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    f1_values = [e["metrics"]["f1_macro"] for e in body["leaderboard"]]
    assert f1_values == sorted(f1_values, reverse=True)
    cv_means = [e["metrics"]["cv_mean"] for e in body["leaderboard"]]
    assert cv_means == f1_values
    assert body["extras"]["metric"] == "f1_macro"
    assert all(
        e["metrics"]["primary_metric"] == "f1_macro"
        for e in body["leaderboard"]
    )


@pytest.mark.asyncio
async def test_train_imbalanced_dataset_flags_extras(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-04: 90/10 dataset → extras.class_balance.imbalanced=True."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "imb.csv",
                _make_imbalanced_csv().encode("utf-8"),
                "text/csv",
            )
        },
    )
    dataset_id = upload.json()["id"]
    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "target",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    balance = body["extras"]["class_balance"]
    assert balance["imbalanced"] is True
    assert balance["counts"]["low"] == 90
    assert balance["counts"]["high"] == 10
    assert balance["ratio"] == 9.0


@pytest.mark.asyncio
async def test_artifact_reloads_and_predicts(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Acceptance criterion: saved artifact reloads via joblib + predicts."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
    )
    body = response.json()
    artifact = Path(body["artifact_path"])
    loaded = joblib.load(artifact)
    # Tuple shape only for logistic_regression (scaler, model).
    if isinstance(loaded, tuple):
        scaler, model = loaded
        sample = scaler.transform([[5.1, 3.5, 1.4, 0.2]])
        preds = model.predict(sample)
    else:
        preds = loaded.predict([[5.1, 3.5, 1.4, 0.2]])
    assert len(preds) == 1


# ----------------------------- Q5-ML-05 tuning -------------------------------

# 200-row binary classification with 4 informative numeric features.
# Deterministic via numpy seed=42 so the metric-comparison test is stable.
def _make_tunable_csv() -> str:
    import numpy as np

    rng = np.random.default_rng(42)
    n = 200
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    x3 = rng.normal(0, 1, n)
    x4 = rng.normal(0, 1, n)
    # Linear combination + sigmoid noise → binary label.
    score = 1.5 * x1 - 0.8 * x2 + 0.6 * x3 - 0.4 * x4 + rng.normal(0, 0.5, n)
    y = (score > 0).astype(int)
    rows = ["x1,x2,x3,x4,target"]
    for i in range(n):
        rows.append(
            f"{x1[i]:.4f},{x2[i]:.4f},{x3[i]:.4f},{x4[i]:.4f},{y[i]}"
        )
    return "\n".join(rows) + "\n"


@pytest.mark.asyncio
async def test_train_with_tune_flag_persists_best_params(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-05: tune=True surfaces best_params on leaderboard rows."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]
    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
            "tune": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    # Tuning ran — at least one estimator picked a non-default sample
    # (otherwise the safety-floor "{}" candidate won everything and
    # `best_params` is omitted). Iris-60 has enough variance for ≥1
    # estimator to land on a tuned sample.
    tuned = [
        e for e in body["leaderboard"]
        if e["metrics"].get("best_params")
    ]
    assert tuned, body["leaderboard"]

    # Whenever best_params is recorded it must be a non-empty dict
    # whose keys come from the estimator's declared distributions.
    tree_keys = {"n_estimators", "max_depth", "min_samples_split",
                 "max_features", "learning_rate", "num_leaves",
                 "min_child_samples", "C", "penalty", "solver"}
    for e in tuned:
        bp = e["metrics"]["best_params"]
        assert isinstance(bp, dict) and bp, e
        assert tree_keys & set(bp.keys()), e
        assert e["train_time_sec"] > 0

    leaderboard_rows = await auth_client.get(
        f"/api/v1/ml/leaderboard/{dataset_id}"
    )
    assert leaderboard_rows.status_code == 200
    rows = leaderboard_rows.json()
    assert any(r["hyperparams"] for r in rows)


@pytest.mark.asyncio
async def test_train_default_tune_false_omits_best_params(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-05: default path is unchanged — no best_params, no
    persisted hyperparams."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("iris.csv", CLASSIFICATION_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]
    response = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_id,
            "target_column": "species",
            "task_type": "classification",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for entry in body["leaderboard"]:
        assert "best_params" not in entry["metrics"], entry["metrics"]

    leaderboard_rows = await auth_client.get(
        f"/api/v1/ml/leaderboard/{dataset_id}"
    )
    assert leaderboard_rows.status_code == 200
    rows = leaderboard_rows.json()
    assert all(r["hyperparams"] is None for r in rows)


@pytest.mark.asyncio
async def test_tune_true_matches_or_beats_baseline_on_majority_of_estimators(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-ML-05 acceptance criterion: tune=True yields cv_mean >= baseline
    for at least 2 of 3 classification estimators on a 200-row fixture."""
    csv = _make_tunable_csv()

    upload_a = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("tune_a.csv", csv.encode("utf-8"), "text/csv")},
    )
    dataset_a = upload_a.json()["id"]
    baseline = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_a,
            "target_column": "target",
            "task_type": "classification",
        },
    )
    assert baseline.status_code == 200, baseline.text
    base_scores = {
        e["name"]: e["metrics"]["cv_mean"]
        for e in baseline.json()["leaderboard"]
    }

    # Re-upload to a fresh dataset id so the train run is independent.
    upload_b = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("tune_b.csv", csv.encode("utf-8"), "text/csv")},
    )
    dataset_b = upload_b.json()["id"]
    tuned = await auth_client.post(
        "/api/v1/ml/train",
        json={
            "dataset_id": dataset_b,
            "target_column": "target",
            "task_type": "classification",
            "tune": True,
        },
    )
    assert tuned.status_code == 200, tuned.text
    tuned_scores = {
        e["name"]: e["metrics"]["cv_mean"]
        for e in tuned.json()["leaderboard"]
    }

    # Compare on the 3 classification estimators that exist in the registry.
    common = set(base_scores) & set(tuned_scores)
    assert len(common) >= 3
    matched = [
        name for name in common
        # 1e-6 tolerance: ties pass without flake.
        if tuned_scores[name] >= base_scores[name] - 1e-6
    ]
    assert len(matched) >= 2, {
        "baseline": base_scores,
        "tuned": tuned_scores,
    }
