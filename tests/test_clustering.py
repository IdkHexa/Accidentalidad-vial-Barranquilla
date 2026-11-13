"""Pruebas del modulo de clustering geoespacial.

Verifica las funciones puras del pipeline de DBSCAN: conversion
de unidades, filtrado geografico, ponderacion de severidad, resumen
de hotspots y el pipeline completo conectado al repositorio DAO.
"""

import unittest

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from analytics.clustering import (
    calcular_pesos,
    ejecutar_clustering_dbscan,
    filtrar_por_bbox,
    kilometros_a_radianes,
    obtener_clusters_pipeline,
    resumir_clusters,
)
from data.database import Base
from data.storage import AccidenteRepository
from models.entidades import AccidenteDTO


class TestKilometrosARadianes(unittest.TestCase):
    """Verifica la conversion de kilometros a radianes para haversine."""

    def test_300_metros_produce_eps_correcto(self):
        """300 metros (0.3 km) debe dividirse por el radio de la Tierra."""
        resultado = kilometros_a_radianes(0.3)
        esperado = 0.3 / 6371.0
        self.assertAlmostEqual(resultado, esperado, places=10)

    def test_cero_km_da_cero_radianes(self):
        """Una distancia de cero debe producir cero radianes."""
        self.assertEqual(kilometros_a_radianes(0.0), 0.0)

    def test_un_km(self):
        """Un kilometro debe dividirse exactamente por el radio terrestre."""
        self.assertAlmostEqual(kilometros_a_radianes(1.0), 1.0 / 6371.0)


# Constantes del bounding box para los tests.
_BBOX_LAT_MIN = 10.90
_BBOX_LAT_MAX = 11.05
_BBOX_LON_MIN = -74.90
_BBOX_LON_MAX = -74.75


class TestFiltrarPorBbox(unittest.TestCase):
    """Verifica el filtrado geografico por bounding box de Barranquilla."""

    def _df(self, puntos):
        """Crea un DataFrame a partir de una lista de (lat, lon)."""
        return pd.DataFrame(puntos, columns=["latitud", "longitud"])

    def test_punto_dentro_del_bbox(self):
        """Un punto en el centro de Barranquilla debe pasar el filtro."""
        df = self._df([(10.96, -74.80)])
        resultado = filtrar_por_bbox(df)
        self.assertTrue(resultado.iloc[0])

    def test_punto_null_island(self):
        """Coordenadas [0.0, 0.0] deben ser excluidas."""
        df = self._df([(0.0, 0.0)])
        resultado = filtrar_por_bbox(df)
        self.assertFalse(resultado.iloc[0])

    def test_punto_fuera_al_norte(self):
        """Un punto muy al norte (ej: Bogota) debe ser excluido."""
        df = self._df([(4.60, -74.08)])
        resultado = filtrar_por_bbox(df)
        self.assertFalse(resultado.iloc[0])

    def test_punto_en_limite(self):
        """Un punto exactamente en el borde del bbox debe ser incluido."""
        df = self._df([(_BBOX_LAT_MIN, _BBOX_LON_MIN)])
        resultado = filtrar_por_bbox(df)
        self.assertTrue(resultado.iloc[0])

    def test_mezcla_dentro_fuera(self):
        """Mezcla de puntos validos e invalidos filtra correctamente."""
        df = self._df([
            (10.96, -74.80),   # dentro
            (0.0, 0.0),        # fuera
            (10.98, -74.82),   # dentro
            (4.60, -74.08),    # fuera
        ])
        resultado = filtrar_por_bbox(df)
        self.assertEqual(resultado.sum(), 2)


class TestCalcularPesos(unittest.TestCase):
    """Verifica la ponderacion de severidad para sample_weight."""

    def _df(self, accidentes, heridos, muertos):
        """Crea un DataFrame con los datos de severidad."""
        return pd.DataFrame({
            "cantidad_accidentes": accidentes,
            "cant_heridos_en_sitio_accidente": heridos,
            "cant_muertos_en_sitio_accidente": muertos,
        })

    def test_sin_victimas_peso_base(self):
        """Un accidente sin victimas debe tener peso base = 1."""
        df = self._df([1], [0], [0])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 1.0)

    def test_cantidad_cero_usa_piso_uno(self):
        """Si ``cantidad_accidentes`` viene en 0, conserva peso base minimo de 1.0."""
        df = self._df([0], [0], [0])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 1.0)

    def test_heridos_multiplican(self):
        """Cada herido aporta 1.5 al peso total."""
        df = self._df([1], [2], [0])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 4.0)

    def test_muertos_multiplican(self):
        """Cada muerto aporta 3.0 al peso total."""
        df = self._df([1], [0], [1])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 4.0)

    def test_victimas_mixtas(self):
        """Heridos y muertos se suman correctamente."""
        df = self._df([1], [2], [1])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 7.0)

    def test_nulos_se_tratan_como_cero(self):
        """Valores nulos en victimas se interpretan como cero."""
        df = self._df([None], [None], [None])
        pesos = calcular_pesos(df)
        self.assertAlmostEqual(pesos[0], 1.0)


class TestEjecutarClusteringDbscan(unittest.TestCase):
    """Verifica la funcion pura de clustering con datos sinteticos."""

    def _df(self, puntos):
        """Crea un DataFrame con coordenadas y columnas de severidad."""
        return pd.DataFrame({
            "latitud": [p[0] for p in puntos],
            "longitud": [p[1] for p in puntos],
            "cantidad_accidentes": [1] * len(puntos),
            "cant_heridos_en_sitio_accidente": [0] * len(puntos),
            "cant_muertos_en_sitio_accidente": [0] * len(puntos),
            "gravedad_accidente": ["Leve"] * len(puntos),
        })

    def test_dataframe_vacio(self):
        """Un DataFrame vacio debe retornarse vacio pero con columna ``cluster``."""
        df_vacio = pd.DataFrame()
        resultado = ejecutar_clustering_dbscan(df_vacio)
        self.assertTrue(resultado.empty)
        self.assertIn("cluster", resultado.columns)

    def test_todos_fuera_del_bbox(self):
        """Si todos los puntos estan fuera, todos quedan como ruido (-1)."""
        df = self._df([(0.0, 0.0), (4.60, -74.08)])
        resultado = ejecutar_clustering_dbscan(df)
        self.assertTrue((resultado["cluster"] == -1).all())

    def test_punto_null_island_es_ruido(self):
        """El punto [0.0, 0.0] debe quedar como ruido, no contaminar clusters."""
        df = self._df([
            (10.96, -74.80),
            (10.9601, -74.8001),
            (0.0, 0.0),
        ])
        resultado = ejecutar_clustering_dbscan(df, radio_metros=300, min_muestras=2)
        null_island = resultado.iloc[2]
        self.assertEqual(null_island["cluster"], -1)

    def test_todos_mismas_coordenadas(self):
        """Puntos en la misma ubicacion deben formar un cluster."""
        puntos = [(10.96, -74.80)] * 5
        df = self._df(puntos)
        resultado = ejecutar_clustering_dbscan(df, radio_metros=100, min_muestras=3)
        clusters = resultado["cluster"].unique()
        self.assertEqual(len(clusters), 1)
        self.assertNotEqual(clusters[0], -1)

    def test_ponderacion_cambia_clusters(self):
        """Con menos puntos que ``min_muestras``, solo la mayor severidad forma cluster."""
        # 3 puntos sin victimas (peso total = 3 < min_muestras=8) -> todo es ruido (-1)
        df_livianos = self._df([(10.96, -74.80 + i * 0.0001) for i in range(3)])
        res_livianos = ejecutar_clustering_dbscan(df_livianos, radio_metros=100, min_muestras=8)
        self.assertTrue((res_livianos["cluster"] == -1).all())

        # Mismos 3 puntos con victimas fatales (peso total = 30 >= min_muestras=8) -> 1 cluster
        df_pesados = df_livianos.copy()
        df_pesados["cant_muertos_en_sitio_accidente"] = 3
        res_pesados = ejecutar_clustering_dbscan(df_pesados, radio_metros=100, min_muestras=8)
        n_clusters = len(set(res_pesados["cluster"])) - (
            1 if -1 in res_pesados["cluster"].values else 0
        )
        self.assertEqual(n_clusters, 1)

    def test_resumir_clusters_filtra_singleton_y_calcula_centroide(self):
        """``resumir_clusters`` descarta falsos clusters de 1 punto y calcula metricas."""
        df = self._df([(10.98, -74.80)] * 4 + [(10.92, -74.88), (0.0, 0.0)])
        df.loc[4, "cant_muertos_en_sitio_accidente"] = 5
        clustered = ejecutar_clustering_dbscan(df, radio_metros=100, min_muestras=4)
        resumen = resumir_clusters(clustered, min_puntos_cluster=3)
        self.assertEqual(len(resumen["clusters"]), 1)
        self.assertEqual(resumen["clusters"][0]["puntos"], 4)
        self.assertEqual(resumen["total_fuera_bbox"], 1)

    def test_obtener_clusters_pipeline_desde_repositorio(self):
        """Verifica la integracion end-to-end del pipeline con SQLite en memoria."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            repo = AccidenteRepository(session)
            dtos = [
                AccidenteDTO(
                    fecha_accidente="2026-01-01",
                    hora_accidente="10:00",
                    gravedad_accidente="Con heridos",
                    clase_accidente="Choque",
                    a_o_accidente=2026,
                    mes_accidente="ENERO",
                    dia_accidente="JUEVES",
                    latitud=10.985,
                    longitud=-74.805,
                )
                for _ in range(5)
            ]
            repo.insertar_lote(dtos)
            resultado = obtener_clusters_pipeline(repo, radio_metros=100, min_muestras=3)
            self.assertEqual(len(resultado), 5)
            self.assertTrue((resultado["cluster"] >= 0).all())
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
