from __future__ import annotations

from app.services.storage.local import LocalStorage


def test_local_storage_put_get(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    uri = storage.put("deals/1/sample.txt", b"hello", "text/plain")
    assert uri.startswith("local://")
    assert storage.get("deals/1/sample.txt") == b"hello"
