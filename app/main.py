"""FastAPI wiring. All logic lives in `service.py` / `classifier.py`.

Run:  uvicorn app.main:app --reload --port 8000
Env:  see .env.example  (MODELS_DIR, FEEDBACK_FILE, DATABASE_URL, TAXONOMY_FILE, AI_API_KEY, CORS_ORIGINS, BOOTSTRAP_SAMPLES)
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .errors import ServiceError
from .schemas import (
    BatchRequest,
    BatchResponse,
    ClassifyRequest,
    Classification,
    EntitiesRequest,
    EntitiesResponse,
    ErrorResponse,
    FeedbackAck,
    FeedbackRequest,
    FeedbackStats,
    HealthResponse,
    ModelInfo,
    RetrainRequest,
    TaxonomyOut,
)
from .service import RouterService
from .store import FeedbackStore, ModelStore
from .taxonomy import Taxonomy


def build_service() -> RouterService:
    return RouterService(
        taxonomy=Taxonomy.load(os.environ.get("TAXONOMY_FILE") or None),
        models=ModelStore(os.environ.get("MODELS_DIR") or None),
        feedback=FeedbackStore(os.environ.get("FEEDBACK_FILE") or None),
        bootstrap_samples=int(os.environ.get("BOOTSTRAP_SAMPLES", "6000")),
    )


def create_app(service: RouterService | None = None) -> FastAPI:
    svc = service if service is not None else build_service()
    api_key = os.environ.get("AI_API_KEY") or None

    async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        if api_key and x_api_key != api_key:
            raise ServiceError("UNAUTHORIZED", "API key inválida o ausente.", 401)

    app = FastAPI(
        title="pqrsd-router-ai",
        version=__version__,
        description="Clasificación de PQRSD (tipo, dependencia, urgencia) y extracción de entidades para entidades públicas.",
    )
    origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(ServiceError)
    async def _service_error(_: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.to_dict())

    guard = [Depends(require_api_key)]
    errors = {401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return svc.health()

    @app.post("/v1/classify", response_model=Classification, tags=["classify"], dependencies=guard, responses=errors)
    def classify(req: ClassifyRequest) -> Classification:
        return svc.classify(req)

    @app.post("/v1/classify/batch", response_model=BatchResponse, tags=["classify"], dependencies=guard, responses=errors)
    def classify_batch(req: BatchRequest) -> BatchResponse:
        return svc.classify_batch(req)

    @app.post("/v1/entities", response_model=EntitiesResponse, tags=["classify"], dependencies=guard, responses=errors)
    def entities(req: EntitiesRequest) -> EntitiesResponse:
        return svc.entities(req)

    @app.get("/v1/taxonomy", response_model=TaxonomyOut, tags=["taxonomy"], dependencies=guard)
    def taxonomy() -> TaxonomyOut:
        return svc.taxonomy_out()

    @app.post("/v1/feedback", response_model=FeedbackAck, status_code=201, tags=["learning"], dependencies=guard, responses=errors)
    def feedback(req: FeedbackRequest) -> FeedbackAck:
        return svc.add_feedback(req)

    @app.get("/v1/feedback/stats", response_model=FeedbackStats, tags=["learning"], dependencies=guard)
    def feedback_stats() -> FeedbackStats:
        return svc.feedback_stats()

    @app.get("/v1/model", response_model=ModelInfo, tags=["learning"], dependencies=guard)
    def model_info() -> ModelInfo:
        return svc.model_info()

    @app.post("/v1/retrain", response_model=ModelInfo, tags=["learning"], dependencies=guard, responses=errors)
    def retrain(req: RetrainRequest) -> ModelInfo:
        return svc.retrain(req)

    return app


app = create_app()
