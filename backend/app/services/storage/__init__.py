"""File storage abstraction.

Two backends behind a single ABC:

- `local` — `LocalStorage` writes under `Settings.local_storage_dir`.
  Default for dev + tests; no external service.
- `supabase` — `SupabaseStorage` keeps a local-disk mirror AND
  write-throughs to a Supabase Storage bucket. Used in prod (Render).

Pick a backend via `Settings.storage_backend`. The dispatcher in
`get_storage()` is import-free at module import time so importing
`app.services.storage` doesn't pull `supabase-py` into RAM until the
backend is actually selected.
"""

from app.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage


def get_storage() -> StorageBackend:
    """FastAPI dependency. Resolves the storage backend on every call so
    tests / monkeypatches that swap `settings.storage_backend` keep
    working without an import-time freeze."""
    backend = settings.storage_backend.lower()
    if backend == "local":
        return LocalStorage()
    if backend == "supabase":
        # Lazy import — keeps `supabase-py` off the import path for
        # dev environments running with the local backend.
        from app.services.storage.supabase import SupabaseStorage

        return SupabaseStorage()
    raise RuntimeError(
        f"Unknown storage backend: {backend!r}. " f"Set STORAGE_BACKEND to 'local' or 'supabase'."
    )


__all__ = ["StorageBackend", "LocalStorage", "get_storage"]
