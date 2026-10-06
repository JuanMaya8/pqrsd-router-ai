"""Shared, lazily-trained fixtures (training takes seconds, so build once per test run)."""

from __future__ import annotations

from functools import lru_cache

from app.service import RouterService
from app.store import FeedbackStore


@lru_cache(maxsize=1)
def shared_service() -> RouterService:
    return RouterService(feedback=FeedbackStore(None), bootstrap_samples=4000)
