"""PgFeedbackStore against a real PostgreSQL. Skipped unless TEST_DATABASE_URL is set, e.g.
TEST_DATABASE_URL=postgresql://postgres:pg@localhost:55432/pqrsd python -m pytest -q tests/test_pg_store.py
Each run works in its own schema, dropped at the end."""

import os
import time
import unittest

DSN = os.environ.get("TEST_DATABASE_URL")


@unittest.skipUnless(DSN, "TEST_DATABASE_URL not set")
class PgFeedbackStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        cls.schema = f"ai_test_{os.getpid()}_{int(time.time())}"
        with psycopg.connect(DSN, autocommit=True) as c:
            c.execute(f"CREATE SCHEMA {cls.schema}")
        cls.dsn = f"{DSN}{'&' if '?' in DSN else '?'}options=-csearch_path%3D{cls.schema}"

    @classmethod
    def tearDownClass(cls):
        import psycopg

        with psycopg.connect(DSN, autocommit=True) as c:
            c.execute(f"DROP SCHEMA {cls.schema} CASCADE")

    def test_feedback_survives_a_restart_and_feeds_retraining(self):
        from app.schemas import FeedbackRequest, RetrainRequest
        from app.service import RouterService
        from app.store import PgFeedbackStore

        store = PgFeedbackStore(self.dsn)
        self.assertEqual(len(store), 0)
        self.assertFalse(store)  # empty store is falsy: callers must use `is not None`
        svc = RouterService(feedback=store, bootstrap_samples=600)
        svc.add_feedback(FeedbackRequest(text="hay una fuga de gas en el edificio y nadie viene", dependency="servicios_publicos", urgency="critical"))
        svc.add_feedback(FeedbackRequest(text="solicito copia del contrato de obra", type="peticion"))
        store.close()

        again = PgFeedbackStore(self.dsn)
        self.assertEqual(len(again), 2)
        self.assertEqual(again.all()[0]["dependency"], "servicios_publicos")
        svc2 = RouterService(feedback=again, bootstrap_samples=600)
        info = svc2.retrain(RetrainRequest(synthetic_samples=600))
        self.assertEqual(info.feedback_samples, 2)
        self.assertEqual(svc2.feedback_stats().since_last_training, 0)
        again.close()


if __name__ == "__main__":
    unittest.main()
