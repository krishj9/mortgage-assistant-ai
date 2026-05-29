from __future__ import annotations

from app.core.config import settings


def test_settings_defaults_are_loaded():
    # Ensures pydantic-settings is wired.
    assert settings.DATABASE_URL.startswith("postgresql")
    assert isinstance(settings.JWT_SECRET, str)
    assert settings.JWT_ALGORITHM == "HS256"

