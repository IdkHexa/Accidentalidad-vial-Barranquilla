"""Repositorio DAO para operaciones de almacenamiento persistente y analitica SQL.

Implementa el patron Repositorio (Data Access Object) centralizando todas las
consultas, agregaciones estadisticas, filtros geoespaciales y operaciones CRUD
sobre la entidad ``AccidenteDB``. Ningun controlador ni modulo analitico debe
importar ``SessionLocal`` ni ``AccidenteDB`` directamente.
"""

from collections import Counter, defaultdict

import pandas as pd
from sqlalchemy import func

from data.database import AccidenteDB

_ORDEN_MESES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]

_ORDEN_DIAS = [
    "LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO",
]

_ABREV_DIA_A_FULL = {
    "LUN": "LUNES",
    "MAR": "MARTES",
    "MIE": "MIERCOLES",
    "MIÉ": "MIERCOLES",
    "MIÉRCOLES": "MIERCOLES",
    "JUE": "JUEVES",
    "VIE": "VIERNES",
    "SAB": "SABADO",
    "SÁB": "SABADO",
    "SÁBADO": "SABADO",
    "DOM": "DOMINGO",
}


class AccidenteRepository:
    """Repositorio DAO para la entidad ``AccidenteDB``.

    Recibe una sesion de SQLAlchemy en el constructor para mantener el ciclo
    transaccional desacoplado e inyectable desde FastAPI o scripts ETL.
    """

    def __init__(self, session):
        """Guarda la sesion activa con la que trabajara el repositorio."""
        self.session = session

    def insertar_lote(self, accidentes_dto) -> int:
        """Inserta una lista completa de accidentes en una sola transaccion."""
        try:
            objetos_db = [AccidenteDB.desde_dto(dto) for dto in accidentes_dto]
            self.session.add_all(objetos_db)
            self.session.commit()
            return len(objetos_db)
        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _clave_natural(registro: AccidenteDB | tuple) -> tuple:
        """Construye una clave natural reproducible para detectar duplicados en el ETL."""
        if isinstance(registro, tuple):
            fecha, hora, gravedad, clase, sitio, heridos, muertos = registro
        else:
            fecha = registro.fecha_accidente
            hora = registro.hora_accidente
            gravedad = registro.gravedad_accidente
            clase = registro.clase_accidente
            sitio = registro.sitio_exacto_accidente
            heridos = registro.cant_heridos_en_sitio_accidente
            muertos = registro.cant_muertos_en_sitio_accidente
        return (
            (fecha or "").strip(),
            (hora or "").strip(),
            (gravedad or "").strip(),
            (clase or "").strip(),
            (sitio or "").strip().lower(),
            int(heridos or 0),
            int(muertos or 0),
        )

    def sincronizar_lote(self, accidentes_dto) -> int:
        """Inserta unicamente los accidentes que aun no existen en la base de datos.

        Compara por multiconjunto de claves naturales contra los registros ya
        persistidos para garantizar idempotencia al re-ejecutar el pipeline ETL
        sin descartar siniestros legitimos con metadatos repetidos en la fuente.
        """
        if not accidentes_dto:
            return 0

        filas_existentes = self.session.query(
            AccidenteDB.fecha_accidente,
            AccidenteDB.hora_accidente,
            AccidenteDB.gravedad_accidente,
            AccidenteDB.clase_accidente,
            AccidenteDB.sitio_exacto_accidente,
            AccidenteDB.cant_heridos_en_sitio_accidente,
            AccidenteDB.cant_muertos_en_sitio_accidente,
        ).all()

        conteo_existente = Counter(self._clave_natural(fila) for fila in filas_existentes)
        nuevos_db: list[AccidenteDB] = []

        for dto in accidentes_dto:
            obj = AccidenteDB.desde_dto(dto)
            clave = self._clave_natural(obj)
            if conteo_existente[clave] > 0:
                conteo_existente[clave] -= 1
                continue
            nuevos_db.append(obj)

        if not nuevos_db:
            return 0

        try:
            self.session.add_all(nuevos_db)
            self.session.commit()
            return len(nuevos_db)
        except Exception:
            self.session.rollback()
            raise

    def contar(self) -> int:
        """Cuenta cuantos registros hay almacenados en total."""
        return self.session.query(func.count(AccidenteDB.id)).scalar() or 0

    def obtener_todos(self, limit: int = 100):
        """Obtiene los registros mas recientes, ordenados por ID descendente."""
        return (
            self.session.query(AccidenteDB)
            .order_by(AccidenteDB.id.desc())
            .limit(limit)
            .all()
        )

    def obtener_por_gravedad(self, gravedad: str):
        """Busca accidentes que coincidan con una gravedad especifica."""
        return (
            self.session.query(AccidenteDB)
            .filter(AccidenteDB.gravedad_accidente == gravedad)
            .all()
        )

    def obtener_por_año(self, año: int):
        """Filtra los accidentes ocurridos en un año determinado."""
        return (
            self.session.query(AccidenteDB)
            .filter(AccidenteDB.a_o_accidente == año)
            .all()
        )

    # ── Estadisticas y agregaciones para el controlador ───────────────────────

    def obtener_resumen(self) -> dict:
        """Retorna KPIs agregados en una sola consulta SQL."""
        fila = self.session.query(
            func.count(AccidenteDB.id),
            func.coalesce(func.sum(AccidenteDB.cant_muertos_en_sitio_accidente), 0),
            func.coalesce(func.sum(AccidenteDB.cant_heridos_en_sitio_accidente), 0),
            func.min(AccidenteDB.a_o_accidente),
            func.max(AccidenteDB.a_o_accidente),
            func.count(func.distinct(AccidenteDB.a_o_accidente)),
        ).one()

        total = int(fila[0] or 0)
        muertos = int(fila[1] or 0)
        heridos = int(fila[2] or 0)
        año_inicio = int(fila[3]) if fila[3] is not None else None
        año_fin = int(fila[4]) if fila[4] is not None else None
        n_años = int(fila[5] or 0)

        tasa_letalidad = round((muertos / total) * 100, 2) if total > 0 else 0.0
        promedio_anual = round(total / n_años) if n_años > 0 else 0

        return {
            "total": total,
            "muertos": muertos,
            "heridos": heridos,
            "año_inicio": año_inicio,
            "año_fin": año_fin,
            "tasa_letalidad": tasa_letalidad,
            "promedio_anual": promedio_anual,
        }

    def obtener_años_disponibles(self) -> list[int]:
        """Retorna la lista de años distintos ordenados de mayor a menor."""
        filas = (
            self.session.query(AccidenteDB.a_o_accidente)
            .filter(AccidenteDB.a_o_accidente.isnot(None))
            .distinct()
            .order_by(AccidenteDB.a_o_accidente.desc())
            .all()
        )
        return [int(f[0]) for f in filas if f[0] is not None]

    def contar_por_año(self) -> list[dict]:
        """Agrupa accidentes, muertos y heridos por año en orden cronologico."""
        filas = (
            self.session.query(
                AccidenteDB.a_o_accidente.label("año"),
                func.count(AccidenteDB.id).label("total"),
                func.coalesce(func.sum(AccidenteDB.cant_muertos_en_sitio_accidente), 0).label("muertos"),
                func.coalesce(func.sum(AccidenteDB.cant_heridos_en_sitio_accidente), 0).label("heridos"),
            )
            .filter(AccidenteDB.a_o_accidente.isnot(None))
            .group_by(AccidenteDB.a_o_accidente)
            .order_by(AccidenteDB.a_o_accidente)
            .all()
        )
        return [
            {
                "año": int(r.año),
                "total": int(r.total),
                "muertos": int(r.muertos or 0),
                "heridos": int(r.heridos or 0),
            }
            for r in filas
        ]

    def contar_por_gravedad(self) -> list[dict]:
        """Cuenta accidentes agrupados por nivel de gravedad."""
        total_expr = func.count(AccidenteDB.id)
        filas = (
            self.session.query(
                AccidenteDB.gravedad_accidente.label("gravedad"),
                total_expr.label("total"),
            )
            .group_by(AccidenteDB.gravedad_accidente)
            .order_by(total_expr.desc())
            .all()
        )
        return [{"gravedad": r.gravedad, "total": int(r.total)} for r in filas]

    def contar_por_clase(self, limit: int = 10) -> list[dict]:
        """Cuenta las ``limit`` clases de accidente mas frecuentes."""
        total_expr = func.count(AccidenteDB.id)
        filas = (
            self.session.query(
                AccidenteDB.clase_accidente.label("clase"),
                total_expr.label("total"),
            )
            .group_by(AccidenteDB.clase_accidente)
            .order_by(total_expr.desc())
            .limit(limit)
            .all()
        )
        return [{"clase": r.clase, "total": int(r.total)} for r in filas]

    def contar_por_mes(self) -> list[dict]:
        """Cuenta accidentes por mes respetando el orden calendario enero-diciembre."""
        filas = (
            self.session.query(
                AccidenteDB.mes_accidente,
                func.count(AccidenteDB.id),
            )
            .filter(AccidenteDB.mes_accidente.isnot(None))
            .group_by(AccidenteDB.mes_accidente)
            .all()
        )
        conteo = {(mes or "").strip().upper(): int(total) for mes, total in filas}
        return [{"mes": mes, "total": conteo.get(mes, 0)} for mes in _ORDEN_MESES]

    def contar_por_dia(self) -> list[dict]:
        """Cuenta accidentes por dia de la semana normalizando abreviaturas."""
        filas = (
            self.session.query(
                AccidenteDB.dia_accidente,
                func.count(AccidenteDB.id),
            )
            .filter(AccidenteDB.dia_accidente.isnot(None))
            .group_by(AccidenteDB.dia_accidente)
            .all()
        )
        acumulado: dict[str, int] = defaultdict(int)
        for dia, total in filas:
            clave = (dia or "").strip().upper()
            clave = _ABREV_DIA_A_FULL.get(clave, clave)
            acumulado[clave] += int(total)
        return [{"dia": dia, "total": acumulado.get(dia, 0)} for dia in _ORDEN_DIAS]

    def contar_por_hora(self) -> list[dict]:
        """Agrupa horarios distintos en SQL y acumula por franja horaria (0-23h)."""
        filas = (
            self.session.query(
                AccidenteDB.hora_accidente,
                func.count(AccidenteDB.id),
            )
            .filter(AccidenteDB.hora_accidente.isnot(None))
            .group_by(AccidenteDB.hora_accidente)
            .all()
        )
        buckets: dict[int, int] = defaultdict(int)
        for hora_raw, cantidad in filas:
            texto = str(hora_raw).strip().lower()
            try:
                hora = int(texto.split(":")[0])
            except (ValueError, IndexError):
                continue
            if "pm" in texto and hora != 12:
                hora += 12
            elif "am" in texto and hora == 12:
                hora = 0
            if 0 <= hora <= 23:
                buckets[hora] += int(cantidad)
        return [{"hora": h, "total": buckets.get(h, 0)} for h in range(24)]

    # ── Consultas geoespaciales, listado paginado y CRUD ─────────────────────

    def obtener_puntos_mapa(
        self,
        limit: int = 3000,
        gravedad: str | None = None,
        año: int | None = None,
    ) -> list[dict]:
        """Retorna puntos georreferenciados filtrables por gravedad y año."""
        query = self.session.query(
            AccidenteDB.latitud,
            AccidenteDB.longitud,
            AccidenteDB.gravedad_accidente,
            AccidenteDB.clase_accidente,
            AccidenteDB.fecha_accidente,
            AccidenteDB.sitio_exacto_accidente,
            AccidenteDB.a_o_accidente,
        ).filter(
            AccidenteDB.latitud.isnot(None),
            AccidenteDB.longitud.isnot(None),
        )
        if gravedad:
            query = query.filter(AccidenteDB.gravedad_accidente == gravedad)
        if año is not None:
            query = query.filter(AccidenteDB.a_o_accidente == año)

        filas = query.order_by(AccidenteDB.id.desc()).limit(limit).all()
        return [
            {
                "lat": r.latitud,
                "lng": r.longitud,
                "gravedad": r.gravedad_accidente,
                "clase": r.clase_accidente,
                "fecha": r.fecha_accidente,
                "sitio": r.sitio_exacto_accidente,
                "año": r.a_o_accidente,
            }
            for r in filas
        ]

    def listar_filtrados(
        self,
        limit: int = 50,
        offset: int = 0,
        gravedad: str | None = None,
        año: int | None = None,
    ) -> list[dict]:
        """Lista accidentes paginados ordenados del registro mas reciente al mas antiguo."""
        query = self.session.query(AccidenteDB)
        if gravedad:
            query = query.filter(AccidenteDB.gravedad_accidente == gravedad)
        if año is not None:
            query = query.filter(AccidenteDB.a_o_accidente == año)

        filas = (
            query.order_by(AccidenteDB.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "fecha": r.fecha_accidente,
                "hora": r.hora_accidente,
                "gravedad": r.gravedad_accidente,
                "clase": r.clase_accidente,
                "año": r.a_o_accidente,
                "mes": r.mes_accidente,
                "dia": r.dia_accidente,
                "sitio": r.sitio_exacto_accidente,
                "heridos": r.cant_heridos_en_sitio_accidente,
                "muertos": r.cant_muertos_en_sitio_accidente,
                "lat": r.latitud,
                "lng": r.longitud,
            }
            for r in filas
        ]

    def obtener_por_id(self, accidente_id: int) -> AccidenteDB | None:
        """Busca un registro individual por su identificador primario."""
        return (
            self.session.query(AccidenteDB)
            .filter(AccidenteDB.id == accidente_id)
            .first()
        )

    def crear(self, datos: dict) -> AccidenteDB:
        """Persiste un nuevo accidente con rollback automatico ante errores."""
        try:
            accidente = AccidenteDB(**datos)
            self.session.add(accidente)
            self.session.commit()
            self.session.refresh(accidente)
            return accidente
        except Exception:
            self.session.rollback()
            raise

    def actualizar(self, accidente_id: int, datos: dict) -> AccidenteDB | None:
        """Actualiza campos permitidos de un accidente existente."""
        accidente = self.obtener_por_id(accidente_id)
        if accidente is None:
            return None
        try:
            for clave, valor in datos.items():
                setattr(accidente, clave, valor)
            self.session.commit()
            self.session.refresh(accidente)
            return accidente
        except Exception:
            self.session.rollback()
            raise

    def eliminar(self, accidente_id: int) -> bool:
        """Elimina un accidente por ID; retorna ``False`` si no existe."""
        accidente = self.obtener_por_id(accidente_id)
        if accidente is None:
            return False
        try:
            self.session.delete(accidente)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    # ── Proyeccion para clustering ────────────────────────────────────────────

    def obtener_para_clustering(
        self,
        anio_desde: int | None = None,
        anio_hasta: int | None = None,
    ) -> pd.DataFrame:
        """Extrae solo las columnas necesarias para DBSCAN filtrando nulos desde SQL."""
        query = self.session.query(
            AccidenteDB.latitud,
            AccidenteDB.longitud,
            AccidenteDB.a_o_accidente,
            AccidenteDB.cantidad_accidentes,
            AccidenteDB.cant_heridos_en_sitio_accidente,
            AccidenteDB.cant_muertos_en_sitio_accidente,
            AccidenteDB.gravedad_accidente,
        ).filter(
            AccidenteDB.latitud.isnot(None),
            AccidenteDB.longitud.isnot(None),
        )
        if anio_desde is not None:
            query = query.filter(AccidenteDB.a_o_accidente >= anio_desde)
        if anio_hasta is not None:
            query = query.filter(AccidenteDB.a_o_accidente <= anio_hasta)

        rows = query.all()

        return pd.DataFrame(
            rows,
            columns=[
                "latitud",
                "longitud",
                "año",
                "cantidad_accidentes",
                "cant_heridos_en_sitio_accidente",
                "cant_muertos_en_sitio_accidente",
                "gravedad_accidente",
            ],
        )
