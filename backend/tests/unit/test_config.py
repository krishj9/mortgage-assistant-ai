from __future__ import annotations

from app.core.config import Settings


def test_settings_defaults_are_loaded():
    assert Settings().DATABASE_URL.startswith("postgresql")
    assert Settings().JWT_ALGORITHM == "HS256"


def test_effective_document_parser_llamaindex_default():
    settings = Settings.model_validate({"DOCUMENT_PARSER": "llamaindex"})
    assert settings.effective_document_parser() == "llamaindex"


def test_effective_document_parser_textract():
    settings = Settings.model_validate({"DOCUMENT_PARSER": "textract"})
    assert settings.effective_document_parser() == "textract"


def test_require_llama_cloud_key_raises():
    settings = Settings.model_validate({"LLAMA_CLOUD_API_KEY": ""})
    try:
        settings.require_llama_cloud_key()
        raised = False
    except ValueError:
        raised = True
    assert raised
