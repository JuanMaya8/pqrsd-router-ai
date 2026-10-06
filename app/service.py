"""Application service. Framework-free: `main.py` only wires HTTP to these methods, so this is what unit tests cover."""

from __future__ import annotations

import threading
import time

from . import __version__
from .classifier import HybridClassifier
from .corpus import generate
from .entities import extract_entities, redact
from .errors import ServiceError
from .model import LabeledText, TextModel
from .schemas import (
    BatchRequest,
    BatchResponse,
    BatchResult,
    ClassifyRequest,
    Classification,
    EntitiesRequest,
    EntitiesResponse,
    FeedbackAck,
    FeedbackRequest,
    FeedbackStats,
    HealthResponse,
    ModelInfo,
    RetrainRequest,
    TaxonomyOut,
)
from .store import FeedbackStore, ModelStore
from .taxonomy import Taxonomy

COLD_START_NOTE = (
    "El modelo se entrenó con un corpus SINTÉTICO de arranque (plantillas) más la retroalimentación humana. "
    "Antes de producción reentrénelo con PQRSD reales etiquetadas por funcionarios (POST /v1/feedback + /v1/retrain)."
)


class RouterService:
    def __init__(self, taxonomy: Taxonomy | None = None, models: ModelStore | None = None, feedback: FeedbackStore | None = None, bootstrap_samples: int = 6000) -> None:
        self.taxonomy = taxonomy if taxonomy is not None else Taxonomy()
        self.models = models if models is not None else ModelStore()
        self.feedback = feedback if feedback is not None else FeedbackStore()
        self._lock = threading.Lock()  # only one retraining at a time
        self._classifier: HybridClassifier | None = None
        self._meta: dict = {}
        loaded = self.models.load()
        if loaded:
            model, self._meta = loaded
            self._classifier = HybridClassifier(self.taxonomy, model)
        else:
            self._train(RetrainRequest(synthetic_samples=bootstrap_samples, include_feedback=True))

    # ---------------------------------------------------------------- training
    def _dataset(self, req: RetrainRequest) -> list[LabeledText]:
        dep_ids = set(self.taxonomy.dependency_ids())
        items: list[LabeledText] = []
        if req.synthetic_samples > 0:
            for s in generate(req.synthetic_samples, seed=req.seed):
                # a custom taxonomy does not know the default dependencies: train that head only on feedback
                items.append(LabeledText(s.text, s.type, s.dependency if s.dependency in dep_ids else None, s.urgency, s.subtype))
        if req.include_feedback:
            for f in self.feedback.all():
                dep = f.get("dependency")
                items.append(LabeledText(f["text"], f.get("type"), dep if dep in dep_ids else None, f.get("urgency"), f.get("subtype"), weight=req.feedback_weight))
        return items

    def _train(self, req: RetrainRequest) -> TextModel:
        items = self._dataset(req)
        if len(items) < 30:
            raise ServiceError("NOT_ENOUGH_DATA", "Se necesitan al menos 30 ejemplos (sintéticos o corregidos) para entrenar.", 422)
        model = TextModel(seed=req.seed).fit(items)
        fb = sum(1 for i in items if i.weight > 1.0)
        meta = {"synthetic_samples": len(items) - fb, "feedback_samples": fb}
        self._classifier = HybridClassifier(self.taxonomy, model)
        self._meta = meta
        self.models.save(model, meta)
        self.feedback.mark_trained()
        return model

    def retrain(self, req: RetrainRequest) -> ModelInfo:
        if not self._lock.acquire(blocking=False):
            raise ServiceError("TRAINING_IN_PROGRESS", "Ya hay un reentrenamiento en curso.", 409)
        try:
            self._train(req)
        finally:
            self._lock.release()
        return self.model_info()

    # ---------------------------------------------------------------- use cases
    @property
    def classifier(self) -> HybridClassifier:
        if self._classifier is None:  # pragma: no cover - guarded by __init__
            raise ServiceError("MODEL_NOT_READY", "El modelo aún no está listo.", 503)
        return self._classifier

    def classify(self, req: ClassifyRequest) -> Classification:
        out = self.classifier.classify(req.text, req.reference_date, req.top_k, req.redact)
        return Classification.model_validate(out)

    def classify_batch(self, req: BatchRequest) -> BatchResponse:
        t0 = time.perf_counter()
        outs = self.classifier.classify_many([i.text for i in req.items], req.reference_date, req.top_k, req.redact)
        results = [BatchResult(id=item.id, classification=Classification.model_validate(o)) for item, o in zip(req.items, outs)]
        return BatchResponse(
            results=results,
            total=len(results),
            needs_review=sum(1 for r in results if r.classification.needs_review),
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

    def entities(self, req: EntitiesRequest) -> EntitiesResponse:
        ents = extract_entities(req.text, req.reference_date)
        return EntitiesResponse(entities=[e.to_dict() for e in ents], redacted_text=redact(req.text, ents))  # type: ignore[arg-type]

    def add_feedback(self, req: FeedbackRequest) -> FeedbackAck:
        if not any([req.type, req.dependency, req.urgency, req.subtype]):
            raise ServiceError("EMPTY_FEEDBACK", "Indique al menos una etiqueta corregida (tipo, dependencia, urgencia o subtipo).", 422)
        if req.dependency and req.dependency not in self.taxonomy.dependency_ids():
            raise ServiceError("UNKNOWN_DEPENDENCY", f"La dependencia «{req.dependency}» no existe en la taxonomía.", 422)
        total = self.feedback.add({k: v for k, v in req.model_dump().items() if v is not None})
        return FeedbackAck(stored=True, total_feedback=total)

    def feedback_stats(self) -> FeedbackStats:
        return FeedbackStats(**self.feedback.stats())

    def taxonomy_out(self) -> TaxonomyOut:
        return TaxonomyOut(**self.taxonomy.to_dict())

    def model_info(self) -> ModelInfo:
        m = self.classifier.model
        return ModelInfo(
            model_version=self.classifier.version(),
            trained_at=m.trained_at or None,
            trained_on=m.trained_on,
            metrics=m.metrics,
            heads=sorted(m.heads),
            synthetic_samples=int(self._meta.get("synthetic_samples", 0)),
            feedback_samples=int(self._meta.get("feedback_samples", 0)),
            note=COLD_START_NOTE,
        )

    def health(self) -> HealthResponse:
        return HealthResponse(status="ok", version=__version__, model_version=self.classifier.version(), ready=self._classifier is not None)
