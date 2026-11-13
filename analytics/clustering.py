"""Clustering geoespacial de accidentes con DBSCAN.

Este modulo implementa el analisis de zonas calientes de accidentalidad
vial en Barranquilla usando el algoritmo DBSCAN con metrica haversine.

Arquitectura:
    - ``ejecutar_clustering_dbscan()`` es una funcion pura: recibe
      datos, retorna datos con columna ``cluster``. No toca la base de
      datos ni tiene side effects.
    - ``resumir_clusters()`` agrega centroides ponderados por severidad y
      descarta anomalias de 1 o 2 registros cuando se analiza la malla real.
    - ``obtener_clusters_pipeline()`` es el orquestador que conecta el
      repositorio DAO con la funcion de clustering.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from data.database import SessionLocal
from data.storage import AccidenteRepository

# Radio medio de la Tierra en kilometros para convertir distancias a radianes.
RADIO_TIERRA_KM: float = 6371.0

# Limites geograficos del area urbana de Barranquilla para descartar basura espacial.
_BBOX_LAT_MIN = 10.90
_BBOX_LAT_MAX = 11.05
_BBOX_LON_MIN = -74.90
_BBOX_LON_MAX = -74.75

# Hiperparametros calibrados empiricamente sobre ~28.8k registros en Barranquilla:
# eps=100m y min_samples=50 evitan el colapso por encadenamiento del 94.4% en un megacluster.
RADIO_DEFECTO_METROS: float = 100.0
MIN_MUESTRAS_DEFECTO: int = 50


def kilometros_a_radianes(km: float) -> float:
    """Convierte una distancia en kilometros a radianes en la esfera terrestre."""
    return km / RADIO_TIERRA_KM


def filtrar_por_bbox(df: pd.DataFrame) -> pd.Series:
    """Genera una mascara booleana para accidentes dentro del area de Barranquilla."""
    lat = pd.to_numeric(df["latitud"], errors="coerce")
    lon = pd.to_numeric(df["longitud"], errors="coerce")
    return (
        lat.between(_BBOX_LAT_MIN, _BBOX_LAT_MAX, inclusive="both")
        & lon.between(_BBOX_LON_MIN, _BBOX_LON_MAX, inclusive="both")
    )


def calcular_pesos(df: pd.DataFrame) -> np.ndarray:
    """Calcula el peso de cada accidente segun su severidad para DBSCAN.

    Formula::

        peso = max(1, cantidad_accidentes) + 1.5 * heridos + 3.0 * muertos

    Garantiza un peso minimo de 1.0 por registro fisico incluso si el campo
    ``cantidad_accidentes`` llego nulo o en cero.
    """
    accidentes = (
        pd.to_numeric(df["cantidad_accidentes"], errors="coerce")
        .fillna(1.0)
        .clip(lower=1.0)
    )
    heridos = (
        pd.to_numeric(df["cant_heridos_en_sitio_accidente"], errors="coerce")
        .fillna(0.0)
        .clip(lower=0.0)
    )
    muertos = (
        pd.to_numeric(df["cant_muertos_en_sitio_accidente"], errors="coerce")
        .fillna(0.0)
        .clip(lower=0.0)
    )
    return (accidentes + heridos * 1.5 + muertos * 3.0).to_numpy(dtype=float)


def ejecutar_clustering_dbscan(
    df: pd.DataFrame,
    radio_metros: float = RADIO_DEFECTO_METROS,
    min_muestras: int = MIN_MUESTRAS_DEFECTO,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Ejecuta DBSCAN ponderado sobre un DataFrame de accidentes.

    Siempre devuelve la columna ``cluster`` (con dtype ``int64``), incluso
    cuando el DataFrame de entrada viene vacio o ningun punto cae en el bbox.

    Parametros:
    - ``df``: DataFrame con coordenadas y columnas de severidad.
    - ``radio_metros``: radio de vecindad en metros (default 100 m).
    - ``min_muestras``: peso acumulado minimo para formar nucleo (default 50).
    - ``n_jobs``: hilos de ejecucion para ball_tree (default 1 para evitar
      contencion dentro de workers ASGI).
    """
    if df.empty:
        return df.assign(cluster=pd.Series(dtype="int64"))

    mascara_bbox = filtrar_por_bbox(df)
    df_filtrado = df[mascara_bbox].copy()

    if df_filtrado.empty:
        resultado = df.copy()
        resultado["cluster"] = -1
        return resultado

    coords = np.column_stack(
        [
            pd.to_numeric(df_filtrado["latitud"], errors="coerce").to_numpy(dtype=float),
            pd.to_numeric(df_filtrado["longitud"], errors="coerce").to_numpy(dtype=float),
        ]
    )
    coordenadas_rad = np.radians(coords)
    eps_radianes = kilometros_a_radianes(radio_metros / 1000.0)
    pesos = calcular_pesos(df_filtrado)

    dbscan = DBSCAN(
        eps=eps_radianes,
        min_samples=min_muestras,
        metric="haversine",
        algorithm="ball_tree",
        n_jobs=n_jobs,
    )

    etiquetas = dbscan.fit_predict(coordenadas_rad, sample_weight=pesos)

    resultado = df.copy()
    resultado["cluster"] = -1
    resultado.loc[mascara_bbox, "cluster"] = etiquetas
    resultado["cluster"] = resultado["cluster"].astype("int64")

    return resultado


def resumir_clusters(df: pd.DataFrame, min_puntos_cluster: int = 3) -> dict:
    """Agrupa las zonas detectadas en un resumen JSON con centroides ponderados.

    Descarta falsos clusters de 1 o 2 registros aislados cuyo peso por victimas
    supero ``min_muestras`` en solitario y separa puntos fuera del bbox.
    """
    if df.empty or "cluster" not in df.columns:
        return {
            "clusters": [],
            "total_puntos_en_clusters": 0,
            "total_ruido": 0,
            "total_fuera_bbox": 0,
        }

    fuera_bbox = int((~filtrar_por_bbox(df)).sum()) if len(df) > 0 else 0
    clusters_df = df[df["cluster"] >= 0].copy()
    resumen = []
    puntos_validos = 0

    for cid, grupo in clusters_df.groupby("cluster"):
        n_puntos = int(len(grupo))
        if n_puntos < min_puntos_cluster:
            continue

        pesos = calcular_pesos(grupo)
        peso_total = float(pesos.sum())
        lat_centro = float(np.average(grupo["latitud"].astype(float), weights=pesos))
        lng_centro = float(np.average(grupo["longitud"].astype(float), weights=pesos))
        muertos = int(pd.to_numeric(grupo["cant_muertos_en_sitio_accidente"], errors="coerce").fillna(0).sum())
        heridos = int(pd.to_numeric(grupo["cant_heridos_en_sitio_accidente"], errors="coerce").fillna(0).sum())

        if muertos >= 3 or peso_total >= 400:
            nivel = "critico"
        elif peso_total >= 150:
            nivel = "alto"
        else:
            nivel = "moderado"

        puntos_validos += n_puntos
        resumen.append(
            {
                "cluster": int(cid),
                "puntos": n_puntos,
                "lat_centro": round(lat_centro, 6),
                "lng_centro": round(lng_centro, 6),
                "muertos": muertos,
                "heridos": heridos,
                "peso_total": round(peso_total, 1),
                "nivel": nivel,
            }
        )

    resumen.sort(key=lambda c: (c["peso_total"], c["puntos"]), reverse=True)
    total_ruido = int(len(df)) - puntos_validos

    return {
        "clusters": resumen,
        "total_puntos_en_clusters": puntos_validos,
        "total_ruido": total_ruido,
        "total_fuera_bbox": fuera_bbox,
    }


def obtener_clusters_pipeline(
    repo: AccidenteRepository,
    radio_metros: float = RADIO_DEFECTO_METROS,
    min_muestras: int = MIN_MUESTRAS_DEFECTO,
    anio_desde: int | None = None,
    anio_hasta: int | None = None,
) -> pd.DataFrame:
    """Pipeline principal: extrae datos del repositorio y ejecuta el clustering."""
    df = repo.obtener_para_clustering(anio_desde=anio_desde, anio_hasta=anio_hasta)
    return ejecutar_clustering_dbscan(
        df, radio_metros=radio_metros, min_muestras=min_muestras, n_jobs=1
    )


def obtener_clusters(
    radio_metros: float = RADIO_DEFECTO_METROS,
    min_muestras: int = MIN_MUESTRAS_DEFECTO,
) -> pd.DataFrame:
    """Wrapper CLI que abre y cierra una sesion de base de datos."""
    session = SessionLocal()
    try:
        repo = AccidenteRepository(session)
        return obtener_clusters_pipeline(
            repo, radio_metros=radio_metros, min_muestras=min_muestras
        )
    finally:
        session.close()


def main():
    """Punto de entrada para ejecucion directa desde la terminal."""
    df = obtener_clusters()
    resumen = resumir_clusters(df)
    n_total = len(df)
    n_ruido = resumen["total_ruido"]

    print(f"Clusters detectados: {len(resumen['clusters'])}")
    if n_total > 0:
        print(f"Puntos de ruido (outliers): {n_ruido} ({n_ruido / n_total * 100:.1f}%)")
        en_clusters = resumen["total_puntos_en_clusters"]
        print(f"En zonas calientes: {en_clusters} ({en_clusters / n_total * 100:.1f}%)")
    else:
        print("Sin registros georreferenciados para agrupar.")


if __name__ == "__main__":
    main()
