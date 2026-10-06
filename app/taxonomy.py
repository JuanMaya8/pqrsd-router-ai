"""Classification taxonomy: PQRSD types, urgency levels, petition sub-types and the entity's dependencies.

The built-in dependencies are a typical municipal/district entity. To adapt it to another entity set
`TAXONOMY_FILE` (JSON, same shape as `Taxonomy.to_dict()`): the rules use the keywords you provide, and
the ML head learns the new ids from staff feedback (`POST /v1/feedback` + `POST /v1/retrain`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

FALLBACK_DEPENDENCY = "atencion_ciudadano"


@dataclass(frozen=True)
class Option:
    id: str
    label: str
    description: str = ""


@dataclass(frozen=True)
class Dependency:
    id: str
    name: str
    description: str
    keywords: tuple[str, ...] = ()


TYPES: tuple[Option, ...] = (
    Option("peticion", "Petición", "Solicitud respetuosa de información, documentos, un trámite o una actuación de la entidad."),
    Option("queja", "Queja", "Inconformidad con la conducta o actuación de un servidor público."),
    Option("reclamo", "Reclamo", "Inconformidad por un servicio no prestado o prestado de forma deficiente; se exige solución."),
    Option("sugerencia", "Sugerencia", "Propuesta para mejorar un servicio, trámite o política de la entidad."),
    Option("denuncia", "Denuncia", "Pone en conocimiento hechos presuntamente irregulares, corruptos o delictivos."),
)

URGENCY: tuple[Option, ...] = (
    Option("critical", "Crítica", "Riesgo inminente para la vida, la integridad o la seguridad de personas."),
    Option("high", "Alta", "Derechos fundamentales, población vulnerable o plazos vencidos."),
    Option("medium", "Media", "Trámite o inconformidad ordinaria."),
    Option("low", "Baja", "Sugerencias o solicitudes sin afectación actual."),
)

SUBTYPES: tuple[Option, ...] = (
    Option("general", "Petición general", "Solicitud general (15 días hábiles)."),
    Option("information", "Solicitud de información o documentos", "Copias, certificaciones o acceso a información (10 días hábiles)."),
    Option("consultation", "Consulta", "Consulta a la autoridad sobre asuntos a su cargo (30 días hábiles)."),
)

DEFAULT_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("atencion_ciudadano", "Atención al Ciudadano", "Orientación general, radicación y asuntos sin dependencia clara.",
               ("atencion al ciudadano", "ventanilla", "radicacion", "turno", "horario de atencion", "pagina web", "pqrs", "no me responden", "oficina de atencion")),
    Dependency("salud", "Secretaría de Salud", "Servicios de salud, EPS/IPS, vacunación y salud pública.",
               ("eps", "ips", "hospital", "clinica", "medico", "medicamento", "cita medica", "vacuna", "urgencias", "salud", "ambulancia", "historia clinica", "regimen subsidiado", "tratamiento", "dengue", "puesto de salud")),
    Dependency("movilidad", "Secretaría de Movilidad y Tránsito", "Tránsito, transporte público, comparendos y licencias.",
               ("transito", "comparendo", "fotomulta", "foto multa", "semaforo", "pico y placa", "licencia de conduccion", "tarjeta de propiedad", "runt", "parqueadero", "oficina de transito", "transporte publico", "bus", "taxi", "agente de transito", "patios", "senalizacion", "vehiculo")),
    Dependency("hacienda", "Secretaría de Hacienda e Impuestos", "Impuestos, facturación, pagos y cobro coactivo.",
               ("impuesto", "predial", "industria y comercio", "valorizacion", "paz y salvo", "recaudo", "cobro coactivo", "declaracion de renta", "tarifa", "devolucion de pago", "pago doble", "factura de impuesto", "embargo de cuentas", "sancion tributaria")),
    Dependency("infraestructura", "Obras Públicas e Infraestructura", "Vías, andenes, alumbrado, puentes y obras.",
               ("hueco", "huecos", "via", "pavimento", "anden", "puente", "obra publica", "alcantarilla", "alumbrado publico", "reparcheo", "contratista", "escombros", "mantenimiento vial", "calle danada", "bache", "poste")),
    Dependency("educacion", "Secretaría de Educación", "Colegios públicos, cupos, docentes y alimentación escolar.",
               ("colegio", "escuela", "docente", "profesor", "rector", "cupo escolar", "matricula", "alimentacion escolar", "restaurante escolar", "transporte escolar", "estudiante", "beca", "secretaria de educacion", "bachillerato")),
    Dependency("ambiente", "Secretaría de Ambiente", "Contaminación, árboles, fauna, ruido ambiental y recursos naturales.",
               ("contaminacion", "arbol", "arboles", "poda", "tala", "quebrada", "rio", "maltrato animal", "fauna", "quema", "vertimiento", "humo", "basura en el rio", "ambiental", "mascotas", "ruido de fabrica")),
    Dependency("planeacion", "Planeación y Urbanismo", "Licencias, uso del suelo, estratificación y espacio público.",
               ("licencia de construccion", "curaduria", "uso del suelo", "estratificacion", "plan de ordenamiento", "construccion ilegal", "invasion", "lote", "nomenclatura", "urbanismo", "espacio publico", "andenes invadidos", "estrato", "obra sin licencia")),
    Dependency("servicios_publicos", "Servicios Públicos Domiciliarios", "Agua, alcantarillado, energía, gas y aseo.",
               ("agua", "acueducto", "alcantarillado", "energia", "gas", "fuga de gas", "factura de agua", "fuga de agua", "aseo", "recoleccion de basuras", "medidor", "corte del servicio", "reconexion", "apagon", "presion del agua", "factura de servicios", "recibo de agua", "recibo de luz", "basuras")),
    Dependency("seguridad", "Seguridad y Convivencia", "Seguridad ciudadana, convivencia, policía y comisarías.",
               ("policia", "robo", "hurto", "atraco", "inseguridad", "pandilla", "rina", "cai", "camaras de seguridad", "microtrafico", "convivencia", "inspeccion de policia", "bar", "venta de licor", "vigilancia", "ruido de vecinos", "ruido", "venta de drogas", "expendio de drogas", "drogas", "fiesta", "consumo de drogas")),
    Dependency("control_interno", "Control Interno Disciplinario", "Conductas de servidores públicos, corrupción y contratación irregular.",
               ("funcionario corrupto", "soborno", "coima", "investigacion disciplinaria", "proceso disciplinario", "conducta del servidor", "contrato irregular", "trafico de influencias", "nepotismo", "peculado", "abuso de autoridad", "licitacion", "dinero por debajo de la mesa", "pidio dinero", "me pidio dinero", "agilizar el tramite", "sin concurso", "corrupcion", "cobro indebido")),
    Dependency("desarrollo_social", "Desarrollo Social", "Subsidios, adulto mayor, víctimas, población vulnerable y familia.",
               ("subsidio", "adulto mayor", "colombia mayor", "subsidio de arriendo", "victima", "desplazado", "familias en accion", "sisben", "ayuda humanitaria", "discapacidad", "habitante de calle", "comisaria de familia", "violencia intrafamiliar", "bienestar", "madre cabeza de hogar", "jovenes en accion", "bono")),
)


@dataclass
class Taxonomy:
    types: tuple[Option, ...] = TYPES
    urgency: tuple[Option, ...] = URGENCY
    subtypes: tuple[Option, ...] = SUBTYPES
    dependencies: tuple[Dependency, ...] = DEFAULT_DEPENDENCIES
    fallback_dependency: str = FALLBACK_DEPENDENCY
    _labels: dict[str, dict[str, str]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._labels = {
            "type": {o.id: o.label for o in self.types},
            "urgency": {o.id: o.label for o in self.urgency},
            "subtype": {o.id: o.label for o in self.subtypes},
            "dependency": {d.id: d.name for d in self.dependencies},
        }

    def label(self, head: str, id_: str) -> str:
        return self._labels[head].get(id_, id_)

    def dependency(self, id_: str) -> Dependency | None:
        return next((d for d in self.dependencies if d.id == id_), None)

    def dependency_ids(self) -> list[str]:
        return [d.id for d in self.dependencies]

    def to_dict(self) -> dict:
        opt = lambda o: {"id": o.id, "label": o.label, "description": o.description}  # noqa: E731
        return {
            "types": [opt(o) for o in self.types],
            "urgency": [opt(o) for o in self.urgency],
            "subtypes": [opt(o) for o in self.subtypes],
            "dependencies": [{"id": d.id, "name": d.name, "description": d.description, "keywords": list(d.keywords)} for d in self.dependencies],
            "fallback_dependency": self.fallback_dependency,
        }

    @staticmethod
    def from_dict(data: dict) -> "Taxonomy":
        deps = tuple(Dependency(d["id"], d["name"], d.get("description", ""), tuple(d.get("keywords", []))) for d in data["dependencies"])
        fallback = data.get("fallback_dependency", FALLBACK_DEPENDENCY)
        if fallback not in {d.id for d in deps}:
            raise ValueError(f"fallback_dependency «{fallback}» no está en la lista de dependencias")
        return Taxonomy(dependencies=deps, fallback_dependency=fallback)

    @staticmethod
    def load(path: str | None) -> "Taxonomy":
        if not path:
            return Taxonomy()
        with open(path, encoding="utf-8") as fh:
            return Taxonomy.from_dict(json.load(fh))
