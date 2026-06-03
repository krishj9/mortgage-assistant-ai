from __future__ import annotations

import pytest

from app.core.config import Settings
from app.observability.provider import get_observability_provider


def test_observability_provider_default_none():
    settings = Settings.model_validate({"OBSERVABILITY_PROVIDER": "none"})
    assert settings.effective_observability_provider() == "none"


def test_get_observability_provider():
    assert get_observability_provider() in ("langsmith", "aws", "none")
