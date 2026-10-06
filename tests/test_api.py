"""HTTP-level tests. Require fastapi + httpx (see requirements-dev.txt); skipped otherwise."""

import importlib.util
import os
import unittest

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None and importlib.util.find_spec("httpx") is not None


@unittest.skipUnless(HAS_FASTAPI, "fastapi/httpx not installed")
class ApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app.main import create_app
        from tests.helpers import shared_service

        self.client = TestClient(create_app(shared_service()))

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ready"])

    def test_classify(self):
        r = self.client.post("/v1/classify", json={"text": "Solicito copia del contrato 345 de 2024.", "redact": True})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["type"]["id"], "peticion")
        self.assertIn("redacted_text", body)

    def test_validation_errors_are_422(self):
        self.assertEqual(self.client.post("/v1/classify", json={"text": ""}).status_code, 422)
        self.assertEqual(self.client.post("/v1/classify", json={}).status_code, 422)
        self.assertEqual(self.client.post("/v1/classify/batch", json={"items": []}).status_code, 422)

    def test_feedback_and_taxonomy(self):
        self.assertEqual(self.client.get("/v1/taxonomy").json()["fallback_dependency"], "atencion_ciudadano")
        r = self.client.post("/v1/feedback", json={"text": "demora en la cita", "type": "reclamo"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/v1/feedback", json={"text": "demora en la cita"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.get("/v1/feedback/stats").status_code, 200)

    def test_api_key(self):
        from fastapi.testclient import TestClient

        from app.main import create_app
        from tests.helpers import shared_service

        os.environ["AI_API_KEY"] = "secret"
        try:
            client = TestClient(create_app(shared_service()))
        finally:
            del os.environ["AI_API_KEY"]
        self.assertEqual(client.post("/v1/classify", json={"text": "hola"}).status_code, 401)
        self.assertEqual(client.post("/v1/classify", headers={"X-API-Key": "secret"}, json={"text": "hola buenas tardes"}).status_code, 200)
        self.assertEqual(client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
