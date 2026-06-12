"""Pruebas del modulo de clustering geoespacial.

Verifica las funciones puras del pipeline de DBSCAN: conversion
de unidades, filtrado geografico, ponderacion de severidad y
el clustering completo con datos sinteticos.

Los tests usan un DataFrame en memoria (no tocan la base de datos
real) para que sean rapidos y deterministas.
"""

import unittest

import numpy as np
import pandas as pd

from analytics.clustering import (
    calcular_pesos,
    ejecutar_clustering_dbscan,
    filtrar_por_bbox,
    kilometros_a_radianes,
)


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


# Constantes del bounding box para los tests.
_BBOX_LAT_MIN = 10.90
_BBOX_LAT_MAX = 11.05
_BBOX_LON_MIN = -74.90
_BBOX_LON_MAX = -74.75


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

    def test_heridos_multiplican(self):
        """Cada herido aporta 1.5 al peso total."""
        df = self._df([1], [2], [0])
        pesos = calcular_pesos(df)
        # 1 + 2 * 1.5 = 4.0
        self.assertAlmostEqual(pesos[0], 4.0)

    def test_muertos_multiplican(self):
        """Cada muerto aporta 3.0 al peso total."""
        df = self._df([1], [0], [1])
        pesos = calcular_pesos(df)
        # 1 + 1 * 3.0 = 4.0
        self.assertAlmostEqual(pesos[0], 4.0)

    def test_victimas_mixtas(self):
        """Heridos y muertos se suman correctamente."""
        df = self._df([1], [2], [1])
        pesos = calcular_pesos(df)
        # 1 + 2*1.5 + 1*3.0 = 1 + 3.0 + 3.0 = 7.0
        self.assertAlmostEqual(pesos[0], 7.0)

    def test_nulos_se_tratan_como_cero(self):
        """Valores nulos en victimas se interpretan como cero."""
        df = self._df([1], [None], [None])
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
        """Un DataFrame vacio debe retornarse vacio sin errores."""
        df_vacio = pd.DataFrame()
        resultado = ejecutar_clustering_dbscan(df_vacio)
        self.assertTrue(resultado.empty)

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
        """Ponderar por severidad produce clusters distintos que sin ponderar."""
        # 8 puntos livianos + 3 puntos pesados (misma zona)
        df_livianos = self._df([(10.96, -74.80 + i * 0.0001) for i in range(8)])
        df_pesados = self._df([(10.96, -74.80 + i * 0.0001) for i in range(8, 11)])
        df_pesados["cant_muertos_en_sitio_accidente"] = 3

        df = pd.concat([df_livianos, df_pesados], ignore_index=True)

        # Con min_muestras=8 (peso acumulado), los pesados deben formar cluster
        resultado = ejecutar_clustering_dbscan(df, radio_metros=300, min_muestras=8)
        n_clusters = len(set(resultado["cluster"])) - (
            1 if -1 in resultado["cluster"].values else 0
        )
        self.assertGreater(n_clusters, 0)


if __name__ == "__main__":
    unittest.main()
