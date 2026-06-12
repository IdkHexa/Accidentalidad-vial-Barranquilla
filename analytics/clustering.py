"""Clustering geoespacial de accidentes con DBSCAN.

Este modulo implementa el analisis de zonas calientes de accidentalidad
vial en Barranquilla usando el algoritmo DBSCAN con metrica haversine.

Arquitectura:
    - ``ejecutar_clustering_dbscan()`` es una funcion pura: recibe
      datos, retorna datos.  No toca la base de datos ni tiene side
      effects.  Esto permite probarla con datos sinteticos.
    - ``obtener_clusters_pipeline()`` es el orquestador que conecta
      el repositorio de datos con la funcion de clustering.
    - ``obtener_clusters()`` es un wrapper legacy que mantiene la
      compatibilidad con ``mapa_clusters.py`` sin modificarlo.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from data.database import SessionLocal
from data.storage import AccidenteRepository

# Radio medio de la Tierra en kilometros, usado para convertir
# distancias a radianes en la metrica haversine de DBSCAN.
RADIO_TIERRA_KM: float = 6371.0

# Limites geograficos aproximados del area urbana de Barranquilla.
# Coordenadas fuera de este rectangulo se consideran basura geografica
# (Null Island, registros de otras ciudades, geocodificaciones erroneas).
_BBOX_LAT_MIN = 10.90
_BBOX_LAT_MAX = 11.05
_BBOX_LON_MIN = -74.90
_BBOX_LON_MAX = -74.75


def kilometros_a_radianes(km: float) -> float:
    """Convierte una distancia en kilometros a radianes en la esfera terrestre.

    DBSCAN con metrica haversine espera que el radio de vecindad (eps)
    este expresado en radianes.  Esta funcion hace explicita la
    conversion para que el llamador piense en metros/kilometros y no
    tenga que recordar la constante del radio terrestre.

    Parametros:
    - ``km``: distancia en kilometros (ej: 0.3 para 300 metros).

    Retorna la distancia expresada en radianes.
    """
    return km / RADIO_TIERRA_KM


def filtrar_por_bbox(df: pd.DataFrame) -> pd.Series:
    """Genera una mascara booleana para accidentes dentro del area de Barranquilla.

    El bounding box cubre la zona urbana y metropolitana de Barranquilla
    (desde el aeropuerto hasta el Gran Malecón).  Puntos fuera de este
    rectangulo —como coordenadas corruptas [0.0, 0.0] o registros de
    otras ciudades— seran excluidos del calculo de densidad para evitar
    que distorsionen los clusters.

    Parametros:
    - ``df``: DataFrame con columnas ``latitud`` y ``longitud``.

    Retorna una Serie booleana: ``True`` para registros dentro del
    bounding box, ``False`` para los que quedan fuera.
    """
    return (
        df["latitud"].between(_BBOX_LAT_MIN, _BBOX_LAT_MAX, inclusive="both")
        & df["longitud"].between(_BBOX_LON_MIN, _BBOX_LON_MAX, inclusive="both")
    )


def calcular_pesos(df: pd.DataFrame) -> np.ndarray:
    """Calcula el peso de cada accidente segun su severidad para DBSCAN.

    DBSCAN con ``sample_weight`` interpreta la densidad como la suma
    de pesos dentro del radio, no como el conteo de filas.  Esta
    funcion asigna un peso mayor a accidentes con victimas para que
    las zonas criticas se identifiquen por impacto real, no solo
    por frecuencia de ocurrencia.

    Formula::

        peso = cantidad_accidentes + 1.5 * heridos + 3.0 * muertos

    Con esta formula, ``min_samples`` se reinterpreta como
    "severidad acumulada equivalente a N accidentes sin victimas".
    Por ejemplo, ``min_samples=10`` podria alcanzarse con 2
    accidentes fatales (2 * 3.0 = 6) mas 3 con heridos
    (3 * 1.5 = 4.5), total = 10.5.

    Parametros:
    - ``df``: DataFrame con columnas ``cantidad_accidentes``,
      ``cant_heridos_en_sitio_accidente`` y
      ``cant_muertos_en_sitio_accidente``.

    Retorna un array numpy con un peso por fila.  Los valores nulos
    en las columnas de victimas se tratan como 0; los nulos en
    ``cantidad_accidentes`` se tratan como 1 (peso minimo).
    """
    return (
        df["cantidad_accidentes"].fillna(1.0)
        + df["cant_heridos_en_sitio_accidente"].fillna(0.0) * 1.5
        + df["cant_muertos_en_sitio_accidente"].fillna(0.0) * 3.0
    ).values


def ejecutar_clustering_dbscan(
    df: pd.DataFrame,
    radio_metros: float = 300.0,
    min_muestras: int = 10,
) -> pd.DataFrame:
    """Ejecuta DBSCAN ponderado sobre un DataFrame de accidentes.

    Esta es una **funcion pura**: recibe un DataFrame, retorna un
    DataFrame con la columna ``cluster`` agregada.  No toca la base
    de datos ni tiene side effects.  Esto permite probarla con datos
    sinteticos sin necesidad de una sesion de SQLAlchemy.

    Flujo interno:
        1. Filtra puntos fuera del bounding box de Barranquilla.
        2. Convierte coordenadas lat/lon a radianes (requerido por
           la metrica haversine).
        3. Calcula pesos de severidad para ``sample_weight``.
        4. Ejecuta DBSCAN con ``algorithm="ball_tree"`` y
           ``n_jobs=-1`` para optimizar el calculo.
        5. Reintegra los resultados al DataFrame original, marcando
           los puntos excluidos del bbox como ruido (``cluster=-1``).

    Parametros:
    - ``df``: DataFrame con columnas ``latitud``, ``longitud``,
      ``cantidad_accidentes``, ``cant_heridos_en_sitio_accidente``
      y ``cant_muertos_en_sitio_accidente``.
    - ``radio_metros``: radio de vecindad en metros para DBSCAN
      (default 300m).
    - ``min_muestras``: numero minimo de muestras (peso acumulado)
      para formar un cluster (default 10).

    Retorna un DataFrame identico al de entrada con una columna
    ``cluster`` agregada: entero >= 0 para clusters, -1 para ruido.
    """
    if df.empty:
        return df.copy()

    mascara_bbox = filtrar_por_bbox(df)
    df_filtrado = df[mascara_bbox].copy()

    if df_filtrado.empty:
        resultado = df.copy()
        resultado["cluster"] = -1
        return resultado

    coordenadas_rad = np.radians(df_filtrado[["latitud", "longitud"]].values)
    eps_radianes = kilometros_a_radianes(radio_metros / 1000.0)
    pesos = calcular_pesos(df_filtrado)

    dbscan = DBSCAN(
        eps=eps_radianes,
        min_samples=min_muestras,
        metric="haversine",
        algorithm="ball_tree",
        n_jobs=-1,
    )

    df_filtrado["cluster"] = dbscan.fit_predict(
        coordenadas_rad, sample_weight=pesos
    )

    resultado = df.copy()
    resultado["cluster"] = -1
    resultado.loc[mascara_bbox, "cluster"] = df_filtrado["cluster"].values

    return resultado


def obtener_clusters_pipeline(
    repo: AccidenteRepository,
    radio_metros: float = 300.0,
    min_muestras: int = 10,
    anio_desde: int | None = None,
    anio_hasta: int | None = None,
) -> pd.DataFrame:
    """Pipeline principal: extrae datos del repositorio y ejecuta el clustering.

    Este orquestador conecta la capa de persistencia (repositorio DAO)
    con la funcion pura de clustering.  Es la forma recomendada de
    invocar el analisis porque mantiene la separacion de responsabilidades:
    el repositorio sabe como acceder a los datos, la funcion de clustering
    sabe como analizarlos.

    Parametros:
    - ``repo``: instancia de ``AccidenteRepository`` con una sesion activa.
    - ``radio_metros``: radio de vecindad en metros (default 300m).
    - ``min_muestras``: peso acumulado minimo para formar cluster (default 10).
    - ``anio_desde``: año minimo a incluir, o ``None`` para todos.
    - ``anio_hasta``: año maximo a incluir, o ``None`` para todos.

    Retorna un DataFrame con columna ``cluster``.
    """
    df = repo.obtener_para_clustering(anio_desde=anio_desde, anio_hasta=anio_hasta)
    return ejecutar_clustering_dbscan(df, radio_metros=radio_metros, min_muestras=min_muestras)


def obtener_clusters(radio_metros: float = 300.0, min_muestras: int = 10) -> pd.DataFrame:
    """Wrapper legacy para mantener compatibilidad con ``mapa_clusters.py``.

    Crea internamente una sesion de base de datos y un repositorio,
    ejecuta el pipeline y cierra la sesion.  Esta funcion existe
    exclusivamente para no romper el modulo de visualizacion mientras
    Juan trabaja en el controller y el frontend.

    NOTA: Esta funcion toca ``SessionLocal`` directamente, lo cual
    viola la arquitectura del proyecto.  Deberia eliminarse cuando
    ``mapa_clusters.py`` se refactore para recibir el repositorio
    como parametro.
    """
    session = SessionLocal()
    try:
        repo = AccidenteRepository(session)
        return obtener_clusters_pipeline(repo, radio_metros=radio_metros, min_muestras=min_muestras)
    finally:
        session.close()


def main():
    """Punto de entrada para ejecucion directa desde la terminal.

    Ejecuta el pipeline completo y muestra un resumen basico de
    los clusters detectados.
    """
    df = obtener_clusters(radio_metros=300.0, min_muestras=10)

    n_clusters = len(set(df["cluster"])) - (1 if -1 in df["cluster"].values else 0)
    n_ruido = (df["cluster"] == -1).sum()
    n_total = len(df)

    print(f"Clusters detectados: {n_clusters}")
    print(f"Puntos de ruido (outliers): {n_ruido} ({n_ruido / n_total * 100:.1f}%)")
    print(f"En zonas calientes: {n_total - n_ruido} ({(n_total - n_ruido) / n_total * 100:.1f}%)")


if __name__ == "__main__":
    main()
