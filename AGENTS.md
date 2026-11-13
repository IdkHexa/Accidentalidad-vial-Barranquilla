# AGENTS.md — Accidentalidad Vial en Barranquilla

## Role

The agent also acts as a teaching mentor. When the developer asks for
explanations (architecture decisions, why a pattern is used, what a
library does, etc.), the agent explains the concept thoroughly instead
of jumping to write code. The developer is learning professional
software engineering practices and uses the agent as a sounding board,
not as a code generator.

## Quick start

```powershell
# First time
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Ensure .env exists (PostgreSQL vars, APP_HOST/APP_PORT, optional GOOGLE_MAPS_KEY)
# Run the full pipeline (API → ETL → DB)
python main.py

# Run the FastAPI web server (defaults to 127.0.0.1:8080)
python run.py

# Run tests
python -m unittest discover -v tests/
```

## Architecture

MVC layered project. Two owners, strict boundary:

| Layer | Owner | Modules | Status |
|-------|-------|---------|--------|
| `api/`, `models/`, `data/`, `analytics/` | Jofier | 1–4 + Analytics | Done |
| `controllers/`, `views/` | Juan | 5–8 (FastAPI + Jinja2/ECharts/Leaflet) | Done |

- `main.py` — ETL CLI entry point, calls `init_db()` then `ejecutar_etl()`
- `run.py` — Web entry point, runs `controllers.main_controller:app` via Uvicorn (`APP_HOST`/`APP_PORT`, default `127.0.0.1:8080`)
- `config.py` — loads `.env` anchored to `BASE_DIR`, builds `DATABASE_URL` via SQLAlchemy `URL.create` (PostgreSQL with SQLite fallback), exports `API_URL`, `GOOGLE_MAPS_KEY`, `APP_HOST`, `APP_PORT`

## Analytics Module

Clustering geoespacial con DBSCAN para identificar zonas críticas.

- `analytics/clustering.py` — Functions: `calcular_pesos()`, `ejecutar_clustering_dbscan()` (pure), `resumir_clusters()`, `obtener_clusters_pipeline()` (orchestrator), `obtener_clusters()` (legacy wrapper)
- `data/storage.py` — `obtener_para_clustering()` returns 7-column geocoded DataFrame (`latitud IS NOT NULL`) for analytics
- Tests: `tests/test_clustering.py` — unit tests with synthetic data

Key design decisions:
- **Pure function**: `ejecutar_clustering_dbscan()` never touches the database
- **Severity weighting**: `sample_weight = max(cantidad_accidentes, 1) + 1.5*heridos + 3.0*muertos`
- **Bounding box**: Filters coordinates outside Barranquilla (10.90–11.05, -74.90–-74.75)
- **Explicit conversion**: `kilometros_a_radianes()` eliminates magic numbers (`RADIO_DEFECTO_METROS = 100.0`, `MIN_MUESTRAS_DEFECTO = 50`)
- **Optimized DBSCAN**: `algorithm="ball_tree"`, `n_jobs=1` (thread-safe inside web server, paired with TTL cache in `controllers/main_controller.py`)

## Environment

`.env` (git-ignored) configures PostgreSQL (`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` plus `POSTGRE_*` aliases, `POSTGRES_HOST`, `POSTGRES_PORT`), web binding (`APP_HOST`, `APP_PORT`), and optional `GOOGLE_MAPS_KEY`.
The app warns but doesn't crash if `GOOGLE_MAPS_KEY` is missing or denied — `GeoCoder` sets `self.gmaps = None`
and `obtener_coordenadas()` returns `None` immediately, relying on `data/geocache.json` instead of crashing the pipeline.

## Database (PostgreSQL / SQLite + SQLAlchemy)

- PostgreSQL 16 (`docker-compose.yml`, `127.0.0.1:8448:5432`) when Postgres vars are configured; local `accidentalidad.db` fallback (git-ignored via `*.db`)
- Engine (`pool_pre_ping=True`), 4 secondary indexes (`ix_accidentes_anio`, `ix_accidentes_gravedad`, `ix_accidentes_fecha`, `ix_accidentes_coords`), and ORM model live in `data/database.py`
- `init_db()` creates tables and indexes idempotently — call it in `main.py` CLI and FastAPI `lifespan`
- Repository DAO in `data/storage.py` (`AccidenteRepository`) — always use it (injected via `Depends(get_repository)`), never call `session` or `AccidenteDB` directly from controllers/routes

## DTO ↔ ORM mapping gotchas

The Pydantic DTO (`AccidenteDTO`) uses Spanish field names with accents.
The SQLAlchemy model (`AccidenteDB`) uses the same names **without accents**.
`desde_dto()` in `data/database.py` handles the mapping.

Critical mappings that break if you guess them:

| Pydantic (`AccidenteDTO`) | SQLAlchemy column |
|---|---|
| `AÑO_ACCIDENTE` | `a_o_accidente` |
| `SITIO_EXACTO_ACCIDENTE` | `sitio_exacto_accidente` |
| `CANTIDAD_ACCIDENTES` | `cantidad_accidentes` |

Never write `A_O_ACCIDENTE`, `SITIO_ACCIDENTE_EXACTO`, or `CANTIDAD_ACCIDENTE` — those don't exist on the DTO.

## Code style

- Docstrings in **Spanish**, explaining the *why* not just the *what*
- Module, class, and method docstrings on everything — triple-quote, PEP 257
- Docstrings are written by the agent; all functional code is written by the human
- Backtick-quoted parameter names in docstrings: ```` ``limite_registros`` ````
- `black` / `isort` are not configured; the project follows manual formatting
- Commit messages in Spanish

## Testing

- Framework: `unittest` (stdlib, no pytest)
- Run all: `python -m unittest discover tests/`
- Run one file: `python -m unittest tests.test_parser`
- Run storage tests: `python -m unittest tests.test_storage`
- Run clustering tests: `python -m unittest tests.test_clustering`
- Tests use a separate geocache file (`tests/test_geocache.json`) to avoid polluting real data
- Storage tests use an in-memory SQLite database (`:memory:`) — never touch `accidentalidad.db`
- Clustering tests use synthetic DataFrames — no database dependency

## Known IDE hazard

Autocompletion (VS Code / Copilot) silently reverts manual edits before save.
After pasting corrected code, **always verify the file was saved** and re-read it
before declaring "done". This has caused multiple "fix-apply-fix-again" cycles.

## Web modules & remaining placeholders

- Modules 5–6: FastAPI in `controllers/main_controller.py` (REST API, `/health`, DBSCAN hotspot caching, Jinja2 routes)
- Modules 7–8: Frontend in `views/static/css/app.css` and `views/templates/{base,index,dashboard,mapa,registro}.html` (Apache ECharts, Leaflet + `leaflet.heat` + DBSCAN hotspots)
- `utils/logger.py` is implemented (`RotatingFileHandler` + `reiniciar_logging()`); legacy placeholders (`sync_manager.py`, `visualizer.py`, `app.py`) remain unused
