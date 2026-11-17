# PQRSD Inteligente · Servicio de IA

Servicio de **clasificación de texto y extracción de entidades** del proyecto *Clasificador y Enrutador Inteligente de PQRSD
para Entidades Públicas*. Recibe lo que escribe el ciudadano con sus propias palabras y responde en milisegundos, con
justificación en español, **qué es, a quién le corresponde y qué tan urgente es**.

| Repositorio | Rol |
|---|---|
| [`pqrsd-router-frontend`](https://github.com/JuanMaya8/pqrsd-router-frontend) | Portal ciudadano y bandeja de funcionarios (Next.js) |
| [`pqrsd-router-backend`](https://github.com/JuanMaya8/pqrsd-router-backend) | Radicación, plazos legales, flujo y tiempo real (NestJS) |
| **`pqrsd-router-ai`** (este) | Clasificación híbrida, entidades y aprendizaje continuo (FastAPI + scikit-learn) |

> Guía de demostración (levantar todo con una orden, claves de prueba y recorrido de 10 minutos):
> [`pqrsd-router-frontend/docs/GUIA_DEMO.md`](https://github.com/JuanMaya8/pqrsd-router-frontend/blob/main/docs/GUIA_DEMO.md)

---

## Qué devuelve

| Salida | Detalle |
|---|---|
| **Tipo** | Petición · Queja · Reclamo · Sugerencia · Denuncia. Si es petición, también el subtipo (general, información/documentos, consulta), que define el plazo legal |
| **Dependencia competente** | Una de 12 dependencias municipales (Salud, Movilidad, Hacienda, Infraestructura, Educación, Ambiente, Servicios Públicos…). Configurable |
| **Urgencia y prioridad** | Crítica · Alta · Media · Baja, y un puntaje de prioridad de 0 a 100 para ordenar la bandeja |
| **Entidades** | Fechas (también «ayer» o «hace 3 días»), montos, lugares, direcciones, trámites, placas, radicados previos, personas, cédulas, teléfonos y correos |
| **Datos personales** | Las entidades personales se marcan y el texto se puede anonimizar |
| **`needs_review`** | Indica cuándo un funcionario debe confirmar: baja confianza, empate entre dependencias, texto muy corto o urgencia escalada por riesgo |
| **Razones** | Frases que explican la decisión, para que el funcionario entienda por qué |

## Cómo clasifica: modelo + reglas

```
texto ─┬─► Modelo (TF-IDF + Regresión Logística) ─┐
       │                                          ├─► mezcla ─► umbrales y seguridad ─► resultado + razones
       └─► Reglas explicables (léxicos en español) ┘
```

1. **Modelo de aprendizaje automático.** El texto se vectoriza con **TF-IDF** por palabras (1–2) y por fragmentos de caracteres (3–5),
   lo que lo hace tolerante a faltas de ortografía y tildes. Una **regresión logística** por cada salida (tipo, dependencia, urgencia y subtipo),
   con clases balanceadas.
2. **Reglas explicables.** Léxicos en español con pesos de 1 a 3 («fuga de gas», «no llega el agua», «cobro doble»…). Aportan la
   justificación que ve el funcionario y ayudan en casos poco frecuentes.
3. **Mezcla.** Las probabilidades del modelo se suavizan (temperatura por salida) y se combinan con las reglas; el peso de las reglas crece
   con la evidencia encontrada.
4. **Seguridad primero.** Si aparece una frase de riesgo para la vida o la integridad, la urgencia **se escala a crítica** aunque el modelo
   discrepe: una falsa alarma cuesta menos que una emergencia sin atender.
5. **Duda = revisión humana.** Con baja confianza la solicitud se marca para revisión, y si ninguna dependencia es clara se envía a
   *Atención al Ciudadano*.
6. **Aprendizaje continuo.** Cada corrección de un funcionario llega anonimizada a `POST /v1/feedback`; `POST /v1/retrain` reentrena
   con esas correcciones (con más peso) y reemplaza el modelo sin reiniciar el servicio.

**¿Por qué no un modelo de lenguaje grande?** Este modelo corre en CPU en un servidor gratuito, responde en ≈ 6 ms, es explicable, no envía
datos de ciudadanos a terceros y aprende con pocas correcciones. El diseño deja un punto de extensión para añadir un clasificador
*zero-shot* (p. ej. XLM-RoBERTa NLI) cuando haga falta.

## Precisión: medida con honestidad

El modelo inicial se entrena con un **corpus sintético de 6 000 ejemplos** generados a partir de situaciones y plantillas, balanceado por tipo
y dependencia. Es sintético y así se declara en la respuesta del servicio.

| Medida | Resultado |
|---|---|
| 30 textos escritos a mano, fuera de las plantillas (`tests/realistic_set.py`) | Tipo **90 %** · Dependencia **83 %** · Urgencia **80 %** |
| Latencia | ≈ 6 ms por texto (CPU, un hilo) |

Con 30 casos el margen es de ± 10 puntos, así que estas cifras son **indicativas**. La medida válida es la que haga una entidad con sus
PQRSD históricas etiquetadas:

```bash
python scripts/evaluate.py --csv etiquetadas.csv   # columnas: text,type,dependency,urgency
```

## API

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/v1/classify` | Clasifica un texto (opcional `redact: true` para anonimizar) |
| `POST` | `/v1/classify/batch` | Clasifica varios textos |
| `POST` | `/v1/entities` | Solo extracción de entidades |
| `POST` | `/v1/feedback` | Registra la corrección de un funcionario |
| `POST` | `/v1/retrain` | Reentrena con las correcciones guardadas |
| `GET` | `/v1/model` · `/v1/taxonomy` · `/health` | Información del modelo, vocabulario y estado |

Documentación interactiva (Swagger) en `/docs`. El contrato completo entre los 3 repositorios está en [`docs/CONTRACT.md`](docs/CONTRACT.md).

## Ejecutar en local

Requisitos: **Python 3.11+**.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```

El primer arranque entrena el modelo inicial (≈ 8 s).

Prueba rápida:

```bash
curl -s localhost:8000/v1/classify -H 'content-type: application/json' -d '{
  "text": "Hace tres semanas no llega el agua a mi barrio Santa Lucía y tengo un bebé.",
  "redact": true }'
```

Pruebas:

```bash
python -m pytest -q                        # unitarias, API y casos realistas
python scripts/evaluate.py --show-errors   # precisión sobre textos escritos a mano
```

Con Docker: `docker build -t pqrsd-router-ai . && docker run -p 8000:8000 pqrsd-router-ai`.

## Estructura

```
app/
├── main.py         API FastAPI (rutas, API key, CORS, errores). Único archivo que conoce FastAPI
├── service.py      Casos de uso: clasificar, entidades, feedback, reentrenar
├── classifier.py   Clasificador híbrido: mezcla, umbrales, escalamiento, prioridad y razones
├── model.py        TF-IDF + regresiones logísticas
├── rules.py        Léxicos explicables
├── entities.py     Extracción de entidades y anonimización
├── taxonomy.py     Tipos, urgencias, subtipos y dependencias (personalizable)
├── corpus.py       Generador del corpus sintético (determinista)
└── store.py        Persistencia del modelo y de las correcciones (archivo o PostgreSQL)
scripts/            evaluate.py · train.py
tests/              Pruebas automatizadas
```

## Variables de entorno

| Variable | Para qué |
|---|---|
| `AI_API_KEY` | Clave que el backend envía en `X-API-Key` |
| `DATABASE_URL` | PostgreSQL para guardar las correcciones (recomendado en la nube) |
| `FEEDBACK_FILE`, `MODELS_DIR` | Alternativa en disco para correcciones y modelo |
| `TAXONOMY_FILE` | Taxonomía propia de la entidad |
| `CORS_ORIGINS`, `BOOTSTRAP_SAMPLES` | Orígenes permitidos y tamaño del corpus inicial |

## Despliegue

Desplegado en **Render** con la base de datos en **Neon** (PostgreSQL). Se crea junto con el backend desde el blueprint `render.yaml`
del repositorio `pqrsd-router-backend`; el paso a paso está en su
[`docs/DEPLOY.md`](https://github.com/JuanMaya8/pqrsd-router-backend/blob/main/docs/DEPLOY.md).
Consume ≈ 175 MB de RAM y cabe en el plan gratuito.

## Limitaciones y trabajo futuro

* Entrenar y medir con PQRSD reales de una entidad (lo que más mejora la calidad).
* Clasificación *zero-shot* para dependencias nuevas y reconocimiento de entidades con un modelo (hoy por reglas).
* Calibrar las confianzas con datos reales.
* Detectar solicitudes duplicadas o campañas masivas.
