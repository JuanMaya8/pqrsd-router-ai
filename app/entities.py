"""Rule-based entity extraction for Colombian PQRSD texts: dates, amounts, places, procedures, people and identifiers.

Offsets (`start`/`end`) always refer to the ORIGINAL text. Identifiers and people are flagged `pii: true`.
Relative dates ("ayer", "hace 3 meses") are resolved against `reference_date`.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import asdict, dataclass
from datetime import date, timedelta

from .text import fold

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_MONTH_RE = "|".join(MONTHS)

DEPARTMENTS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba",
    "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío",
    "Risaralda", "San Andrés", "Santander", "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada",
]
CITIES = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué", "Pasto", "Manizales",
    "Neiva", "Villavicencio", "Armenia", "Valledupar", "Montería", "Sincelejo", "Popayán", "Tunja", "Florencia", "Riohacha", "Yopal", "Quibdó",
    "Mocoa", "Soacha", "Bello", "Itagüí", "Envigado", "Palmira", "Buenaventura", "Tuluá", "Soledad", "Floridablanca", "Girardot", "Zipaquirá",
    "Chía", "Facatativá", "Sogamoso", "Duitama", "Barrancabermeja", "Rionegro", "Apartadó", "Maicao", "Ipiales", "Tumaco",
]

PROCEDURES = [
    "certificado de libertad y tradicion", "certificado de tradicion", "licencia de construccion", "licencia de conduccion", "licencia ambiental",
    "licencia de funcionamiento", "impuesto predial", "impuesto de industria y comercio", "impuesto vehicular", "valorizacion", "pico y placa", "comparendo",
    "fotomulta", "tarjeta de propiedad", "traspaso de vehiculo", "matricula vehicular", "afiliacion al sisben", "sisben", "subsidio de vivienda",
    "subsidio", "cita medica", "autorizacion de medicamentos", "historia clinica", "certificado de residencia", "paz y salvo", "poda de arboles",
    "alumbrado publico", "recoleccion de basuras", "cupo escolar", "matricula escolar", "pension", "registro civil", "uso del suelo", "estratificacion",
    "certificado de estratificacion", "permiso de ocupacion del espacio publico", "devolucion de dinero", "cobro coactivo", "acuerdo de pago",
    "certificado de bomberos", "permiso de espectaculos publicos", "inscripcion de victimas", "colombia mayor", "familias en accion", "carne de salud",
    "certificado de discapacidad", "sustitucion de pension", "reconexion del servicio", "alumbrado", "restaurante escolar", "alimentacion escolar",
]

_FOLDED_PLACE_RE: list[tuple[str, re.Pattern[str]]] = []
_FOLDED_PROC_RE: list[tuple[str, re.Pattern[str]]] = []

PII_TYPES = {"person", "document_id", "phone", "email", "address"}
PRIORITY = ["email", "phone", "document_id", "radicado", "plate", "address", "amount", "date", "person", "procedure", "place"]
LABELS_ES = {
    "date": "Fecha", "amount": "Monto", "place": "Lugar", "procedure": "Trámite", "person": "Persona", "document_id": "Documento de identidad",
    "phone": "Teléfono", "email": "Correo", "radicado": "Radicado previo", "plate": "Placa", "address": "Dirección",
}


@dataclass
class Entity:
    type: str
    label: str
    text: str
    start: int
    end: int
    value: str | None = None
    pii: bool = False
    approx: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _ent(kind: str, text: str, start: int, end: int, value: str | None = None, approx: bool = False) -> Entity:
    return Entity(kind, LABELS_ES[kind], text, start, end, value, kind in PII_TYPES, approx)


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _add_months(d: date, months: int) -> date:
    idx = d.year * 12 + (d.month - 1) - months
    y, m = divmod(idx, 12)
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


# ------------------------------------------------------------------ extractors

def _dates(text: str, folded: str, ref: date) -> list[Entity]:
    out: list[Entity] = []
    for m in re.finditer(rf"\b(\d{{1,2}})\s+de\s+({_MONTH_RE})(?:\s+(?:de|del)\s+(\d{{4}}))?", folded):
        day, month = int(m.group(1)), MONTHS[m.group(2)]
        if m.group(3):
            d = _safe_date(int(m.group(3)), month, day)
        else:
            d = _safe_date(ref.year, month, day)
            if d and d > ref:
                d = _safe_date(ref.year - 1, month, day)
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), d.isoformat() if d else None, approx=not m.group(3)))
    for m in re.finditer(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})\b", folded):
        y = int(m.group(3))
        y = y + 2000 if y < 100 else y
        d = _safe_date(y, int(m.group(2)), int(m.group(1)))  # Colombian order: day/month/year
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), d.isoformat() if d else None))
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", folded):
        d = _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), d.isoformat() if d else None))
    rel = {"hoy": 0, "ayer": 1, "anteayer": 2, "antier": 2, "antes de ayer": 2}
    for m in re.finditer(r"\b(antes de ayer|anteayer|antier|ayer|hoy)\b", folded):
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), (ref - timedelta(days=rel[m.group(1)])).isoformat(), approx=True))
    words = {"un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
    for m in re.finditer(r"\bhace\s+(\d{1,3}|" + "|".join(words) + r")\s+(dias?|semanas?|mes(?:es)?|anos?|años?)\b", folded):
        n = int(m.group(1)) if m.group(1).isdigit() else words[m.group(1)]
        unit = m.group(2)
        if unit.startswith("dia"):
            d = ref - timedelta(days=n)
        elif unit.startswith("semana"):
            d = ref - timedelta(weeks=n)
        elif unit.startswith("mes"):
            d = _add_months(ref, n)
        else:
            d = _add_months(ref, 12 * n)
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), d.isoformat(), approx=True))
    for m in re.finditer(r"\b(?:la semana pasada|el mes pasado|el ano pasado)\b", folded):
        kind = m.group(0)
        d = ref - timedelta(weeks=1) if "semana" in kind else _add_months(ref, 1) if "mes" in kind else _add_months(ref, 12)
        out.append(_ent("date", text[m.start():m.end()], m.start(), m.end(), d.isoformat(), approx=True))
    return out


def _to_number(raw: str) -> float | None:
    s = raw.strip()
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", s):
        return float(s.replace(",", ""))
    if re.fullmatch(r"\d+(?:,\d+)?", s):
        return float(s.replace(",", "."))
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return float(s)
    return None


def _amounts(text: str, folded: str) -> list[Entity]:
    out: list[Entity] = []
    for m in re.finditer(r"\$\s?(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)", text):
        v = _to_number(m.group(1))
        out.append(_ent("amount", m.group(0), m.start(), m.end(), None if v is None else f"{v:.0f}"))
    for m in re.finditer(r"\b(\d+(?:[.,]\d+)?)\s*(millones|millon|mil)\s*(?:de\s+)?pesos\b", folded):
        base = _to_number(m.group(1))
        mult = 1_000_000 if m.group(2).startswith("mill") else 1_000
        out.append(_ent("amount", text[m.start():m.end()], m.start(), m.end(), None if base is None else f"{base * mult:.0f}"))
    for m in re.finditer(r"\b(\d{1,3}(?:\.\d{3})+)\s*pesos\b", folded):
        v = _to_number(m.group(1))
        out.append(_ent("amount", text[m.start():m.end()], m.start(), m.end(), None if v is None else f"{v:.0f}"))
    return out


def _identifiers(text: str, folded: str) -> list[Entity]:
    out: list[Entity] = []
    for m in re.finditer(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text):
        out.append(_ent("email", m.group(0), m.start(), m.end(), m.group(0).lower()))
    for m in re.finditer(r"(?<!\d)(?:\+?57[\s-]?)?(3\d{2})[\s-]?(\d{3})[\s-]?(\d{4})(?!\d)", text):
        out.append(_ent("phone", m.group(0), m.start(), m.end(), "".join(m.groups())))
    for m in re.finditer(r"\b(?:c\.?\s?c\.?|cedula(?:\s+de\s+ciudadania)?|identificacion|nit|c\.?\s?e\.?|t\.?\s?i\.?)\s*(?:(?:es|son|de)\s+)?(?:no\.?|numero|n°|#|:)?\s*(\d{1,3}(?:[.\s]\d{3}){1,3}|\d{6,12})\b", folded):
        digits = re.sub(r"\D", "", m.group(1))
        out.append(_ent("document_id", text[m.start():m.end()], m.start(), m.end(), digits))
    for m in re.finditer(r"\bradicado\s*(?:no\.?|numero|n°|#)?\s*[:#]?\s*([a-z0-9][a-z0-9\-/]{4,24})", folded):
        out.append(_ent("radicado", text[m.start():m.end()], m.start(), m.end(), text[m.start(1):m.end(1)].upper()))
    for m in re.finditer(r"\b([A-Z]{3})[\s-]?(\d{2}[A-Z0-9])\b", text):
        out.append(_ent("plate", m.group(0), m.start(), m.end(), m.group(1) + m.group(2)))
    return out


_ADDRESS = re.compile(
    r"\b(?:calle|carrera|cra\.?|kr\.?|avenida|av\.?|diagonal|transversal|tv\.?|autopista|circular)\s*\d+\s*[a-z]?(?:\s*(?:bis|sur|norte|este|oeste))?"
    r"(?:\s*(?:#|no\.?|n°|numero)\s*\d+\s*[a-z]?\s*[-–]\s*\d+|\s+con\s+(?:calle|carrera|cra\.?|avenida|av\.?|diagonal|transversal)\s*\d+\s*[a-z]?)", re.I,
)


def _places(text: str, folded: str) -> list[Entity]:
    out: list[Entity] = []
    for m in _ADDRESS.finditer(folded):
        out.append(_ent("address", text[m.start():m.end()], m.start(), m.end(), None))
    cap = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+"
    for m in re.finditer(rf"\b((?i:barrio|vereda|localidad|comuna|corregimiento|sector|urbanizacion|urbanización|conjunto residencial|conjunto|municipio))\s+(?:de\s+|del\s+|la\s+|el\s+|los\s+)?((?:{cap}|\d+)(?:\s+(?:de\s+(?:la\s+)?|del\s+)?{cap}){{0,2}})", text):
        out.append(_ent("place", m.group(0), m.start(), m.end(), m.group(2)))
    if not _FOLDED_PLACE_RE:
        for name in DEPARTMENTS + CITIES:
            _FOLDED_PLACE_RE.append((name, re.compile(rf"(?<![a-z0-9]){re.escape(fold(name))}(?![a-z0-9])")))
    for name, pat in _FOLDED_PLACE_RE:
        for m in pat.finditer(folded):
            if text[m.start()].isupper():  # «Meta» the department vs «meta» the word
                out.append(_ent("place", text[m.start():m.end()], m.start(), m.end(), name))
    return out


def _procedures(text: str, folded: str) -> list[Entity]:
    if not _FOLDED_PROC_RE:
        for name in PROCEDURES:
            _FOLDED_PROC_RE.append((name, re.compile(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])")))
    out: list[Entity] = []
    for name, pat in _FOLDED_PROC_RE:
        for m in pat.finditer(folded):
            out.append(_ent("procedure", text[m.start():m.end()], m.start(), m.end(), name))
    return out


_NAME = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+(?:la\s+|los\s+)?|del\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3}"
_NAME_2 = r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+(?:la\s+|los\s+)?|del\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}"


def _people(text: str) -> list[Entity]:
    out: list[Entity] = []
    title = r"(?i:señor|señora|sr\.?|sra\.?|doctor|doctora|dr\.?|dra\.?|ingeniero|ingeniera|ing\.?|funcionario|funcionaria|abogado|abogada|licenciado|licenciada|secretario|secretaria|alcalde|alcaldesa|rector|rectora|profesor|profesora|agente|inspector|inspectora)"
    for m in re.finditer(rf"\b{title}\s+({_NAME})", text):
        out.append(_ent("person", m.group(1), m.start(1), m.end(1), m.group(1)))
    for m in re.finditer(rf"\b(?i:me llamo|mi nombre es|mi nombre:|nombre:)\s+({_NAME})", text):
        out.append(_ent("person", m.group(1), m.start(1), m.end(1), m.group(1)))
    # «Soy Ana Pérez»: at least two capitalised words, so «soy Madre» or «soy Vecino» are not taken as names
    for m in re.finditer(rf"\b(?i:soy|habla)\s+({_NAME_2})", text):
        out.append(_ent("person", m.group(1), m.start(1), m.end(1), m.group(1)))
    # sign-offs: «Atentamente, Ana Pérez»
    for m in re.finditer(rf"\b(?i:atentamente|cordialmente|cordial saludo|firma)\s*[,:]?\s*({_NAME})", text):
        out.append(_ent("person", m.group(1), m.start(1), m.end(1), m.group(1)))
    return out


# ------------------------------------------------------------------ public API

def extract_entities(text: str, reference_date: date | None = None) -> list[Entity]:
    ref = reference_date or date.today()
    folded = fold(text)
    found = [*_identifiers(text, folded), *_places(text, folded), *_amounts(text, folded), *_dates(text, folded, ref), *_people(text), *_procedures(text, folded)]
    rank = {k: i for i, k in enumerate(PRIORITY)}
    found.sort(key=lambda e: (rank[e.type], e.start))
    kept: list[Entity] = []
    for e in found:  # greedy by priority, no overlaps
        if all(e.end <= k.start or e.start >= k.end for k in kept):
            kept.append(e)
    kept.sort(key=lambda e: (e.start, e.end))
    return kept


_TOKEN = {"person": "[PERSONA]", "document_id": "[DOCUMENTO]", "phone": "[TELÉFONO]", "email": "[CORREO]", "address": "[DIRECCIÓN]"}


def redact(text: str, entities: list[Entity]) -> str:
    """Replaces personal data with tokens (useful before storing training examples or publishing statistics)."""
    out: list[str] = []
    pos = 0
    for e in sorted((e for e in entities if e.pii), key=lambda e: e.start):
        if e.start < pos:
            continue
        out.append(text[pos:e.start])
        out.append(_TOKEN[e.type])
        pos = e.end
    out.append(text[pos:])
    return "".join(out)
