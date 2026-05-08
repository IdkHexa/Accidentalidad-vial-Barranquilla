"""Pruebas del modulo de geocodificacion.

Verifican la construccion de la consulta y el uso del cache local.
"""

import unittest
from data.geocoding import GeoCoder
from data.direccion_parser import parsear_texto
import os


class TestGeoCoding(unittest.TestCase):
    """Agrupa pruebas del geocodificador."""

    def setUp(self):
        """
        Crea un archivo de cache temporal para las pruebas.

        `self.cache_test` guarda la ruta del archivo usado solo en este entorno.
        """
        self.cache_test = "tests/test_geocache.json"
        self.geocoder = GeoCoder(cache_file=self.cache_test)

    def tearDown(self):
        """Elimina el archivo temporal usado en las pruebas."""
        if os.path.exists(self.cache_test):
            os.remove(self.cache_test)

    def test_formato_query(self):
        """Comprueba la cadena final enviada a la geocodificacion."""
        direccion = parsear_texto("CL 72 46 10")
        query = str(direccion)
        self.assertEqual(query, "Calle 72 46 - 10, Barranquilla, Colombia")

    def test_cache_logic(self):
        """Comprueba que una direccion repetida pueda resolverse desde el cache."""
        direccion = parsear_texto("Calle Falsa 123")
        self.geocoder.cache[str(direccion)] = (10.123, -74.456)

        coords = self.geocoder.obtener_coordenadas(direccion)
        self.assertEqual(coords, (10.123, -74.456))


if __name__ == "__main__":
    unittest.main()
