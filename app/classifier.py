"""Hybrid classifier: ML probabilities blended with explainable rules, plus entity extraction and Spanish reasons."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date

from .entities import Entity, extract_entities, redact
from .model import TextModel
from .rules import RuleResult, evaluate, to_probs, top_evidence
from .taxonomy import Taxonomy
from .text import word_count

RULE_MIX = {"type": 0.50, "dependency": 0.30, "urgency": 0.50, "subtype": 0.40}
URGENCY_VALUE = {"critical": 95.0, "high": 72.0, "medium": 42.0, "low": 15.0}
# the score never contradicts the chosen level: a «critical» case always outranks any «high» one
URGENCY_FLOOR = {"critical": 85.0, "high": 62.0, "medium": 30.0, "low": 0.0}
MIN_WORDS_OK = 6
CRITICAL_RULE_SCORE = 3.0  # at least one decisive phrase: escalate (a false alarm costs less than a missed emergency)
FALLBACK_BELOW = 0.30
# The model is trained on a templated cold-start corpus, so on real text it is over-confident.
# Tempering (p^(1/T), renormalised) lets the explainable rules weigh in; retrained-on-real-data models can use a lower T.
MODEL_TEMPERATURE = {"type": 3.0, "dependency": 1.0, "urgency": 5.0, "subtype": 2.0}


@dataclass
class Choice:
    id: str
    label: str
    confidence: float


def _normalise(p: dict[str, float]) -> dict[str, float]:
    total = sum(p.values())
    return {k: v / total for k, v in p.items()} if total > 0 else p


def _temper(p: dict[str, float] | None, temperature: float) -> dict[str, float] | None:
    if not p or temperature == 1.0:
        return p
    return _normalise({k: max(v, 1e-9) ** (1.0 / temperature) for k, v in p.items()})


def _mix(model_p: dict[str, float] | None, rule_scores: dict[str, float], mix: float, universe: list[str], prior_floor: float = 0.0) -> dict[str, float]:
    """Blends model probabilities with rule evidence. Rule weight grows with the amount of evidence (up to `mix`)."""
    base = {c: (model_p or {}).get(c, 0.0) for c in universe}
    if not model_p:
        base = {c: 1.0 / len(universe) for c in universe}
    total = sum(rule_scores.get(c, 0.0) for c in universe)
    if total <= prior_floor:
        return _normalise(base)
    strength = min(1.0, total / 6.0) * mix
    rules_p = {c: rule_scores.get(c, 0.0) / total for c in universe}
    return _normalise({c: (1 - strength) * base[c] + strength * rules_p[c] for c in universe})


class HybridClassifier:
    def __init__(self, taxonomy: Taxonomy, model: TextModel) -> None:
        self.taxonomy = taxonomy
        self.model = model

    # ------------------------------------------------------------------ public
    def classify(self, text: str, reference_date: date | None = None, top_k: int = 3, with_redaction: bool = False) -> dict:
        return self.classify_many([text], reference_date, top_k, with_redaction)[0]

    def classify_many(self, texts: list[str], reference_date: date | None = None, top_k: int = 3, with_redaction: bool = False) -> list[dict]:
        t0 = time.perf_counter()
        probs = self.model.predict_proba(texts)
        results = []
        for i, text in enumerate(texts):
            results.append(self._one(text, {h: p[i] for h, p in probs.items()}, reference_date, top_k, with_redaction))
        per = (time.perf_counter() - t0) * 1000 / max(1, len(texts))
        for r in results:
            r["latency_ms"] = round(per, 2)
        return results

    # ------------------------------------------------------------------ internals
    def _one(self, text: str, model_p: dict[str, dict[str, float]], ref: date | None, top_k: int, with_redaction: bool) -> dict:
        tax = self.taxonomy
        model_p = {h: _temper(p, MODEL_TEMPERATURE.get(h, 1.0)) or p for h, p in model_p.items()}
        rules = evaluate(text, tax)
        entities = extract_entities(text, ref)

        type_ids = [o.id for o in tax.types]
        p_type = _mix(model_p.get("type"), rules.type_scores, RULE_MIX["type"], type_ids)

        dep_ids = tax.dependency_ids()
        p_dep = _mix(model_p.get("dependency"), rules.dependency_scores, RULE_MIX["dependency"], dep_ids)
        # the generic office only wins by itself when nothing more specific is known
        top_dep = max(p_dep, key=p_dep.get)  # type: ignore[arg-type]

        urg_ids = [o.id for o in tax.urgency]
        urg_rules = dict(rules.urgency_scores)
        urg_rules["medium"] = 1.5  # "no signals" is a real option, so it must compete with the signalled levels
        p_urg = _mix(model_p.get("urgency"), urg_rules, RULE_MIX["urgency"], urg_ids)
        urg_id = max(p_urg, key=p_urg.get)  # type: ignore[arg-type]
        escalated = False
        if rules.urgency_scores.get("critical", 0.0) >= CRITICAL_RULE_SCORE and urg_id != "critical":
            urg_id, escalated = "critical", True

        type_id = max(p_type, key=p_type.get)  # type: ignore[arg-type]
        subtype = None
        if type_id == "peticion":
            sub_ids = [o.id for o in tax.subtypes]
            sub_rules = dict(rules.subtype_scores)
            sub_rules["general"] = 1.0
            p_sub = _mix(model_p.get("subtype"), sub_rules, RULE_MIX["subtype"], sub_ids)
            sid = max(p_sub, key=p_sub.get)  # type: ignore[arg-type]
            subtype = {"id": sid, "label": tax.label("subtype", sid), "confidence": round(p_sub[sid], 4),
                       "reasons": self._subtype_reasons(sid, rules)}

        dep_sorted = sorted(p_dep.items(), key=lambda kv: -kv[1])
        routed_fallback = p_dep[top_dep] < FALLBACK_BELOW and top_dep != tax.fallback_dependency
        dep_final = tax.fallback_dependency if routed_fallback else top_dep

        words = word_count(text)
        review: list[str] = []
        if p_type[type_id] < 0.42:
            review.append("La IA no está segura del tipo de solicitud.")
        if p_dep[top_dep] < 0.40:
            review.append("La IA no está segura de la dependencia competente.")
        if len(dep_sorted) > 1 and dep_sorted[0][1] - dep_sorted[1][1] < 0.08:
            review.append(f"Dos dependencias son casi igual de probables: {tax.label('dependency', dep_sorted[0][0])} y {tax.label('dependency', dep_sorted[1][0])}.")
        if words < MIN_WORDS_OK:
            review.append("El texto es muy corto para clasificarlo con confianza.")
        if escalated:
            review.append("Se escaló la urgencia por una señal de riesgo vital: confirme cuanto antes.")

        priority = sum(p_urg[u] * URGENCY_VALUE[u] for u in urg_ids)
        priority = max(priority, URGENCY_FLOOR[urg_id])
        if escalated:
            priority = max(priority, 90.0)

        def top(head: str, dist: dict[str, float]) -> list[dict]:
            return [{"id": k, "label": tax.label(head, k), "confidence": round(v, 4)} for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:top_k]]

        return {
            "type": {"id": type_id, "label": tax.label("type", type_id), "confidence": round(p_type[type_id], 4), "alternatives": top("type", p_type)[1:], "reasons": self._type_reasons(type_id, p_type[type_id], rules)},
            "dependency": {"id": dep_final, "label": tax.label("dependency", dep_final), "confidence": round(p_dep[dep_final] if not routed_fallback else p_dep[top_dep], 4),
                           "alternatives": [a for a in top("dependency", p_dep) if a["id"] != dep_final][: top_k - 1], "routed_to_fallback": routed_fallback,
                           "reasons": self._dependency_reasons(dep_final if not routed_fallback else top_dep, p_dep, rules, routed_fallback)},
            "urgency": {"id": urg_id, "label": tax.label("urgency", urg_id), "confidence": round(p_urg[urg_id], 4), "priority_score": round(priority, 1),
                        "alternatives": [a for a in top("urgency", p_urg) if a["id"] != urg_id][: top_k - 1], "reasons": self._urgency_reasons(urg_id, rules, escalated)},
            "subtype": subtype,
            "entities": [e.to_dict() for e in entities],
            "needs_review": bool(review),
            "review_reasons": review,
            "redacted_text": redact(text, entities) if with_redaction else None,
            "word_count": words,
            "model_version": self.version(),
        }

    def version(self) -> str:
        return f"hybrid-{int(self.model.trained_at)}" if self.model.trained_at else "hybrid-untrained"

    # ---------------------------------------------------------------- reasons (Spanish)
    @staticmethod
    def _quote(phrases: list[str]) -> str:
        return ", ".join(f"«{p}»" for p in phrases)

    def _type_reasons(self, type_id: str, prob: float, rules: RuleResult) -> list[str]:
        ev = top_evidence(rules, "type", type_id)
        out = []
        if ev:
            out.append(f"El texto contiene {self._quote(ev)}, expresiones propias de {self._article(type_id)}.")
        out.append(f"El modelo, entrenado con ejemplos de PQRSD, asigna {round(prob * 100)} % de probabilidad a «{self.taxonomy.label('type', type_id)}».")
        return out

    @staticmethod
    def _article(type_id: str) -> str:
        return {"peticion": "una petición", "queja": "una queja", "reclamo": "un reclamo", "sugerencia": "una sugerencia", "denuncia": "una denuncia"}.get(type_id, type_id)

    def _dependency_reasons(self, dep_id: str, p_dep: dict[str, float], rules: RuleResult, fallback: bool) -> list[str]:
        name = self.taxonomy.label("dependency", dep_id)
        ev = top_evidence(rules, "dependency", dep_id, 4)
        out = []
        if ev:
            out.append(f"Menciona {self._quote(ev)}, asuntos de {name}.")
        out.append(f"Probabilidad estimada para {name}: {round(p_dep[dep_id] * 100)} %.")
        if fallback:
            out.append(f"Como la confianza es baja, se sugiere enviarla a {self.taxonomy.label('dependency', self.taxonomy.fallback_dependency)} para que la redirija.")
        return out

    def _urgency_reasons(self, urg_id: str, rules: RuleResult, escalated: bool) -> list[str]:
        ev = top_evidence(rules, "urgency", urg_id, 4) if urg_id in rules.urgency_scores else []
        label = self.taxonomy.label("urgency", urg_id)
        if urg_id == "medium" and not any(v > 0 for v in rules.urgency_scores.values()):
            return ["No se encontraron señales de riesgo, vulnerabilidad ni plazos vencidos: urgencia ordinaria."]
        if ev:
            msg = f"Urgencia {label.lower()} porque el texto menciona {self._quote(ev)}."
            return [msg + (" Se escaló automáticamente por riesgo vital." if escalated else "")]
        return [f"El modelo estima urgencia {label.lower()} por el contenido general del texto."]

    def _subtype_reasons(self, sid: str, rules: RuleResult) -> list[str]:
        ev = top_evidence(rules, "subtype", sid)
        if sid == "information" and ev:
            return [f"Pide información o documentos ({self._quote(ev)}): la ley da 10 días hábiles."]
        if sid == "consultation" and ev:
            return [f"Es una consulta a la entidad ({self._quote(ev)}): la ley da 30 días hábiles."]
        return ["Petición general: 15 días hábiles."]
