from __future__ import annotations

import logging
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DocumentParserMode = Literal["llamaindex", "textract"]
ObservabilityProvider = Literal["langsmith", "aws", "none"]


class Settings(BaseSettings):
    """
    Centralized environment configuration.

    Note: this project is MVP-focused; keep defaults safe for local development only.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg://loanofficer:loanofficer_password@localhost:5432/loanofficer_mvp"

    # Auth
    JWT_SECRET: str = "dev-change-me"
    JWT_ALGORITHM: str = "HS256"
    STAFF_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24  # 24h
    BORROWER_TOKEN_EXPIRE_SECONDS: int = 60 * 60  # 1h

    # LLM / Agents
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    TEXTRACT_REGION: str = "us-east-1"

    # Document parsing: "llamaindex" (default) or "textract" (explicit AWS opt-in)
    DOCUMENT_PARSER: str = "llamaindex"

    # Deprecated — mapped in model_validator
    OCR_BACKEND: str = ""
    INCOME_DOC_PARSER: str = ""

    # LlamaCloud (Parse + Extract)
    LLAMA_CLOUD_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("LLAMA_CLOUD_API_KEY", "LlamaIndex_API_KEY"),
    )
    LLAMA_PARSE_TIER: str = "cost_effective"
    LLAMA_EXTRACT_TIER: str = "cost_effective"
    LLAMA_POLL_INTERVAL_SEC: float = 2.0
    LLAMA_JOB_TIMEOUT_SEC: int = 120

    # Observability
    OBSERVABILITY_PROVIDER: str = "none"
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "loan-officer-copilot"
    OTEL_SERVICE_NAME: str = "loan-officer-copilot"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""

    # Storage
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    S3_BUCKET: str = "loan-officer-copilot-mvp"
    LOCAL_STORAGE_DIR: str = "./local_storage"

    @model_validator(mode="after")
    def _apply_legacy_parser_env(self) -> Settings:
        if self.OCR_BACKEND.strip():
            mapped = self.OCR_BACKEND.lower().strip()
            if mapped == "textract":
                logger.warning(
                    "OCR_BACKEND is deprecated; use DOCUMENT_PARSER=textract instead."
                )
                object.__setattr__(self, "DOCUMENT_PARSER", "textract")
            elif mapped in ("auto", "local"):
                logger.warning(
                    "OCR_BACKEND is deprecated; use DOCUMENT_PARSER=llamaindex instead."
                )
        if self.INCOME_DOC_PARSER.strip().lower() == "legacy":
            logger.warning(
                "INCOME_DOC_PARSER=legacy is deprecated; use DOCUMENT_PARSER=textract instead."
            )
            object.__setattr__(self, "DOCUMENT_PARSER", "textract")
        return self

    def effective_document_parser(self) -> DocumentParserMode:
        mode = self.DOCUMENT_PARSER.lower().strip()
        if mode == "textract":
            return "textract"
        return "llamaindex"

    def effective_observability_provider(self) -> ObservabilityProvider:
        value = self.OBSERVABILITY_PROVIDER.lower().strip()
        if value in ("langsmith", "aws", "none"):
            return value  # type: ignore[return-value]
        return "none"

    def require_llama_cloud_key(self) -> None:
        if not self.LLAMA_CLOUD_API_KEY.strip():
            raise ValueError(
                "LLAMA_CLOUD_API_KEY is required when DOCUMENT_PARSER=llamaindex. "
                "Set the key or use DOCUMENT_PARSER=textract."
            )


settings = Settings()
