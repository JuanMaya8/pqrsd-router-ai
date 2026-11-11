"""Persistence: the current model (joblib) and the feedback log (JSON Lines, append-only).

Security note: joblib uses pickle. Only load files written by this service from a directory
that untrusted parties cannot write to.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import joblib

from .model import TextModel


class ModelStore:
    FILE = "current.joblib"

    def __init__(self, directory: str | Path | None = None) -> None:
        self._dir = Path(directory) if directory else None
        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> tuple[TextModel, dict] | None:
        if not self._dir or not (self._dir / self.FILE).exists():
            return None
        try:
            payload = joblib.load(self._dir / self.FILE)
            return payload["model"], payload.get("meta", {})
        except Exception:  # corrupted file: ignore and retrain, never crash on boot
            return None

    def save(self, model: TextModel, meta: dict) -> None:
        if not self._dir:
            return
        tmp = self._dir / (self.FILE + ".tmp")
        joblib.dump({"model": model, "meta": meta}, tmp)
        tmp.replace(self._dir / self.FILE)  # atomic swap


class FeedbackStore:
    HEADS = ("type", "dependency", "urgency", "subtype")

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else None
        self._items: list[dict] = []
        self._lock = threading.Lock()
        self._trained_mark = 0
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if self._path.exists():
                for line in self._path.read_text(encoding="utf-8").splitlines():
                    try:
                        self._items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # a half-written line must not break the boot

    def add(self, item: dict) -> int:
        row = {**item, "at": time.time()}
        with self._lock:
            self._items.append(row)
            if self._path:
                with self._path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            return len(self._items)

    def all(self) -> list[dict]:
        with self._lock:
            return list(self._items)

    def stats(self) -> dict:
        items = self.all()
        by_head = {h: sum(1 for i in items if i.get(h)) for h in self.HEADS}
        return {"total": len(items), "by_head": by_head, "since_last_training": max(0, len(items) - self._trained_mark)}

    def mark_trained(self) -> None:
        with self._lock:
            self._trained_mark = len(self._items)

    def __len__(self) -> int:
        return len(self._items)


class PgFeedbackStore(FeedbackStore):
    """Feedback log in PostgreSQL (table ``ai_feedback``), for hosts whose disk is wiped on every deploy (Render, Fly…).

    Same interface and in-memory cache as :class:`FeedbackStore`; every ``add`` is written to the database first.
    Like its parent it defines ``__len__``: an empty store is *falsy*, so never write ``store or X()``.
    ``psycopg`` is imported here only, so the dependency is needed just when DATABASE_URL is used.
    Every operation opens its own short connection: serverless databases (Neon) suspend when idle and drop open
    connections, so a long-lived one would fail on the first correction after a quiet period. Feedback is rare,
    so the extra connect (~50 ms, ~1 s if the database was asleep) does not matter.
    """

    TABLE = "ai_feedback"

    def __init__(self, dsn: str) -> None:
        import psycopg  # noqa: PLC0415 — optional dependency

        super().__init__(None)
        self._conn = psycopg.connect(dsn, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {self.TABLE} ("
                " id BIGSERIAL PRIMARY KEY, data JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            cur.execute(f"SELECT data FROM {self.TABLE} ORDER BY id")
            for (data,) in cur.fetchall():
                self._items.append(data if isinstance(data, dict) else json.loads(data))

    def add(self, item: dict) -> int:
        row = {**item, "at": time.time()}
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute(f"INSERT INTO {self.TABLE} (data) VALUES (%s::jsonb)", (json.dumps(row, ensure_ascii=False),))
            self._items.append(row)
            return len(self._items)

    def close(self) -> None:
        self._conn.close()
