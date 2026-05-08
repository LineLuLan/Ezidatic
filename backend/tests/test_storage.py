"""Storage backend dispatch + registry tests.

These never hit real Supabase — `SupabaseStorage.__init__` is mocked
out so the construction path is verifiable without network or
credentials.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.config import settings
from app.services.storage import LocalStorage, get_storage
from app.services.storage.base import StorageBackend


def test_get_storage_returns_local_by_default() -> None:
    backend = get_storage()
    assert isinstance(backend, LocalStorage)
    assert isinstance(backend, StorageBackend)


def test_get_storage_dispatches_to_supabase(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_service_role_key", "service-role-token")
    monkeypatch.setattr(settings, "supabase_bucket", "datasets")

    # Patch the symbol where it is *used* (post-import binding), not
    # where it is defined — `from supabase import create_client` binds
    # a local reference that wouldn't see a `supabase.create_client`
    # patch.
    with patch("app.services.storage.supabase.create_client") as create_client:
        create_client.return_value = object()  # we don't call into it
        from app.services.storage.supabase import SupabaseStorage

        backend = get_storage()
        assert isinstance(backend, SupabaseStorage)
        create_client.assert_called_once_with("https://example.supabase.co", "service-role-token")


def test_get_storage_raises_for_unknown_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "storage_backend", "s3")
    with pytest.raises(RuntimeError, match="Unknown storage backend"):
        get_storage()


def test_supabase_storage_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "supabase_url", None)
    monkeypatch.setattr(settings, "supabase_service_role_key", None)

    from app.services.storage.supabase import SupabaseStorage

    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        SupabaseStorage()


def test_local_storage_upload_local_is_noop(tmp_path) -> None:
    backend = LocalStorage(root=tmp_path)
    target = backend.write_bytes(uuid4(), "csv", b"col1\n1\n")
    # Calling upload_local should not raise and should leave the file
    # exactly as-is (no remote, no copy elsewhere).
    backend.upload_local(target)
    assert target.read_bytes() == b"col1\n1\n"


def test_local_storage_read_bytes_round_trips(tmp_path) -> None:
    backend = LocalStorage(root=tmp_path)
    dataset_id = uuid4()
    backend.write_bytes(dataset_id, "csv", b"a,b\n1,2\n")
    target = backend.path_for(dataset_id, "csv")
    assert backend.read_bytes(target) == b"a,b\n1,2\n"
