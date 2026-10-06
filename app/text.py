"""Text normalisation shared by rules, entities and the ML model."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def normalize(text: str) -> str:
    """lower-case, no accents, single spaces. Used for matching only (never shown to users)."""
    return _WS.sub(" ", strip_accents(text).lower()).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text))


def fold(text: str) -> str:
    """Length-preserving fold (lower-case, accents removed) so offsets in the folded text match the original."""
    out: list[str] = []
    for ch in text:
        base = "".join(c for c in unicodedata.normalize("NFD", ch) if unicodedata.category(c) != "Mn")
        folded = base.lower()
        out.append(folded if len(folded) == 1 else ch.lower()[:1] or ch)
    return "".join(out)
