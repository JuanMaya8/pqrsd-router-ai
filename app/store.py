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
