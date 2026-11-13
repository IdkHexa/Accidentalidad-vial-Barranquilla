"""Pruebas unitarias de validacion y normalizacion en ``AccidenteDTO``."""

import unittest

from models.entidades import AccidenteDTO


class TestAccidenteDTO(unittest.TestCase):
    """Verifica las reglas de traduccion y sanitizacion de ``AccidenteDTO``."""

    def _base(self, **overrides):
        """Construye un payload minimo valido con sobrescrituras opcionales."""
        datos = {
            "fecha_accidente": "2026-09-30T00:00:00.000",
            "hora_accidente": "12:30:00:pm",
            "gravedad_accidente": "Con heridos",
            "clase_accidente": "Choque",
            "a_o_accidente": "2026",
            "mes_accidente": "September",
            "dia_accidente": "Wed",
            "cant_heridos_en_sitio_accidente": "1.0",
        }
        datos.update(overrides)
        return AccidenteDTO(**datos)

    def test_normaliza_dias_ingles_y_espanol_con_tildes(self):
        """Unifica abreviaturas y tildes a los siete dias canonicos."""
        casos = {
            "Mon": "LUNES",
            "LUN": "LUNES",
            "Tue": "MARTES",
            "Wed": "MIERCOLES",
            "MIÉ": "MIERCOLES",
            "Miércoles": "MIERCOLES",
            "Thu": "JUEVES",
            "Fri": "VIERNES",
            "VIE": "VIERNES",
            "Sat": "SABADO",
            "SÁB": "SABADO",
            "Sábado": "SABADO",
            "Sun": "DOMINGO",
            "DOM": "DOMINGO",
        }
        for entrada, esperado in casos.items():
            dto = self._base(dia_accidente=entrada)
            self.assertEqual(dto.DIA_ACCIDENTE, esperado)

    def test_traduce_mes_y_asigna_default_cantidad_uno(self):
        """Traduce meses en ingles y usa 1 cuando falta ``cantidad_accidentes``."""
        dto = self._base()
        self.assertEqual(dto.MES_ACCIDENTE, "SEPTIEMBRE")
        self.assertEqual(dto.CANTIDAD_ACCIDENTES, 1)
        self.assertEqual(dto.CANT_HERIDOS_EN_SITIO_ACCIDENTE, 1)


if __name__ == "__main__":
    unittest.main()
