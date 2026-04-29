import unittest
from data.direccion_parser import parsear_texto

class TestDireccionParser(unittest.TestCase):
    
    def test_direccion_estandar(self):
        """Prueba una dirección con el formato estándar completo"""
        direccion = "Calle 45 20 10"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle")
        self.assertEqual(resultado.numero_via, "45")
        self.assertEqual(resultado.numero_cruce, "20")
        self.assertEqual(resultado.complemento, "10")

    def test_direccion_con_letras(self):
        """Prueba direcciones con letras (ej: 45B)"""
        direccion = "CRA 43B 80 12"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Carrera")
        self.assertEqual(resultado.numero_via, "43B")

    def test_interseccion_con_con(self):
        """Prueba intersecciones usando el conector 'CON'"""
        direccion = "CALLE 72 CON CRA 46"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle 72")
        self.assertEqual(resultado.interseccion, "Carrera 46")

    def test_interseccion_con_y(self):
        """Prueba intersecciones usando el conector 'Y'"""
        direccion = "VIA 40 Y CALLE 85"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Via 40")
        self.assertEqual(resultado.interseccion, "Calle 85")

    def test_limpieza_ruido(self):
        """Prueba que se eliminen palabras de ruido como 'BARR' o 'ESQUINA'"""
        direccion = "BARR EL PRADO CL 50 44 10 ESQUINA"
        resultado = parsear_texto(direccion)
        self.assertEqual(resultado.tipo_via, "Calle")
        self.assertEqual(resultado.numero_via, "50")

if __name__ == '__main__':
    unittest.main()
