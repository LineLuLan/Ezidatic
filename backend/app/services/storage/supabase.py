"""Supabase Storage backend.

Used in production (`STORAGE_BACKEND=supabase`). Maintains a local-disk
mirror under `Settings.local_storage_dir` so the existing call sites
that do `polars.read_csv(path)` / `joblib.dump(model, path)` keep
working without changes — the local mirror is the hot read-cache,
Supabase is the durable backing store.

Lifecycle:

- `write_bytes(...)` writes to local FS, then uploads to the bucket
  with the same relative key. Future reads on the same machine hit
  the local mirror first; cold reads (after Render redeploy or on
  another machine) fall through to Supabase download.
- `read_bytes(path)` checks local FS, downloads on miss, returns bytes.
- `path_for_preprocessed(...)` and `path_for_model(...)` return the
  local Path; subsequent file-write operations (polars `write_csv`,
  joblib `dump`) hit local FS only, so we explicitly upload them via
  the helpers below in `app/api/v1/preprocessing.py` +
  `app/api/v1/ml.py` after the file is written.

This is deliberate — keeping the storage interface Path-shaped means
no caller has to learn a new `read_to_temp(...)` pattern. The price is
that callers writing files directly to a path must call
`storage.upload_local(path)` afterwards (helper provided here, no-op
on `LocalStorage` so call sites stay backend-agnostic).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from supabase import Client, create_client

from app.config import settings
from app.services.storage.base import StorageBackend


def _bucket_key_for_path(local_root: Path, path: Path) -> str:
    """Translate an absolute local path under `local_root` into a Supabase
    storage key (forward-slashes, relative to the bucket root)."""
    rel = path.resolve().relative_to(local_root.resolve())
    return rel.as_posix()


class SupabaseStorage(StorageBackend):
    """Local-disk mirror with write-through to Supabase Storage."""

    def __init__(
        self,
        url: str | None = None,
        service_role_key: str | None = None,
        bucket: str | None = None,
        local_root: str | Path | None = None,
    ) -> None:
        url = url or settings.supabase_url
        service_role_key = service_role_key or settings.supabase_service_role_key
        bucket = bucket or settings.supabase_bucket

        if not url or not service_role_key or not bucket:
            raise RuntimeError(
                "SupabaseStorage requires SUPABASE_URL, "
                "SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_BUCKET to be set."
            )

        self.bucket = bucket
        self.root = Path(local_root or settings.local_storage_dir)
        self._client: Client = create_client(url, service_role_key)

    # --- path helpers (mirror LocalStorage so callers stay backend-agnostic) ---

    def path_for(self, dataset_id: UUID, suffix: str) -> Path:
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{dataset_id}{suffix.lower()}"

    def path_for_preprocessed(self, dataset_id: UUID) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{dataset_id}_pp.csv"

    def models_dir(self) -> Path:
        target = self.root / "models"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def path_for_model(self, dataset_id: UUID, model_name: str) -> Path:
        return self.models_dir() / f"{dataset_id}_{model_name}.joblib"

    # --- I/O ---

    def write_bytes(self, dataset_id: UUID, suffix: str, data: bytes) -> Path:
        target = self.path_for(dataset_id, suffix)
        target.write_bytes(data)
        self._upload(target, data)
        return target

    def read_bytes(self, path: Path) -> bytes:
        if path.exists():
            return path.read_bytes()
        key = _bucket_key_for_path(self.root, path)
        data = self._client.storage.from_(self.bucket).download(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data

    def upload_local(self, path: Path) -> None:
        """Upload an already-written local file to Supabase. No-op on misses.

        Used by call sites that bypass `write_bytes` (e.g. polars
        `write_csv` for preprocessing output, joblib `dump` for ML
        artifacts) — they write to the path returned by
        `path_for_preprocessed` / `path_for_model`, then call this to
        push to remote.
        """
        if not path.exists():
            return
        self._upload(path, path.read_bytes())

    # --- internals ---

    def _upload(self, path: Path, data: bytes) -> None:
        key = _bucket_key_for_path(self.root, path)
        # supabase-py 2.x: upload(...) raises if the object exists
        # unless we pass file_options.upsert. Use upsert so re-uploads
        # (e.g. retraining the same model) replace cleanly.
        self._client.storage.from_(self.bucket).upload(
            path=key,
            file=data,
            file_options={"upsert": "true"},
        )
