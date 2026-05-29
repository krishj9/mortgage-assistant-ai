from __future__ import annotations

from app.core.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage
from app.services.storage.s3 import S3Storage


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3Storage()
    return LocalStorage()
