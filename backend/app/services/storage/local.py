from __future__ import annotations

import os
from pathlib import Path

from app.core.config import settings
from app.services.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("..", "").lstrip("/")
        return self.base_dir / safe_key

    def put(self, key: str, data: bytes, content_type: str) -> str:
        safe_key = key.replace("..", "").lstrip("/")
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{safe_key}"

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def presigned_url(self, key: str, expires_seconds: int = 3600) -> str | None:
        return None
