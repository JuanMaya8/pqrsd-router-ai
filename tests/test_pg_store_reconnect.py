"""PgFeedbackStore opens one short connection per operation (Neon drops idle connections). Uses a fake psycopg: no database."""

import json
import sys
import types
import unittest


class _Cursor:
    def __init__(self, db):
        self.db = db
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if sql.startswith("SELECT"):
            self._rows = [(r,) for r in self.db["rows"]]
        elif sql.startswith("INSERT"):
            self.db["rows"].append(json.loads(params[0]))

    def fetchall(self):
        return self._rows


class _Conn:
    def __init__(self, db):
        self.db = db
        db["opened"] += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.db["closed"] += 1
        return False

    def cursor(self):
        return _Cursor(self.db)


class PgStoreReconnectTests(unittest.TestCase):
    def setUp(self):
        self.db = {"rows": [{"text": "previa", "dependency": "salud"}], "opened": 0, "closed": 0, "kwargs": None}
        fake = types.ModuleType("psycopg")

        def connect(dsn, **kwargs):
            self.db["kwargs"] = kwargs
            return _Conn(self.db)

        fake.connect = connect
        self._saved = sys.modules.get("psycopg")
        sys.modules["psycopg"] = fake

    def tearDown(self):
        if self._saved is None:
            sys.modules.pop("psycopg", None)
        else:
            sys.modules["psycopg"] = self._saved

    def test_each_operation_uses_its_own_connection_and_closes_it(self):
        from app.store import PgFeedbackStore

        store = PgFeedbackStore("postgresql://u:p@ep-x.neon.tech/db?sslmode=require")
        self.assertEqual(len(store), 1)
        self.assertEqual((self.db["opened"], self.db["closed"]), (1, 1))
        store.add({"text": "nueva", "urgency": "high"})
        store.add({"text": "otra", "type": "queja"})
        self.assertEqual((self.db["opened"], self.db["closed"]), (3, 3))
        self.assertEqual(len(self.db["rows"]), 3)
        self.assertEqual(len(store), 3)
        self.assertTrue(self.db["kwargs"]["autocommit"])
        store.close()  # nothing left open


if __name__ == "__main__":
    unittest.main()
