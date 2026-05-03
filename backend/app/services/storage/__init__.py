"""File storage abstraction.

Local-filesystem only for now. When we add Supabase Storage in Polish,
introduce a `StorageBackend` ABC + registry like the other subsystems.
"""

from app.services.storage.local import LocalStorage, get_storage

__all__ = ["LocalStorage", "get_storage"]
