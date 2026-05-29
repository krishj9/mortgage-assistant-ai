from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # LLM / Agents (wired later; still required for config parsing in early phases)
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    TEXTRACT_REGION: str = "us-east-1"
    # OCR: "auto" (Textract with local fallback), "textract", or "local" (no AWS; for .txt fixtures)
    OCR_BACKEND: str = "auto"

    # Observability
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "loan-officer-copilot"

    # Storage
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    S3_BUCKET: str = "loan-officer-copilot-mvp"
    LOCAL_STORAGE_DIR: str = "./local_storage"


settings = Settings()

