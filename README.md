# pqrsd-router-ai

Servicio de **IA** del proyecto *Clasificador y Enrutador Inteligente de PQRSD para Entidades Públicas*.
Es el tercer repositorio del sistema (junto a `pqrsd-router-frontend` y `pqrsd-router-backend`).

Recibe el texto libre que escribe el ciudadano y devuelve, **en milisegundos y con justificación en español**:

* **Tipo**: petición · queja · reclamo · sugerencia · denuncia (y, si es petición, el subtipo: general, información/documentos, consulta).
* **Dependencia competente** (12 dependencias municipales por defecto; configurable).
* **Nivel de urgencia** (crítica/alta/media/baja) y un **puntaje de prioridad 0–100** para ordenar la bandeja.
* **Entidades**: fechas (incluidas «ayer», «hace 3 días»), montos, lugares, direcciones, trámites, personas, cédulas, teléfonos, correos, placas — con marca de **dato personal** y texto anonimizado.
* **`needs_review`**: cuándo un funcionario debe confirmar (baja confianza, texto muy corto, empate entre dependencias, urgencia escalada por riesgo vital).

> **Estado: avance funcional (v0.1.0)**, no el proyecto terminado. Lee *Qué está hecho y qué no* y, sobre todo,
> *Honestidad sobre la precisión*: **el modelo arranca con un corpus SINTÉTICO**; para producción hay que reentrenarlo con PQRSD reales.

## Cómo ejecutarlo

Requisitos: **Python 3.11+** (probado con 3.13).

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt  # incluye pytest y httpx
cp .env.example .env                 # opcional; MODELS_DIR persiste el modelo y FEEDBACK_FILE las correcciones

uvicorn app.main:app --reload --port 8000
#   Swagger: http://localhost:8000/docs      Salud: http://localhost:8000/health

python -m pytest -q                  # o: python -m unittest discover -s tests -t .
python scripts/evaluate.py --show-errors   # mide el clasificador con textos escritos a mano
```

Al primer arranque (sin modelo guardado) entrena el modelo de arranque: **≈ 8 s**. Con `MODELS_DIR` definido solo ocurre una vez.

Con Docker:
```bash
docker build -t pqrsd-router-ai .
docker run -p 8000:8000 -v "$PWD/data/models:/data/models" -v "$PWD/data/feedback:/data/feedback" pqrsd-router-ai
```

Prueba rápida:
```bash
curl -s localhost:8000/v1/classify -H 'content-type: application/json' -d '{
  "text": "Hace tres semanas no llega el agua a mi barrio Santa Lucía y tengo un bebé. Soy Ana Pérez, cédula 52.123.456.",
  "redact": true }' | python -m json.tool
```

## Arquitectura

```
app/
├── main.py        FastAPI: solo cablea HTTP ↔ servicio (CORS, API key, errores)
├── service.py     RouterService: casos de uso (classify, batch, entities, feedback, retrain) — sin framework
├── classifier.py  HybridClassifier: mezcla modelo + reglas, umbrales, fallback, escalamiento, prioridad, razones en español
├── model.py       TextModel: TF-IDF (palabras 1-2 + caracteres 3-5) + 4 cabezas de Regresión Logística
├── rules.py       Léxicos explicables (sin tildes, con límites de palabra) para tipo, urgencia, subtipo y dependencia
├── entities.py    Extracción de entidades por reglas + anonimización (offsets sobre el texto original)
├── taxonomy.py    Tipos, urgencias, subtipos y dependencias (TAXONOMY_FILE para personalizar)
├── corpus.py      Generador del corpus SINTÉTICO de arranque (determinista)  ·  corpus_data.py: situaciones y plantillas
├── store.py       ModelStore (joblib, escritura atómica) y FeedbackStore (JSON Lines, append-only)
├── schemas.py     Contrato pydantic v2  ·  errors.py: ServiceError(code, mensaje_es, status)  ·  text.py: normalización
scripts/           evaluate.py (medir) · train.py (reentrenar sin servidor)
tests/             unitarias + realistic_set.py (30 textos escritos a mano, fuera de las plantillas)
docs/CONTRACT.md   contrato compartido por los 3 repos
```

Capas: **HTTP (`main.py`) → servicio → clasificador (modelo + reglas + entidades) → almacén**. Solo `main.py` importa FastAPI.

### Cómo clasifica (modelo híbrido)
1. **Modelo**: un vectorizador TF-IDF (palabras y n-gramas de caracteres, robusto a faltas de ortografía) y una **Regresión
   Logística por cabeza** (`type`, `dependency`, `urgency`, `subtype`) con `class_weight="balanced"`.
2. **Reglas explicables**: léxicos en español sin tildes con pesos 1–3. Dan (a) la **justificación** que ve el funcionario
   («menciona «fuga de gas», «huele muy fuerte»…») y (b) un *prior* para casos raros o nuevos.
3. **Mezcla**: el modelo se *atempera* (`p^(1/T)` con `T` por cabeza: tipo 3, dependencia 1, urgencia 5) porque un modelo entrenado
   con plantillas es demasiado seguro ante texto real; el peso de las reglas crece con la evidencia
   (`mix × min(1, puntaje/6)`; `mix`: tipo 0.5, dependencia 0.3, urgencia 0.5, subtipo 0.4).
4. **Seguridad primero**: si una regla crítica suma ≥ 3 (fuga de gas, cable caído, amenaza de muerte, niño casi atropellado…) la
   urgencia **se escala a crítica** aunque el modelo discrepe (un falso positivo cuesta menos que una emergencia sin atender) y se marca para revisión.
5. **Dependencia dudosa**: si la mejor dependencia tiene < 0.30 de probabilidad se envía a *Atención al Ciudadano* con `routed_to_fallback = true`.
6. **Prioridad**: esperanza de los valores de urgencia (95/72/42/15) con un piso por nivel (crítica ≥ 85, alta ≥ 62, media ≥ 30), de modo que
   el puntaje nunca contradiga el nivel.
7. **Aprendizaje continuo**: cada corrección de un funcionario llega por `POST /v1/feedback`; `POST /v1/retrain` reentrena con
   sintético + correcciones (peso ×5 por defecto) y reemplaza el modelo en caliente (escritura atómica).

### ¿Zero-shot o *fine-tuning*?
El caso de estudio admite ambos. Aquí se eligió un modelo **ligero entrenable en CPU** (TF-IDF + regresión logística) porque
corre en cualquier servidor barato, responde en ~6 ms, es explicable y aprende con pocas correcciones. **Gancho zero-shot (no incluido):**
`HybridClassifier._one` recibe `model_p` por cabeza; para usar un NLI multilingüe (p. ej. `joeddav/xlm-roberta-large-xnli`) basta
con generar `model_p["dependency"]` desde sus etiquetas (hipótesis = descripción de cada dependencia en `taxonomy.py`) cuando
`model.heads` esté vacío o la confianza sea baja. Requiere `transformers` + `torch` (≈ 2 GB): por eso quedó fuera del avance.

## Honestidad sobre la precisión
| Medida | Resultado | Cómo leerlo |
|--------|-----------|-------------|
| Validación 85/15 sobre el corpus **sintético** | ≈ 100 % | **No significa nada**: el modelo memoriza las plantillas. |
| **30 textos escritos a mano** (`tests/realistic_set.py`), modelo de arranque 6 000 muestras | tipo **90 %** · dependencia **83 %** · urgencia **80 %** | Indicativo. Con 30 casos el margen de error es de ± 10 puntos. |
| De los 12 textos con algún error, marcados `needs_review` | 5 | La revisión humana atrapa menos de la mitad de los errores: **no quites al funcionario del circuito**. |
| Latencia | ≈ 6 ms por texto (CPU, 1 hilo) | Medida en el sandbox. |

⚠️ Los léxicos y los parámetros de mezcla se ajustaron mirando ese mismo conjunto de 30 textos, así que **los porcentajes son
optimistas**. Las fronteras *queja / reclamo / petición* son difusas incluso entre humanos. La medida válida es la que haga la entidad con
**sus** PQRSD históricas etiquetadas: `python scripts/evaluate.py --csv etiquetadas.csv` (columnas `text,type,dependency,urgency`).

## Qué está hecho y qué no

| Estado | Elemento |
|--------|----------|
| ✅ Verificado (`python -m pytest -q` → 47 pruebas, 0 omitidas; Python 3.11 con fastapi/httpx reales) | Capa HTTP (`app/main.py`: rutas, API key, CORS, errores 422), integración real con `pqrsd-router-backend` (clasificar, vista previa, feedback y `POST /v1/retrain` desde la bandeja), imagen Docker dentro del `docker compose` de los 3 repos. Léxicos y reglas, extracción de entidades y anonimización, corpus sintético, modelo, clasificador híbrido, escalamiento crítico, prioridad, servicio, retroalimentación persistente, reentrenamiento y recarga, taxonomía personalizada, guardas de regresión sobre textos a mano |
| ❌ No hecho | Zero-shot / transformers, NER con modelo (hoy es por reglas), evaluación con PQRSD reales, calibración de probabilidades con datos reales, detección de duplicados/«casos masivos», idioma distinto del español, métricas Prometheus, autenticación por usuario |

`python -m pytest -q` ejecuta también `tests/test_api.py` (FastAPI real con `TestClient`).

## Limitaciones conocidas
* El modelo de arranque se entrenó con **plantillas sintéticas** y reglas escritas por nosotros; no hay datos reales de ninguna entidad.
* Las entidades por reglas no entienden todas las formas de escribir fechas o nombres; la lista de ciudades/departamentos es parcial.
* `joblib` usa *pickle*: carga modelos solo de un directorio propio y no accesible a terceros.
* El texto del ciudadano puede contener datos personales: `/v1/classify` **no los guarda**; solo `/v1/feedback` persiste texto (úsalo con `redact` aplicado si tu política lo exige).

## Despliegue (más adelante)
Imagen Docker lista. Variables: `MODELS_DIR` y `FEEDBACK_FILE` (volúmenes persistentes), `AI_API_KEY` (el backend la envía como `X-API-Key`),
`TAXONOMY_FILE`, `CORS_ORIGINS` (normalmente vacío), `BOOTSTRAP_SAMPLES`. Una sola réplica con volumen es suficiente para empezar
(el reentrenamiento es en proceso); para varias réplicas, mover el modelo y el archivo de retroalimentación a un bucket/base de datos.

## Nombre de repositorio sugerido
`pqrsd-router-ai`
