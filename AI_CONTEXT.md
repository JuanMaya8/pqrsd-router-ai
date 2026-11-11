# AI_CONTEXT.md — contexto para la IA generadora de código

> Léeme completo antes de tocar nada. Este repo es **1 de 3** del proyecto *pqrsd-router* (Clasificador y Enrutador
> Inteligente de PQRSD para Entidades Públicas). Idioma: **código, nombres de archivo, commits y pruebas en inglés;
> textos para el usuario (mensajes, explicaciones) en español**.

## 1. Objetivo del proyecto (caso de estudio original)
Hoy los funcionarios leen cada PQRSD una por una para decidir a qué dependencia pertenece y qué tan urgente es: hay cuellos
de botella y respuestas tardías, con incumplimiento de plazos legales. Propuesta: el ciudadano escribe en texto libre y el
sistema **clasifica al recibirla** por tipo (petición/queja/reclamo/sugerencia/denuncia), **dependencia competente** y **nivel de
urgencia**. Para pruebas de volumen puede usarse un dataset público real (p. ej. issues de GitHub vía API, adaptado). La IA:
clasificación de texto (zero-shot o fine-tuned) + extracción de entidades (fechas, lugares, nombres de trámites).
Diferencial: resuelve un cuello de botella burocrático medible y no necesita datos inventados.

## 2. Los 3 repos y el rol de ESTE repo
| Repo | Stack | Rol |
|------|-------|-----|
| `pqrsd-router-frontend` | Next.js 14 + TS | Portal ciudadano (SSG/CSR/SSR/ISR) y bandeja del funcionario en vivo |
| `pqrsd-router-backend` | NestJS + TS | Radicación, plazos legales en días hábiles, SLA, flujo de estados, estadísticas, tiempo real, proxy a la IA |
| **`pqrsd-router-ai`** (este) | FastAPI + scikit-learn | Clasificación híbrida (modelo + reglas), entidades, retroalimentación y reentrenamiento |

Contrato exacto: `docs/CONTRACT.md` (idéntico en los 3 repos). **No lo rompas sin cambiarlo en los otros dos.**

## 3. Arquitectura de este repo
`main.py` (solo cableado) → `service.py` (casos de uso) → `classifier.py` (mezcla) → `model.py` / `rules.py` / `entities.py`;
`store.py` persiste modelo y retroalimentación; `taxonomy.py` define el vocabulario; `schemas.py` es el contrato.

Invariantes que NO se deben romper:
* `service.py`, `classifier.py`, etc. **no importan FastAPI** (se prueban sin servidor).
* `ModelStore` y `FeedbackStore` definen `__len__` → un almacén vacío es *falsy*: **nunca** `store or X()`; usa `is not None`
  (bug real, ya corregido dos veces, en este repo y en docu-sentinel).
* `entities.fold()` conserva la longitud del texto (los `start/end` apuntan al texto original). No uses `normalize()` para offsets.
* Las reglas se escriben **sin tildes** y en minúscula; `*` final = prefijo.
* El puntaje de prioridad nunca contradice el nivel (`URGENCY_FLOOR`); la escalada crítica (`CRITICAL_RULE_SCORE = 3`) es una decisión de
  seguridad: un falso positivo cuesta menos que una emergencia sin atender. No la quites sin acuerdo explícito.
* `MODEL_TEMPERATURE` y `RULE_MIX` se calibraron contra `tests/realistic_set.py`. Si los cambias, ejecuta `python scripts/evaluate.py --show-errors`.
* Resultados deterministas (semillas fijas) y mensajes al usuario en español.
* El corpus sintético está **etiquetado como sintético** en `ModelInfo.note`; no lo presentes como datos reales.

## 4. Cómo ejecutar y probar
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                         # o: python -m unittest discover -s tests -t .
python scripts/evaluate.py --show-errors    # exactitud en textos escritos a mano
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/docs
```

## 5. Estado exacto (hasta dónde llegué)
**Hecho y VERIFICADO** (sandbox: Python 3.13, scikit-learn 1.9.1, pydantic 2; `python3 -m unittest discover -s tests -t .` → 45 tests OK, 5 omitidos):
* Reglas, entidades + anonimización, corpus sintético (6 000 muestras, balance por tipo/dependencia), modelo, clasificador híbrido,
  escalada crítica, fallback de dependencia, prioridad, `needs_review`, servicio, retroalimentación persistente, reentrenamiento y recarga
  del modelo guardado, taxonomía personalizada, corrupción de línea en el JSONL tolerada.
* Medido sobre 30 textos escritos a mano (optimista, ver README): tipo 90 %, dependencia 83 %, urgencia 80 %; ≈ 6 ms/texto.

**Verificado al retomar (2026-11-11, Windows, Python 3.11, fastapi/httpx reales):**
* `python -m pytest -q` → 47 pruebas OK, 0 omitidas (incluye `tests/test_api.py`). La capa HTTP funcionó sin cambios.
* Integración real con `pqrsd-router-backend` (proceso `uvicorn` + backend compilado): vista previa, radicación, reclasificación → `POST /v1/feedback`, `POST /v1/retrain` desde `/staff/ai/retrain`.
* `docker compose up --build` con los 3 repos (ver `pqrsd-router-frontend/docker-compose.yml`). Se añadió `.dockerignore` (sin él el contexto incluía `.venv`).
* Se probó añadir una frase de «fuga de gas» al corpus: arregla ese caso pero baja la urgencia de 80 % a 76,7 % en `realistic_set` → **revertido**. El caso queda en Atención al Ciudadano + `needs_review` + urgencia crítica (seguro). Se resuelve con datos reales, no con plantillas.

**Añadido (2026-11-11):** `PgFeedbackStore` (`DATABASE_URL`, tabla `ai_feedback`) para hosts con disco efímero (Render); `psycopg` solo se importa
si hay `DATABASE_URL`. Hereda de `FeedbackStore` y también define `__len__`: **sigue valiendo** «nunca `store or X()`». Probado contra PostgreSQL 16
(`tests/test_pg_store.py`, se omite sin `TEST_DATABASE_URL`) y en Docker: una corrección hecha en la bandeja sobrevive al reinicio de la IA.
Despliegue con **Neon**: `PgFeedbackStore` abre **una conexión corta por operación** (Neon suspende la base y corta conexiones inactivas);
no vuelvas a una conexión larga sin reconexión. Probado con un `psycopg` falso (`tests/test_pg_store_reconnect.py`).

**No hecho:**
* **Datos reales**: recolectar PQRSD históricas etiquetadas por la entidad, evaluar con `scripts/evaluate.py --csv`, reentrenar con peso alto en lo real
  y bajar `MODEL_TEMPERATURE` (los modelos entrenados con datos reales no necesitan tanto atemperamiento). Es lo que más sube la calidad.
* Zero-shot / modelo de lenguaje (gancho descrito en README) y NER con modelo (hoy reglas) — mejorarían dependencia y entidades.
* Calibración de probabilidades con datos reales (hoy las «confianzas» son relativas, no frecuencias reales).
* Detección de PQRSD duplicadas o campañas masivas (muchos ciudadanos, mismo problema) — útil para agrupar y responder una vez.
* Otros idiomas, métricas Prometheus, autenticación por usuario, almacenamiento del modelo fuera del disco local (S3/GCS) para varias réplicas.

## 6. Checklist para llegar al 100 % (en orden)
1. ~~Ejecutar y arreglar `tests/test_api.py` con fastapi real; `docker build`.~~ ✅
2. ~~Prueba de integración con `pqrsd-router-backend` siguiendo `docs/CONTRACT.md` (clasificar, feedback, reentrenar).~~ ✅
3. Conseguir PQRSD reales etiquetadas (o el CSV exportado por el backend con las correcciones) y medir con `evaluate.py --csv`.
4. Reentrenar con datos reales; recalibrar `MODEL_TEMPERATURE`/`RULE_MIX`; ampliar léxicos con los errores reales.
5. Añadir zero-shot para dependencias nuevas sin ejemplos; evaluar si mejora.
6. Observabilidad. Despliegue: listo para Render (feedback en PostgreSQL; ver `pqrsd-router-backend/docs/DEPLOY.md`); varias réplicas ⇒ modelo en almacenamiento compartido.
