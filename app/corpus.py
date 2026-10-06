"""SYNTHETIC cold-start corpus generator (deterministic for a given seed).

Why it exists: a classifier needs examples on day one and the project must not depend on invented citizen data
at run time. These texts are built from hand-written phrases (corpus_data.py) and are ONLY a starting point:
officials' corrections (`/v1/feedback`) and real PQRSD exported by the entity replace them (`/v1/retrain`).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import corpus_data as D

URG = {"l": "low", "m": "medium", "h": "high", "c": "critical"}
URG_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
TYPE_WEIGHTS = {"peticion": 0.30, "queja": 0.16, "reclamo": 0.26, "sugerencia": 0.12, "denuncia": 0.16}


@dataclass(frozen=True)
class Sample:
    text: str
    type: str
    dependency: str
    urgency: str
    subtype: str | None


def _parse(entry: str) -> tuple[str, str, str]:
    parts = entry.split("|")
    return parts[0], URG[parts[1]] if len(parts) > 1 else "medium", {"g": "general", "i": "information", "c": "consultation"}[parts[2]] if len(parts) > 2 else "general"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _context(rng: random.Random) -> str:
    bits: list[str] = []
    r = rng.random()
    if r < 0.30:
        bits.append(f"Ocurre en el barrio {rng.choice(D.BARRIOS)}.")
    elif r < 0.45:
        bits.append(f"Vivo en {rng.choice(D.CITIES)}.")
    if rng.random() < 0.20:
        bits.append(f"Desde el {rng.randint(1, 28)} de {rng.choice(['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre'])} de 2025.")
    return " ".join(bits)


def _escalate(rng: random.Random, base: str, ptype: str) -> tuple[str, str]:
    """Maybe adds an urgency cue sentence; returns (cue_sentence, final_urgency)."""
    p = rng.random()
    if ptype == "sugerencia":
        return (rng.choice(D.URGENCY_CUES["l"]) if p < 0.35 else ""), ("low" if p < 0.85 else base if base == "low" else "low")
    if p < 0.12 and base != "critical":
        cue = rng.choice(D.URGENCY_CUES["h"])
        return cue, "high" if URG_RANK[base] < 2 else base
    if p < 0.16:
        return rng.choice(D.URGENCY_CUES["c"]), "critical"
    if p < 0.24 and base == "medium":
        return rng.choice(D.URGENCY_CUES["l"]), "low"
    return "", base


def generate_one(rng: random.Random) -> Sample:
    ptype = rng.choices(list(TYPE_WEIGHTS), weights=list(TYPE_WEIGHTS.values()))[0]
    deps = list(D.SITUATIONS)
    if ptype == "denuncia":
        dep = "control_interno" if rng.random() < 0.38 else rng.choice(deps)
    elif ptype == "queja":
        dep = "control_interno" if rng.random() < 0.15 else rng.choice(deps)
    else:
        dep = rng.choice(deps)
    block = D.SITUATIONS[dep]
    subtype: str | None = None

    if ptype == "peticion":
        x, hint, subtype = _parse(rng.choice(block["requests"]))
        body = rng.choice(D.PETITION_WRAPPERS).format(x=x)
    elif ptype == "reclamo":
        x, hint, _ = _parse(rng.choice(block["failures"]))
        w = rng.choice(D.RECLAMO_WRAPPERS)
        body = w.format(x=x, X=_cap(x))
    elif ptype == "sugerencia":
        x, hint, _ = _parse(rng.choice(block["suggestions"]))
        hint = "low"
        body = rng.choice(D.SUGGESTION_WRAPPERS).format(x=x)
    elif ptype == "denuncia":
        x, hint, _ = _parse(rng.choice(block["irregularities"]))
        hint = "medium" if hint == "medium" else hint
        body = rng.choice(D.DENUNCIA_WRAPPERS).format(x=x)
    else:  # queja
        conduct, h = rng.choice(D.QUEJA_CONDUCTS)
        hint = URG[h]
        body = rng.choice(D.QUEJA_WRAPPERS).format(s=rng.choice(D.QUEJA_SERVANTS), v=rng.choice(block["venues"]), c=conduct)

    cue, urgency = _escalate(rng, hint, ptype)
    parts = [rng.choice(D.OPENINGS), body, _context(rng), cue, rng.choice(D.CLOSINGS)]
    if rng.random() < 0.15:
        parts.append(f"Mi nombre es {rng.choice(D.NAMES)}.")
    text = " ".join(p for p in parts if p).strip()
    return Sample(text, ptype, dep, urgency, subtype)


def generate(n: int, seed: int = 7) -> list[Sample]:
    rng = random.Random(seed)
    seen: set[str] = set()
    out: list[Sample] = []
    guard = 0
    while len(out) < n and guard < n * 20:
        guard += 1
        s = generate_one(rng)
        if s.text in seen:
            continue
        seen.add(s.text)
        out.append(s)
    return out
