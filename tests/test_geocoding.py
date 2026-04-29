import unittest
from data.geocoding import GeoCoder
from data.direccion_parser import parsear_texto
import os

class TestGeoCoding(unittest.TestCase):
    
    def setUp(self):
        # Usamos un archivo de caché separado para pruebas para no ensuciar el real
        self.cache_test = "tests/test_geocache.json"
        self.geocoder = GeoCoder(cache_file=self.cache_test)

    def tearDown(self):
        # Opcional: Borrar el caché de prueba después de correr los tests
        if os.path.exists(self.cache_test):
            os.remove(self.cache_test)

    def test_formato_query(self):
        """Verifica que el objeto DireccionParseada genere la query correcta para Google"""
        direccion = parsear_texto("CL 72 46 10")
        query = str(direccion)
        self.assertEqual(query, "Calle 72 46 - 10, Barranquilla, Colombia")

    def test_cache_logic(self):
        """Verifica que el sistema de caché guarde los datos correctamente"""
        direccion = parsear_texto("Calle Falsa 123")
        # Simulamos una inserción manual en el caché
        self.geocoder.cache[str(direccion)] = (10.123, -74.456)
        
        # Ahora al pedir coordenadas, debería traerlas del caché sin llamar a la API
        coords = self.geocoder.obtener_coordenadas(direccion)
        self.assertEqual(coords, (10.123, -74.456))

if __name__ == '__main__':
    unittest.main()
