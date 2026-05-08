"""Local filesystem storage."""

from pathlib import Path
from uuid import UUID

from app.config import settings
from app.services.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """Save uploaded bytes under `Settings.local_storage_dir`."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or settings.local_storage_dir)

    def path_for(self, dataset_id: UUID, suffix: str) -> Path:
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{dataset_id}{suffix.lower()}"

    def write_bytes(self, dataset_id: UUID, suffix: str, data: bytes) -> Path:
        target = self.path_for(dataset_id, suffix)
        target.write_bytes(data)
        return target

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def path_for_preprocessed(self, dataset_id: UUID) -> Path:
        """Path used by preprocessing pipeline output. Single overwrite per dataset."""
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{dataset_id}_pp.csv"

    def models_dir(self) -> Path:
        """Directory under storage root for AutoML model artifacts."""
        target = self.root / "models"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def path_for_model(self, dataset_id: UUID, model_name: str) -> Path:
        """Resolve {root}/models/{dataset_id}_{model_name}.joblib."""
        return self.models_dir() / f"{dataset_id}_{model_name}.joblib"
