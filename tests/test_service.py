import json
import tempfile
import unittest
from pathlib import Path

from app.errors import ServiceError
from app.schemas import BatchItem, BatchRequest, ClassifyRequest, EntitiesRequest, FeedbackRequest, RetrainRequest
from app.service import RouterService
from app.store import FeedbackStore, ModelStore
from app.taxonomy import Taxonomy
from tests.helpers import shared_service


class ServiceTests(unittest.TestCase):
    def test_classify_and_batch(self):
        svc = shared_service()
        one = svc.classify(ClassifyRequest(text="Solicito copia del acta de la reunión del concejo del mes pasado."))
        self.assertEqual(one.type.id, "peticion")
        batch = svc.classify_batch(BatchRequest(items=[BatchItem(id="a", text="El hueco de la calle 5 con carrera 7 es enorme."), BatchItem(id="b", text="x")]))
        self.assertEqual([r.id for r in batch.results], ["a", "b"])
        self.assertEqual(batch.total, 2)
        self.assertGreaterEqual(batch.needs_review, 1)  # «x» is too short

    def test_entities(self):
        out = shared_service().entities(EntitiesRequest(text="Llamen al 3001234567, vivo en Cali."))
        self.assertIn("[TELÉFONO]", out.redacted_text)

    def test_feedback_validation(self):
        svc = RouterService(feedback=FeedbackStore(None), bootstrap_samples=300)
        with self.assertRaises(ServiceError):
            svc.add_feedback(FeedbackRequest(text="hola"))
        with self.assertRaises(ServiceError) as ctx:
            svc.add_feedback(FeedbackRequest(text="hola", dependency="inexistente"))
        self.assertEqual(ctx.exception.status, 422)
        ack = svc.add_feedback(FeedbackRequest(text="hola mundo", type="queja"))
        self.assertEqual(ack.total_feedback, 1)
        self.assertEqual(svc.feedback_stats().by_head["type"], 1)

    def test_feedback_persists_and_retrain_learns(self):
        with tempfile.TemporaryDirectory() as d:
            fb_path = Path(d) / "fb.jsonl"
            models = ModelStore(Path(d) / "models")
            svc = RouterService(feedback=FeedbackStore(fb_path), models=models, bootstrap_samples=600)
            before = svc.model_info().model_version
            for _ in range(10):
                svc.add_feedback(FeedbackRequest(text="El zumbido del gallinero de la finca vecina nos desvela cada madrugada", type="reclamo", dependency="ambiente", urgency="low"))
            self.assertEqual(svc.feedback_stats().since_last_training, 10)
            info = svc.retrain(RetrainRequest(synthetic_samples=600, feedback_weight=10.0))
            self.assertEqual(info.feedback_samples, 10)
            self.assertNotEqual(info.model_version, before)
            self.assertEqual(svc.feedback_stats().since_last_training, 0)
            self.assertEqual(len(fb_path.read_text().splitlines()), 10)
            # a fresh process loads the persisted model and feedback
            svc2 = RouterService(feedback=FeedbackStore(fb_path), models=ModelStore(Path(d) / "models"), bootstrap_samples=600)
            self.assertEqual(svc2.model_info().model_version, info.model_version)
            self.assertEqual(svc2.feedback_stats().total, 10)

    def test_corrupt_feedback_line_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fb.jsonl"
            p.write_text(json.dumps({"text": "ok", "type": "queja"}) + "\n{not json\n", encoding="utf-8")
            self.assertEqual(len(FeedbackStore(p)), 1)

    def test_retrain_without_data_fails_cleanly(self):
        svc = RouterService(feedback=FeedbackStore(None), bootstrap_samples=300)
        with self.assertRaises(ServiceError) as ctx:
            svc.retrain(RetrainRequest(synthetic_samples=0))
        self.assertEqual(ctx.exception.code, "NOT_ENOUGH_DATA")

    def test_custom_taxonomy(self):
        tax = Taxonomy.from_dict({"dependencies": [
            {"id": "general", "name": "Oficina General", "description": "", "keywords": ["ventanilla"]},
            {"id": "agua", "name": "Acueducto", "description": "", "keywords": ["agua", "acueducto", "medidor"]},
        ], "fallback_dependency": "general"})
        svc = RouterService(taxonomy=tax, feedback=FeedbackStore(None), bootstrap_samples=600)
        r = svc.classify(ClassifyRequest(text="Mi medidor de agua marca un consumo exagerado, pido revisión."))
        self.assertIn(r.dependency.id, {"general", "agua"})
        self.assertEqual(r.dependency.id, "agua")
        self.assertEqual({d["id"] for d in svc.taxonomy_out().dependencies}, {"general", "agua"})

    def test_model_info_is_honest_about_synthetic_data(self):
        info = shared_service().model_info()
        self.assertIn("SINTÉTICO", info.note)
        self.assertGreater(info.synthetic_samples, 0)


if __name__ == "__main__":
    unittest.main()
