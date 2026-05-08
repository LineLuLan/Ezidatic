"""Storage backend ABC.

Concrete implementations live next to this file (one per backend); the
registry in `app/services/storage/__init__.py` picks one based on
`Settings.storage_backend`.

Every concrete backend MUST return `Path` from path-returning methods so
the existing call sites (datasets upload, preprocessing run, AutoML
artifact save) keep working without a wider refactor. Remote backends
(`SupabaseStorage`) achieve this by maintaining a local-disk mirror
under `Settings.local_storage_dir` — uploads write through to the
remote, downloads fetch on cache miss.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID


class StorageBackend(ABC):
    """Common surface every concrete storage backend exposes."""

    @abstractmethod
    def path_for(self, dataset_id: UUID, suffix: str) -> Path:
        """Resolve the canonical local Path used to read/write the raw upload."""

    @abstractmethod
    def write_bytes(self, dataset_id: UUID, suffix: str, data: bytes) -> Path:
        """Persist `data` for `dataset_id` and return the local Path callers should use."""

    @abstractmethod
    def read_bytes(self, path: Path) -> bytes:
        """Return the raw bytes at `path`, fetching from remote if needed."""

    @abstractmethod
    def path_for_preprocessed(self, dataset_id: UUID) -> Path:
        """Path used by the preprocessing pipeline to save its CSV output."""

    @abstractmethod
    def models_dir(self) -> Path:
        """Directory that holds AutoML joblib artifacts."""

    @abstractmethod
    def path_for_model(self, dataset_id: UUID, model_name: str) -> Path:
        """Resolve {models_dir}/{dataset_id}_{model_name}.joblib."""

    def upload_local(self, path: Path) -> None:  # noqa: B027 — default no-op
        """Push an already-written local file to the remote backing store.

        No-op for `LocalStorage` (the local path *is* the source of
        truth). `SupabaseStorage` overrides this to upload via the
        bucket SDK after `polars.write_csv` / `joblib.dump` paths so
        outputs survive Render redeploys.
        """
        return
