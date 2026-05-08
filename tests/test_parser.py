"""Pruebas unitarias del parser de direcciones."""

import unittest
from data.direccion_parser import parsear_texto


class TestDireccionParser(unittest.TestCase):
    """Verifica formatos de direccion soportados por el parser."""

    def test_direccion_estandar(self):
        """Prueba una direccion con via, cruce y placa."""
        direccion = "Calle 45 20 10"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle")
        self.assertEqual(resultado.numero_via, "45")
        self.assertEqual(resultado.numero_cruce, "20")
        self.assertEqual(resultado.complemento, "10")

    def test_direccion_con_letras(self):
        """Prueba una via cuyo numero incluye una letra."""
        direccion = "CRA 43B 80 12"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Carrera")
        self.assertEqual(resultado.numero_via, "43B")

    def test_interseccion_con_con(self):
        """Prueba una interseccion separada por `CON`."""
        direccion = "CALLE 72 CON CRA 46"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle 72")
        self.assertEqual(resultado.interseccion, "Carrera 46")

    def test_interseccion_con_y(self):
        """Prueba una interseccion separada por `Y`."""
        direccion = "VIA 40 Y CALLE 85"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Via 40")
        self.assertEqual(resultado.interseccion, "Calle 85")

    def test_limpieza_ruido(self):
        """Prueba la eliminacion de palabras que no forman la direccion principal."""
        direccion = "BARR EL PRADO CL 50 44 10 ESQUINA"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle")
        self.assertEqual(resultado.numero_via, "50")


if __name__ == "__main__":
    unittest.main()
