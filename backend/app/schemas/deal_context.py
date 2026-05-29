from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class IncomeRecord(BaseModel):
    gross_income: Optional[float] = None
    pay_frequency: Optional[str] = None
    employer: Optional[str] = None
    source_document_id: Optional[int] = None


class AssetRecord(BaseModel):
    account_type: Optional[str] = None
    average_balance: Optional[float] = None
    recent_large_deposits: list[dict[str, Any]] = Field(default_factory=list)
    source_document_id: Optional[int] = None


class ApplicantMetadata(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    employer: Optional[str] = None
    source_document_id: Optional[int] = None


class DealContextRead(BaseModel):
    deal_id: int
    extracted_income: dict[str, Any] = {}
    extracted_assets: dict[str, Any] = {}
    extracted_liabilities: dict[str, Any] = {}
    computed_metrics: dict[str, Any] = {}
    status_flags: dict[str, Any] = {}

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: int
    deal_id: int
    storage_uri: str
    original_filename: str
    mime_type: str
    predicted_type: str
    classification_confidence: float
    extraction_status: str
    uploaded_at: str

    model_config = {"from_attributes": True}


class DocumentExtractionRead(BaseModel):
    id: int
    document_id: int
    raw_ocr: dict[str, Any] = {}
    normalized: dict[str, Any] = {}
    confidence: dict[str, Any] = {}
    human_corrections: dict[str, Any] = {}
    status: str

    model_config = {"from_attributes": True}


class ExtractionPatch(BaseModel):
    human_corrections: dict[str, Any]
