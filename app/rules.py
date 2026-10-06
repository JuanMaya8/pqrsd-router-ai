"""Deterministic, explainable rules (lexicons). They give (a) evidence shown to the official in Spanish and
(b) a prior that is blended with the ML probabilities, so the system works from day one and for rare cases.

All patterns are matched against `normalize(text)` (lower-case, no accents) with word boundaries.
Weights: 1 = weak hint, 2 = clear, 3 = decisive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .taxonomy import Taxonomy
from .text import normalize

# (phrase, weight). Phrases are written without accents.
TYPE_RULES: dict[str, list[tuple[str, int]]] = {
    "peticion": [
        ("derecho de peticion", 3), ("articulo 23", 2), ("solicito", 2), ("solicitamos", 2), ("me permito solicitar", 3), ("requiero", 1),
        ("quisiera saber", 2), ("quisiera conocer", 2), ("como puedo", 1), ("cuales son los requisitos", 2), ("agradezco me informen", 2),
        ("necesito que me", 1), ("ruego", 1), ("copia de", 2), ("expedir", 2), ("expidan", 2), ("favor enviar", 1), ("quiero saber", 1),
        ("informacion sobre", 1), ("certificado", 1), ("certificacion", 1), ("cual es el procedimiento", 2), ("me pueden informar", 2),
            ("quisiera una copia", 2), ("me gustaria saber", 2), ("deseo saber", 2), ("pido que me certifiquen", 3), ("me expliquen", 2), ("me informan", 2), ("que me informen", 2), ("requisitos para", 2), ("horarios y", 1), ("solicito respetuosamente", 3), ("se me informe", 2), ("pido que me", 1),
    ],
    "queja": [
        ("presento queja", 3), ("queja contra", 3), ("mala atencion", 3), ("maltrato", 2), ("grosero", 3), ("grosera", 3), ("groseria", 3),
        ("me atendio mal", 3), ("atendieron mal", 3), ("falta de respeto", 3), ("irrespetuoso", 3), ("irrespetuosa", 3), ("trato indigno", 3),
        ("se nego a atenderme", 3), ("se nego a recibir", 2), ("no quiso atenderme", 3), ("no quisieron atenderme", 3), ("me humillo", 3),
        ("el funcionario", 1), ("la funcionaria", 1), ("el servidor", 1), ("actitud", 1), ("me grito", 3), ("me trato mal", 3), ("mal trato", 2),
        ("me hicieron esperar", 1), ("desatendio", 2), ("indolente", 2), ("prepotente", 2),
            ("trato mal", 3), ("pesima atencion", 3), ("atencion es pesima", 3), ("se rio", 2), ("celular", 1), ("no nos atienden", 2), ("me ignoraron", 2), ("mal atendido", 3), ("mal atendida", 3),
    ],
    "reclamo": [
        ("reclamo", 3), ("exijo", 2), ("no he recibido", 2), ("nunca llego", 2), ("no han resuelto", 2), ("sigue sin", 2), ("me cobraron", 2),
        ("cobro excesivo", 3), ("error en", 1), ("mal servicio", 3), ("servicio deficiente", 3), ("deficiente", 2), ("no funciona", 2),
        ("incumplimiento", 2), ("hace meses sin", 2), ("llevo", 1), ("no me han respondido", 2), ("pago doble", 3), ("cobro doble", 3),
        ("sin respuesta", 1), ("no han venido", 2), ("no han arreglado", 2), ("no han reparado", 2), ("me siguen cobrando", 3), ("inconformidad con el servicio", 3),
        ("no me han entregado", 2), ("no han reconectado", 2), ("exigimos", 2), ("falla en el servicio", 3), ("demora", 1), ("tardanza", 1),
            ("no llega", 2), ("no llego", 2), ("sigue apareciendo", 2), ("todavia me aparece", 3), ("error evidente", 3), ("llego por", 1), ("no es mio", 3), ("no es mia", 3), ("pido que lo anulen", 3), ("anulen", 2), ("lo anulen", 2), ("sin ambulancia", 2), ("sin servicio", 2), ("llevo semanas", 2), ("llevo meses", 2), ("semanas esperando", 2), ("meses esperando", 2), ("revision de mi factura", 2), ("solicito revision", 1), ("no hacen nada", 2), ("nadie viene", 2), ("nadie ha venido", 2), ("no nos dejan dormir", 2),
    ],
    "sugerencia": [
        ("sugiero", 3), ("sugerencia", 3), ("sugerimos", 3), ("propongo", 3), ("proponemos", 3), ("propuesta", 2), ("recomiendo", 3),
        ("seria bueno", 3), ("seria conveniente", 3), ("seria ideal", 3), ("podrian implementar", 3), ("deberian implementar", 3), ("podrian habilitar", 3),
        ("seria excelente", 3), ("valdria la pena", 3), ("mejoraria", 2), ("idea para", 2), ("para mejorar", 2), ("podrian considerar", 3), ("me gustaria que implementen", 3),
        ("seria util", 2), ("estaria bien que", 2),
            ("sugiero que", 3), ("seria bueno que", 3), ("mas canecas", 1), ("podrian poner", 3), ("deberian poner", 3), ("pongan mas", 2), ("instalen mas", 2), ("que se habilite", 3), ("propongo que", 3), ("considere", 1),
    ],
    "denuncia": [
        ("denuncio", 3), ("denuncia", 3), ("denunciar", 3), ("corrupcion", 3), ("soborno", 3), ("coima", 3), ("sobornos", 3), ("irregularidades", 2),
        ("presunto", 2), ("presuntamente", 3), ("contrato amanado", 3), ("peculado", 3), ("trafico de influencias", 3), ("amenaza", 1), ("amenazaron", 2),
        ("por debajo de la mesa", 3), ("pidio dinero", 3), ("piden dinero", 3), ("exige dinero", 3), ("cobran por", 1), ("fraude", 3), ("delito", 2),
        ("ilegal", 2), ("ilegalmente", 2), ("malversacion", 3), ("se robaron", 3), ("desvio de recursos", 3), ("favorecimiento", 3), ("nepotismo", 3),
        ("tramitador", 2), ("venden cupos", 3), ("venta de cupos", 3), ("abuso de autoridad", 3), ("acoso", 2), ("sin licencia", 1), ("contratos a dedo", 3),
            ("venta de drogas", 3), ("expendio de drogas", 3), ("microtrafico", 2), ("acosa", 3), ("acoso sexual", 3), ("abuso", 1), ("pidio mil", 3), ("me pidio dinero", 3), ("pidio 200", 3), ("para agilizar", 3), ("agilizar el tramite", 3), ("botando escombros", 2), ("contaminando", 1), ("sin concurso", 3), ("hermano sin", 2), ("contrato sin", 2), ("quiero denunciar", 3), ("denuncio que", 3), ("pidio plata", 3), ("me pidieron plata", 3), ("mordida", 3),
    ],
}

URGENCY_RULES: dict[str, list[tuple[str, int]]] = {
    "critical": [
        ("riesgo de muerte", 3), ("peligro de muerte", 3), ("riesgo para la vida", 3), ("riesgo vital", 3), ("emergencia", 2), ("cable de alta tension", 3),
        ("cable caido", 3), ("fuga de gas", 3), ("olor a gas", 3), ("derrumbe", 3), ("deslizamiento", 3), ("inundacion", 2), ("incendio", 3),
        ("se esta muriendo", 3), ("agonizando", 3), ("sin oxigeno", 3), ("desnutricion", 3), ("amenaza de muerte", 3), ("amenazas de muerte", 3),
        ("me van a matar", 3), ("abuso sexual", 3), ("abusando", 2), ("violencia intrafamiliar", 3), ("riesgo inminente", 3), ("colapso", 2),
        ("puede caerse", 2), ("a punto de caer", 3), ("poste a punto", 3), ("intento de suicidio", 3), ("suicidio", 3), ("electrocut*", 3), ("cuerpo", 1), ("herido", 2), ("heridos", 2),
        ("sin atencion medica", 2), ("no lo atienden", 2), ("vida de mi", 2), ("morir", 2), ("murio", 1), ("peligro inminente", 3), ("hueco enorme", 1),
            ("casi atropell*", 3), ("casi muere", 3), ("casi murio", 3), ("acosa*", 2), ("a punto de caerse", 3), ("a punto de caer", 3), ("puede caer", 2), ("cualquier momento", 1), ("huele muy fuerte", 2), ("asustad*", 1), ("sin ambulancia", 2), ("accidente*", 1), ("pueden ocurrir accidentes", 2), ("abusan*", 3), ("menores en riesgo", 3),
    ],
    "high": [
        ("urgente", 3), ("con urgencia", 3), ("urgencia", 1), ("tutela", 3), ("derecho fundamental", 3), ("derechos fundamentales", 3), ("adulto mayor", 2),
        ("tercera edad", 2), ("anciano", 2), ("anciana", 2), ("menor de edad", 2), ("menores", 1), ("ninos", 1), ("ninas", 1), ("mi hijo", 1), ("mi hija", 1),
        ("discapacidad", 2), ("embarazada", 2), ("enfermo", 2), ("enferma", 2), ("cancer", 3), ("tratamiento", 1), ("sin medicamento", 3), ("sin agua desde", 2), ("sin luz desde", 2),
        ("vencio el termino", 3), ("vencio el plazo", 3), ("vencido el termino", 3), ("termino vencido", 3), ("plazo vencido", 3), ("fuera de termino", 3), ("silencio administrativo", 3),
        ("desalojo", 3), ("embargo", 2), ("ultimo dia", 2), ("vence", 1), ("dias sin", 1), ("semanas sin", 2), ("meses sin", 2), ("hace meses", 2), ("desde hace anos", 2),
        ("no tengo para comer", 3), ("no tenemos agua", 2), ("sin servicio de agua", 2), ("persona en condicion", 2), ("oxigeno", 2), ("dialisis", 3), ("quimioterapia", 3), ("victima", 2),
        ("grave", 1), ("gravisimo", 2), ("necesito con urgencia", 3), ("por favor ayuda", 1), ("desesperad*", 2),
            ("bebe", 2), ("recien nacido", 3), ("semanas esperando", 2), ("meses esperando", 2), ("dos meses", 1), ("tres semanas", 1), ("llevo semanas", 2), ("llevo meses", 2), ("cardiologia", 1), ("especialista", 1), ("cita con", 1), ("venta de drogas", 2), ("miedo", 2), ("acoso", 2), ("muertos", 2), ("pueden ocurrir accidentes", 2), ("necesito un cupo", 2), ("clases ya empezaron", 3), ("paz y salvo urgente", 3), ("escritura", 1),
    ],
    "low": [
        ("sugiero", 2), ("sugerencia", 2), ("propongo", 2), ("cuando puedan", 3), ("sin afan", 3), ("no es urgente", 3), ("a futuro", 2), ("idea para", 2),
        ("seria bueno", 2), ("seria conveniente", 2), ("para mejorar", 1), ("valdria la pena", 2), ("cuando tengan tiempo", 3), ("con calma", 2), ("a mediano plazo", 2),
        ("tengo curiosidad", 2), ("solo quiero saber", 1), ("consulta general", 1),
            ("solicito respetuosamente", 2), ("quisiera saber", 2), ("quisiera una copia", 2), ("quisiera consultar", 2), ("me gustaria saber", 2), ("deseo saber", 2), ("cuales son los horarios", 2), ("cuales son los requisitos", 2), ("requisitos para", 1), ("como puedo pagar", 1), ("copia del contrato", 2), ("copia de los estudios", 2), ("felicitar*", 2), ("bancas", 1), ("mas canecas", 2), ("agradezco que me expliquen", 1),
    ],
}

SUBTYPE_RULES: dict[str, list[tuple[str, int]]] = {
    "information": [
        ("copia", 2), ("copias", 2), ("informacion", 1), ("me informen", 2), ("certificacion", 2), ("certificado", 2), ("documento", 1), ("documentos", 1),
        ("expediente", 2), ("historia clinica", 2), ("estado de mi tramite", 3), ("estado de mi proceso", 3), ("estado de mi solicitud", 3), ("acceso a la informacion", 3),
        ("ley 1712", 3), ("contrato numero", 1), ("acta", 1), ("soportes", 2), ("copia del", 2), ("me envien", 1), ("remitir copia", 3),
            ("copia del contrato", 3), ("copia de los estudios", 3), ("estudios tecnicos", 2),
    ],
    "consultation": [
        ("consulta", 3), ("concepto", 3), ("me pueden aclarar si", 3), ("es viable", 3), ("es legal", 3), ("interpretacion", 3), ("norma aplicable", 3),
        ("cual es el concepto", 3), ("puedo legalmente", 3), ("esta permitido", 2), ("es permitido", 2), ("que normas", 2), ("aclaren si", 2), ("conforme a la ley", 1),
    ],
}


@dataclass
class Evidence:
    phrase: str
    weight: int


@dataclass
class RuleResult:
    """Raw rule scores per head and the phrases that fired (for explanations)."""

    type_scores: dict[str, float] = field(default_factory=dict)
    urgency_scores: dict[str, float] = field(default_factory=dict)
    subtype_scores: dict[str, float] = field(default_factory=dict)
    dependency_scores: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, dict[str, list[Evidence]]] = field(default_factory=dict)  # head -> class -> evidence


_COMPILED: dict[str, re.Pattern[str]] = {}


def _pattern(phrase: str) -> re.Pattern[str]:
    """A trailing `*` means "prefix" (e.g. «electrocut*» matches electrocutado/electrocutaron)."""
    pat = _COMPILED.get(phrase)
    if pat is None:
        prefix = phrase.endswith("*")
        body = re.escape(phrase.rstrip("*"))
        pat = re.compile(rf"(?<![a-z0-9]){body}" + ("" if prefix else r"(?![a-z0-9])"))
        _COMPILED[phrase] = pat
    return pat


def _score(norm: str, rules: dict[str, list[tuple[str, int]]], head: str, evidence: dict[str, dict[str, list[Evidence]]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for cls, items in rules.items():
        total = 0.0
        for phrase, weight in items:
            if _pattern(phrase).search(norm):
                total += weight
                evidence.setdefault(head, {}).setdefault(cls, []).append(Evidence(phrase, weight))
        scores[cls] = total
    return scores


def evaluate(text: str, taxonomy: Taxonomy) -> RuleResult:
    norm = normalize(text)
    res = RuleResult()
    res.type_scores = _score(norm, TYPE_RULES, "type", res.evidence)
    res.urgency_scores = _score(norm, URGENCY_RULES, "urgency", res.evidence)
    res.subtype_scores = _score(norm, SUBTYPE_RULES, "subtype", res.evidence)
    dep_rules = {d.id: [(normalize(k), 2 if " " in k else 1) for k in d.keywords] for d in taxonomy.dependencies}
    res.dependency_scores = _score(norm, dep_rules, "dependency", res.evidence)
    return res


def to_probs(scores: dict[str, float], floor: float = 0.0) -> dict[str, float]:
    """Turns raw rule scores into a distribution (all zeros -> uniform)."""
    total = sum(scores.values())
    n = len(scores)
    if total <= floor:
        return {k: 1.0 / n for k in scores}
    return {k: v / total for k, v in scores.items()}


def top_evidence(res: RuleResult, head: str, cls: str, limit: int = 3) -> list[str]:
    items = sorted(res.evidence.get(head, {}).get(cls, []), key=lambda e: -e.weight)
    return [e.phrase for e in items[:limit]]
