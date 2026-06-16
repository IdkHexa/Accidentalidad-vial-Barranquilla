"""Controlador principal — FastAPI endpoints REST para el dashboard de accidentalidad."""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, text
from collections import defaultdict
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.database import SessionLocal, AccidenteDB, init_db
from data.storage import AccidenteRepository

app = FastAPI(title="Accidentalidad Vial Barranquilla")

# ── static & templates ────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
ROOT = os.path.dirname(BASE)

app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "views", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT, "views", "templates"))

# ── helper ────────────────────────────────────────────────────────────────────
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _session():
    return SessionLocal()


# ── páginas HTML ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = _session()
    repo = AccidenteRepository(db)
    total = repo.contar()
    db.close()
    return templates.TemplateResponse(request, "dashboard.html", {"total": total})


@app.get("/mapa", response_class=HTMLResponse)
async def mapa(request: Request):
    return templates.TemplateResponse(request, "mapa.html")


@app.get("/registro", response_class=HTMLResponse)
async def registro(request: Request):
    return templates.TemplateResponse(request, "registro.html")


# ── API JSON ──────────────────────────────────────────────────────────────────

@app.get("/api/stats/resumen")
async def stats_resumen():
    """KPIs principales para las tarjetas del dashboard."""
    db = _session()
    try:
        total      = db.query(AccidenteDB).count()
        muertos    = db.query(func.sum(AccidenteDB.cant_muertos_en_sitio_accidente)).scalar() or 0
        heridos    = db.query(func.sum(AccidenteDB.cant_heridos_en_sitio_accidente)).scalar() or 0
        años_q     = db.query(AccidenteDB.a_o_accidente).distinct().all()
        años       = sorted([r[0] for r in años_q if r[0]])
        return {"total": total, "muertos": int(muertos), "heridos": int(heridos),
                "año_inicio": min(años) if años else None,
                "año_fin":   max(años) if años else None}
    finally:
        db.close()


@app.get("/api/stats/por_año")
async def stats_por_año():
    db = _session()
    try:
        rows = (db.query(AccidenteDB.a_o_accidente,
                         func.count(AccidenteDB.id).label("total"),
                         func.sum(AccidenteDB.cant_muertos_en_sitio_accidente).label("muertos"),
                         func.sum(AccidenteDB.cant_heridos_en_sitio_accidente).label("heridos"))
                .filter(AccidenteDB.a_o_accidente.isnot(None))
                .group_by(AccidenteDB.a_o_accidente)
                .order_by(AccidenteDB.a_o_accidente)
                .all())
        return [{"año": r.a_o_accidente, "total": r.total,
                 "muertos": int(r.muertos or 0), "heridos": int(r.heridos or 0)} for r in rows]
    finally:
        db.close()


@app.get("/api/stats/por_gravedad")
async def stats_por_gravedad():
    db = _session()
    try:
        rows = (db.query(AccidenteDB.gravedad_accidente, func.count(AccidenteDB.id).label("n"))
                .group_by(AccidenteDB.gravedad_accidente)
                .order_by(text("n DESC"))
                .all())
        return [{"gravedad": r.gravedad_accidente, "total": r.n} for r in rows]
    finally:
        db.close()


@app.get("/api/stats/por_clase")
async def stats_por_clase():
    db = _session()
    try:
        rows = (db.query(AccidenteDB.clase_accidente, func.count(AccidenteDB.id).label("n"))
                .group_by(AccidenteDB.clase_accidente)
                .order_by(text("n DESC"))
                .limit(10)
                .all())
        return [{"clase": r.clase_accidente, "total": r.n} for r in rows]
    finally:
        db.close()


@app.get("/api/stats/por_mes")
async def stats_por_mes():
    db = _session()
    try:
        ORDEN = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
                 "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
        rows = (db.query(AccidenteDB.mes_accidente, func.count(AccidenteDB.id).label("n"))
                .filter(AccidenteDB.mes_accidente.isnot(None))
                .group_by(AccidenteDB.mes_accidente)
                .all())
        data = {r.mes_accidente.upper(): r.n for r in rows}
        return [{"mes": m, "total": data.get(m, 0)} for m in ORDEN]
    finally:
        db.close()


@app.get("/api/stats/por_dia")
async def stats_por_dia():
    db = _session()
    try:
        ORDEN = ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES","SABADO","DOMINGO"]
        ABREV_A_FULL = {
            "LUN":"LUNES","MAR":"MARTES","MIE":"MIERCOLES","MIÉ":"MIERCOLES",
            "JUE":"JUEVES","VIE":"VIERNES","SAB":"SABADO","SÁB":"SABADO","DOM":"DOMINGO",
        }
        rows = (db.query(AccidenteDB.dia_accidente, func.count(AccidenteDB.id).label("n"))
                .filter(AccidenteDB.dia_accidente.isnot(None))
                .group_by(AccidenteDB.dia_accidente)
                .all())
        data = defaultdict(int)
        for r in rows:
            clave = r.dia_accidente.upper()
            clave = ABREV_A_FULL.get(clave, clave)
            data[clave] += r.n
        return [{"dia": d, "total": data.get(d, 0)} for d in ORDEN]
    finally:
        db.close()


@app.get("/api/stats/por_hora")
async def stats_por_hora():
    db = _session()
    try:
        rows = db.query(AccidenteDB.hora_accidente).filter(AccidenteDB.hora_accidente.isnot(None)).all()
        buckets = defaultdict(int)
        for (h,) in rows:
            try:
                texto = str(h).strip().lower()
                hora = int(texto.split(":")[0])
                if "pm" in texto and hora != 12:
                    hora += 12
                elif "am" in texto and hora == 12:
                    hora = 0
                if 0 <= hora <= 23:
                    buckets[hora] += 1
            except:
                pass
        return [{"hora": h, "total": buckets.get(h, 0)} for h in range(24)]
    finally:
        db.close()


@app.get("/api/mapa/puntos")
async def mapa_puntos(limit: int = 2000):
    db = _session()
    try:
        rows = (db.query(AccidenteDB.latitud, AccidenteDB.longitud,
                         AccidenteDB.gravedad_accidente, AccidenteDB.clase_accidente,
                         AccidenteDB.fecha_accidente, AccidenteDB.sitio_exacto_accidente)
                .filter(AccidenteDB.latitud.isnot(None), AccidenteDB.longitud.isnot(None))
                .limit(limit)
                .all())
        return [{"lat": r.latitud, "lng": r.longitud,
                 "gravedad": r.gravedad_accidente, "clase": r.clase_accidente,
                 "fecha": r.fecha_accidente, "sitio": r.sitio_exacto_accidente} for r in rows]
    finally:
        db.close()


@app.get("/api/accidentes")
async def listar_accidentes(limit: int = 50, gravedad: str = None, año: int = None):
    db = _session()
    try:
        q = db.query(AccidenteDB)
        if gravedad:
            q = q.filter(AccidenteDB.gravedad_accidente == gravedad)
        if año:
            q = q.filter(AccidenteDB.a_o_accidente == año)
        rows = q.order_by(AccidenteDB.id.desc()).limit(limit).all()
        return [{"id": r.id, "fecha": r.fecha_accidente, "hora": r.hora_accidente,
                 "gravedad": r.gravedad_accidente, "clase": r.clase_accidente,
                 "mes": r.mes_accidente, "dia": r.dia_accidente,
                 "sitio": r.sitio_exacto_accidente,
                 "heridos": r.cant_heridos_en_sitio_accidente,
                 "muertos": r.cant_muertos_en_sitio_accidente,
                 "lat": r.latitud, "lng": r.longitud} for r in rows]
    finally:
        db.close()


@app.post("/api/accidentes")
async def crear_accidente(
    fecha_accidente: str = Form(...),
    hora_accidente: str = Form(...),
    gravedad_accidente: str = Form(...),
    clase_accidente: str = Form(...),
    a_o_accidente: int = Form(...),
    mes_accidente: str = Form(...),
    dia_accidente: str = Form(...),
    sitio_exacto_accidente: str = Form(default=None),
    cant_heridos_en_sitio_accidente: int = Form(default=0),
    cant_muertos_en_sitio_accidente: int = Form(default=0),
    cantidad_accidentes: int = Form(default=1),
    latitud: float = Form(default=None),
    longitud: float = Form(default=None),
):
    db = _session()
    try:
        accidente = AccidenteDB(
            fecha_accidente=fecha_accidente,
            hora_accidente=hora_accidente,
            gravedad_accidente=gravedad_accidente,
            clase_accidente=clase_accidente,
            a_o_accidente=a_o_accidente,
            mes_accidente=mes_accidente,
            dia_accidente=dia_accidente,
            sitio_exacto_accidente=sitio_exacto_accidente,
            cant_heridos_en_sitio_accidente=cant_heridos_en_sitio_accidente,
            cant_muertos_en_sitio_accidente=cant_muertos_en_sitio_accidente,
            cantidad_accidentes=cantidad_accidentes,
            latitud=latitud,
            longitud=longitud,
        )
        db.add(accidente)
        db.commit()
        db.refresh(accidente)
        return {"ok": True, "id": accidente.id}
    finally:
        db.close()
