"""Public HTTP contract (pydantic v2). Mirrors docs/CONTRACT.md."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_TEXT_CHARS = 20_000
MAX_BATCH = 200

TypeId = Literal["peticion", "queja", "reclamo", "sugerencia", "denuncia"]
UrgencyId = Literal["critical", "high", "medium", "low"]
SubtypeId = Literal["general", "information", "consultation"]


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    reference_date: date | None = Field(default=None, description="Fecha de radicación; resuelve «ayer», «hace 3 días»… Por defecto, hoy.")
    top_k: int = Field(default=3, ge=1, le=6)
    redact: bool = Field(default=False, description="Si es true devuelve también `redacted_text` sin datos personales.")

    @field_validator("text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El texto no puede estar vacío")
        return v


class BatchItem(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(min_length=1, max_length=MAX_BATCH)
    reference_date: date | None = None
    top_k: int = Field(default=3, ge=1, le=6)
    redact: bool = False


class Alternative(BaseModel):
    id: str
    label: str
    confidence: float


class Choice(BaseModel):
    id: str
    label: str
    confidence: float
    alternatives: list[Alternative] = []
    reasons: list[str] = []


class DependencyChoice(Choice):
    routed_to_fallback: bool = False


class UrgencyChoice(Choice):
    priority_score: float


class SubtypeChoice(BaseModel):
    id: str
    label: str
    confidence: float
    reasons: list[str] = []


class EntityOut(BaseModel):
    type: str
    label: str
    text: str
    start: int
    end: int
    value: str | None = None
    pii: bool = False
    approx: bool = False


class Classification(BaseModel):
    type: Choice
    dependency: DependencyChoice
    urgency: UrgencyChoice
    subtype: SubtypeChoice | None = None
    entities: list[EntityOut] = []
    needs_review: bool
    review_reasons: list[str] = []
    redacted_text: str | None = None
    word_count: int
    model_version: str
    latency_ms: float


class BatchResult(BaseModel):
    id: str | None = None
    classification: Classification


class BatchResponse(BaseModel):
    results: list[BatchResult]
    total: int
    needs_review: int
    latency_ms: float


class EntitiesRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    reference_date: date | None = None


class EntitiesResponse(BaseModel):
    entities: list[EntityOut]
    redacted_text: str


class FeedbackRequest(BaseModel):
    """A human correction. Send only the heads the official actually confirmed/changed."""

    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    type: TypeId | None = None
    dependency: str | None = Field(default=None, max_length=64)
    urgency: UrgencyId | None = None
    subtype: SubtypeId | None = None
    source_id: str | None = Field(default=None, max_length=64, description="Radicado u otra referencia, solo para auditoría.")


class FeedbackAck(BaseModel):
    stored: bool
    total_feedback: int


class FeedbackStats(BaseModel):
    total: int
    by_head: dict[str, int]
    since_last_training: int


class RetrainRequest(BaseModel):
    include_feedback: bool = True
    synthetic_samples: int = Field(default=6000, ge=0, le=50_000, description="Corpus sintético de arranque; 0 = solo retroalimentación real.")
    feedback_weight: float = Field(default=5.0, ge=1.0, le=50.0, description="Peso de cada corrección humana frente a un ejemplo sintético.")
    seed: int = 42


class ModelInfo(BaseModel):
    model_version: str
    trained_at: float | None
    trained_on: dict[str, int]
    metrics: dict[str, dict[str, float]]
    heads: list[str]
    synthetic_samples: int
    feedback_samples: int
    note: str


class TaxonomyOut(BaseModel):
    types: list[dict]
    urgency: list[dict]
    subtypes: list[dict]
    dependencies: list[dict]
    fallback_dependency: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    model_version: str
    ready: bool


class ErrorResponse(BaseModel):
    code: str
    message: str
