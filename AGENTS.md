# AGENTS.md — Accidentalidad Vial en Barranquilla

## Role

This agent NEVER generates implementation code. It only:
- Reviews and debugs existing code
- Writes docstrings (Spanish, PEP 257)
- Answers technical questions

The human writes ALL functional code. If the agent is asked to write code,
it must refuse and explain why.

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

# Ensure .env exists with GOOGLE_MAPS_KEY
# Run the full pipeline (API → ETL → SQLite)
python main.py

# Run tests
python -m unittest discover tests/
```

## Architecture

MVC layered project. Two owners, strict boundary:

| Layer | Owner | Modules | Status |
|-------|-------|---------|--------|
| `api/`, `models/`, `data/` | Jofier | 1–4 | Done |
| `controllers/`, `views/` | Juan | 5–8 | Placeholders |

- `main.py` — entry point, calls `init_db()` then `ejecutar_etl()`
- `config.py` — loads `.env`, exports `API_URL` and `GOOGLE_MAPS_KEY`

## Environment

Single required env var: `GOOGLE_MAPS_KEY` in `.env` (git-ignored).
The app warns but doesn't crash if missing — `GeoCoder` sets `self.gmaps = None`
and `obtener_coordenadas()` returns `None` immediately, so records are stored
without coordinates instead of crashing the pipeline.

## Database (SQLite + SQLAlchemy)

- DB file: `accidentalidad.db` (git-ignored via `*.db`)
- Engine and model live in `data/database.py`
- `init_db()` creates tables idempotently — call it once at startup
- Repository DAO in `data/storage.py` — always use it, never call `session` or `AccidenteDB` directly from outside

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
- Tests use a separate geocache file (`tests/test_geocache.json`) to avoid polluting real data
- Storage tests use an in-memory SQLite database (`:memory:`) — never touch `accidentalidad.db`

## Known IDE hazard

Autocompletion (VS Code / Copilot) silently reverts manual edits before save.
After pasting corrected code, **always verify the file was saved** and re-read it
before declaring "done". This has caused multiple "fix-apply-fix-again" cycles.

## Future modules (for reference)

- Modules 5–6 (Juan): FastAPI in `controllers/main_controller.py`, endpoints for data
- Modules 7–8 (Juan): Frontend in `views/` — Jinja2 templates, Alpine.js, Apache ECharts
- Placeholder files (`sync_manager.py`, `logger.py`, `visualizer.py`, `app.py`, CSS/JS) are not yet implemented — do not assume they work
