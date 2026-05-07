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
