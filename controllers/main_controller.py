"""Controlador principal — FastAPI endpoints HTML y REST para accidentalidad vial.

Mantiene la separacion arquitectonica del proyecto: todas las operaciones sobre
base de datos se delegan a ``AccidenteRepository`` mediante ``Depends(get_repository)``
y los manejadores con I/O sincronico se declaran con ``def`` para ejecutarse en el
threadpool de FastAPI sin bloquear el event loop.
"""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
import threading
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analytics.clustering import (
    MIN_MUESTRAS_DEFECTO,
    RADIO_DEFECTO_METROS,
    obtener_clusters_pipeline,
    resumir_clusters,
)
from data.database import SessionLocal, init_db
from data.storage import AccidenteRepository
from models.entidades import _normalizar_texto

_CLUSTER_CACHE: dict[tuple, tuple[float, dict]] = {}
_CLUSTER_CACHE_LOCK = threading.Lock()
_CLUSTER_CACHE_TTL_SEG = 300.0


def invalidar_cache_clusters() -> None:
    """Limpia la cache en memoria tras mutaciones sobre registros."""
    with _CLUSTER_CACHE_LOCK:
        _CLUSTER_CACHE.clear()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa tablas e indices de forma idempotente al iniciar la aplicacion."""
    init_db()
    yield


app = FastAPI(title="Accidentalidad Vial Barranquilla", lifespan=lifespan)

# ── Archivos estaticos y plantillas ───────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

app.mount(
    "/static",
    StaticFiles(directory=str(ROOT_DIR / "views" / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(ROOT_DIR / "views" / "templates"))


# ── Dependencias DAO ──────────────────────────────────────────────────────────
def get_repository():
    """Entrega un ``AccidenteRepository`` ligado a una sesion por peticion."""
    db = SessionLocal()
    try:
        yield AccidenteRepository(db)
    finally:
        db.close()


RepoDep = Annotated[AccidenteRepository, Depends(get_repository)]


# ── Esquemas de validacion ────────────────────────────────────────────────────
class AccidenteUpdate(BaseModel):
    """Carga util validada para actualizar parcialmente un accidente existente."""

    fecha_accidente: str | None = Field(default=None, min_length=4, max_length=50)
    hora_accidente: str | None = Field(default=None, min_length=2, max_length=20)
    gravedad_accidente: str | None = Field(default=None, min_length=2, max_length=50)
    clase_accidente: str | None = Field(default=None, min_length=2, max_length=50)
    a_o_accidente: int | None = Field(default=None, ge=2000, le=2100)
    mes_accidente: str | None = Field(default=None, min_length=3, max_length=20)
    dia_accidente: str | None = Field(default=None, min_length=3, max_length=20)
    sitio_exacto_accidente: str | None = Field(default=None, max_length=300)
    cant_heridos_en_sitio_accidente: int | None = Field(default=None, ge=0)
    cant_muertos_en_sitio_accidente: int | None = Field(default=None, ge=0)
    cantidad_accidentes: int | None = Field(default=None, ge=1)
    latitud: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitud: float | None = Field(default=None, ge=-180.0, le=180.0)


def _parse_float_opcional(valor: str | None, campo: str) -> float | None:
    """Convierte texto de formulario HTML a flotante o ``None`` si viene vacio."""
    if valor is None:
        return None
    limpio = valor.strip()
    if not limpio:
        return None
    try:
        return float(limpio)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Valor numerico invalido para '{campo}': {valor}",
        ) from exc


# ── Salud y paginas HTML ──────────────────────────────────────────────────────
@app.get("/health")
def healthcheck(repo: RepoDep):
    """Verifica conectividad con la base de datos mediante el repositorio."""
    try:
        total = repo.contar()
        return {"status": "ok", "registros": total}
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Base de datos no disponible: {exc}"
        ) from exc


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Renderiza la pagina de bienvenida."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, repo: RepoDep):
    """Renderiza el tablero estadistico con el conteo base inicial."""
    total = repo.contar()
    return templates.TemplateResponse(request, "dashboard.html", {"total": total})


@app.get("/mapa", response_class=HTMLResponse)
async def mapa(request: Request):
    """Renderiza el visor geoespacial de accidentalidad."""
    return templates.TemplateResponse(request, "mapa.html")


@app.get("/registro", response_class=HTMLResponse)
async def registro(request: Request):
    """Renderiza el formulario de registro manual de accidentes."""
    return templates.TemplateResponse(request, "registro.html")


# ── API de estadisticas ───────────────────────────────────────────────────────
@app.get("/api/stats/resumen")
def stats_resumen(repo: RepoDep):
    """KPIs principales para las tarjetas del dashboard e inicio."""
    return repo.obtener_resumen()


@app.get("/api/stats/años")
def stats_años_disponibles(repo: RepoDep):
    """Lista los años distintos disponibles para filtros."""
    return repo.obtener_años_disponibles()


@app.get("/api/stats/por_año")
def stats_por_año(repo: RepoDep):
    """Serie historica por año de accidentes, heridos y muertos."""
    return repo.contar_por_año()


@app.get("/api/stats/por_gravedad")
def stats_por_gravedad(repo: RepoDep):
    """Conteo de accidentes agrupados por gravedad."""
    return repo.contar_por_gravedad()


@app.get("/api/stats/por_clase")
def stats_por_clase(repo: RepoDep, limit: int = Query(default=10, ge=1, le=50)):
    """Top de clases de accidente mas frecuentes."""
    return repo.contar_por_clase(limit=limit)


@app.get("/api/stats/por_mes")
def stats_por_mes(repo: RepoDep):
    """Distribucion mensual ordenada de enero a diciembre."""
    return repo.contar_por_mes()


@app.get("/api/stats/por_dia")
def stats_por_dia(repo: RepoDep):
    """Distribucion semanal normalizada de lunes a domingo."""
    return repo.contar_por_dia()


@app.get("/api/stats/por_hora")
def stats_por_hora(repo: RepoDep):
    """Distribucion por franja horaria de 0 a 23 horas."""
    return repo.contar_por_hora()


@app.get("/api/stats/clusters")
def stats_clusters(
    repo: RepoDep,
    radio: float = Query(default=RADIO_DEFECTO_METROS, ge=20.0, le=1000.0),
    min_samples: int = Query(default=MIN_MUESTRAS_DEFECTO, ge=2, le=500),
    anio_desde: int | None = Query(default=None, ge=2000, le=2100),
    anio_hasta: int | None = Query(default=None, ge=2000, le=2100),
):
    """Ejecuta o recupera de cache los hotspots DBSCAN geoespaciales."""
    motor_id = id(repo.session.get_bind())
    clave_cache = (motor_id, round(radio, 2), min_samples, anio_desde, anio_hasta)
    ahora = time.monotonic()

    with _CLUSTER_CACHE_LOCK:
        entrada = _CLUSTER_CACHE.get(clave_cache)
        if entrada and (ahora - entrada[0]) < _CLUSTER_CACHE_TTL_SEG:
            return entrada[1]

    df = obtener_clusters_pipeline(
        repo,
        radio_metros=radio,
        min_muestras=min_samples,
        anio_desde=anio_desde,
        anio_hasta=anio_hasta,
    )
    resultado = resumir_clusters(df)

    with _CLUSTER_CACHE_LOCK:
        _CLUSTER_CACHE[clave_cache] = (ahora, resultado)

    return resultado


# ── API geoespacial y CRUD de accidentes ──────────────────────────────────────
@app.get("/api/mapa/puntos")
def mapa_puntos(
    repo: RepoDep,
    limit: int = Query(default=3000, ge=1, le=10000),
    gravedad: str | None = Query(default=None),
    año: int | None = Query(default=None, ge=2000, le=2100),
):
    """Retorna puntos georreferenciados filtrados para el mapa interactivo."""
    return repo.obtener_puntos_mapa(limit=limit, gravedad=gravedad, año=año)


@app.get("/api/accidentes")
def listar_accidentes(
    repo: RepoDep,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    gravedad: str | None = Query(default=None),
    año: int | None = Query(default=None, ge=2000, le=2100),
):
    """Lista registros paginados con filtros opcionales de gravedad y año."""
    return repo.listar_filtrados(
        limit=limit, offset=offset, gravedad=gravedad, año=año
    )


@app.post("/api/accidentes", status_code=status.HTTP_201_CREATED)
def crear_accidente(
    repo: RepoDep,
    fecha_accidente: str = Form(..., min_length=4, max_length=50),
    hora_accidente: str = Form(..., min_length=2, max_length=20),
    gravedad_accidente: str = Form(..., min_length=2, max_length=50),
    clase_accidente: str = Form(..., min_length=2, max_length=50),
    a_o_accidente: int = Form(..., ge=2000, le=2100),
    mes_accidente: str = Form(..., min_length=3, max_length=20),
    dia_accidente: str = Form(..., min_length=3, max_length=20),
    sitio_exacto_accidente: str | None = Form(default=None),
    cant_heridos_en_sitio_accidente: int = Form(default=0, ge=0),
    cant_muertos_en_sitio_accidente: int = Form(default=0, ge=0),
    cantidad_accidentes: int = Form(default=1, ge=1),
    latitud: str | None = Form(default=None),
    longitud: str | None = Form(default=None),
):
    """Registra un accidente desde formulario HTML tolerando coordenadas vacias."""
    lat = _parse_float_opcional(latitud, "latitud")
    lng = _parse_float_opcional(longitud, "longitud")
    if lat is not None and not (-90.0 <= lat <= 90.0):
        raise HTTPException(status_code=422, detail="Latitud fuera de rango (-90 a 90)")
    if lng is not None and not (-180.0 <= lng <= 180.0):
        raise HTTPException(status_code=422, detail="Longitud fuera de rango (-180 a 180)")

    sitio = sitio_exacto_accidente.strip() if sitio_exacto_accidente else None
    accidente = repo.crear(
        {
            "fecha_accidente": fecha_accidente.strip(),
            "hora_accidente": hora_accidente.strip(),
            "gravedad_accidente": gravedad_accidente.strip(),
            "clase_accidente": clase_accidente.strip(),
            "a_o_accidente": a_o_accidente,
            "mes_accidente": _normalizar_texto(mes_accidente),
            "dia_accidente": _normalizar_texto(dia_accidente),
            "sitio_exacto_accidente": sitio or None,
            "cant_heridos_en_sitio_accidente": cant_heridos_en_sitio_accidente,
            "cant_muertos_en_sitio_accidente": cant_muertos_en_sitio_accidente,
            "cantidad_accidentes": cantidad_accidentes,
            "latitud": lat,
            "longitud": lng,
        }
    )
    invalidar_cache_clusters()
    return {"ok": True, "id": accidente.id}


@app.put("/api/accidentes/{accidente_id}")
def actualizar_accidente(
    accidente_id: int,
    payload: AccidenteUpdate,
    repo: RepoDep,
):
    """Actualiza campos validados de un accidente existente."""
    cambios = payload.model_dump(exclude_unset=True)
    if "mes_accidente" in cambios and cambios["mes_accidente"] is not None:
        cambios["mes_accidente"] = _normalizar_texto(cambios["mes_accidente"])
    if "dia_accidente" in cambios and cambios["dia_accidente"] is not None:
        cambios["dia_accidente"] = _normalizar_texto(cambios["dia_accidente"])
    if "sitio_exacto_accidente" in cambios and cambios["sitio_exacto_accidente"] is not None:
        cambios["sitio_exacto_accidente"] = cambios["sitio_exacto_accidente"].strip() or None

    accidente = repo.actualizar(accidente_id, cambios)
    if accidente is None:
        raise HTTPException(status_code=404, detail="Accidente no encontrado")
    invalidar_cache_clusters()
    return {"ok": True, "id": accidente.id}


@app.delete("/api/accidentes/{accidente_id}")
def eliminar_accidente(accidente_id: int, repo: RepoDep):
    """Elimina un accidente registrado por identificador."""
    eliminado = repo.eliminar(accidente_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Accidente no encontrado")
    invalidar_cache_clusters()
    return {"ok": True, "id": accidente_id}
