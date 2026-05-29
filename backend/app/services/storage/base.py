from __future__ import annotations

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Persist bytes and return storage URI."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Load bytes by storage key."""

    @abstractmethod
    def presigned_url(self, key: str, expires_seconds: int = 3600) -> str | None:
        """Return a URL for direct download when supported."""
