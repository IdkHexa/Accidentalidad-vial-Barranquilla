"""Pruebas unitarias del modelo ``AccidenteDTO``.

Verifica que los field_validators (traduccion de meses/dias,
coercion de enteros, parseo de direcciones) se comporten
correctamente tanto con datos validos como con casos limite.
"""

import unittest
from pydantic import ValidationError

from models.entidades import AccidenteDTO


class TestAccidenteDTO(unittest.TestCase):
    """Ejercita cada validador de ``AccidenteDTO`` por separado.

    Cada metodo de esta clase prueba un validador en aislamiento
    para garantizar que los cambios futuros en ``entidades.py``
    no alteren el comportamiento esperado sin que los tests lo
    detecten.
    """

    def setUp(self):
        """Crea un DTO con datos tipicos para usar en multiples tests."""
        self.accidente = self._crear_accidente_dto()

    def _crear_accidente_dto(self, **overrides):
        """Construye un ``AccidenteDTO`` con valores por omision.

        ``overrides`` permite reemplazar campos especificos sin
        repetir el diccionario completo en cada test.
        """
        datos = {
            "fecha_accidente": "2024-01-01",
            "hora_accidente": "12:00:00",
            "gravedad_accidente": "Leve",
            "clase_accidente": "Choque",
            "a_o_accidente": 2024,
            "mes_accidente": "ENERO",
            "dia_accidente": "LUNES",
            "sitio_exacto_accidente": "Calle 45 20 10",
            "cant_heridos_en_sitio_accidente": 1,
            "cant_muertos_en_sitio_accidente": 0,
            "cantidad_accidentes": 1,
        }
        datos.update(overrides)
        return AccidenteDTO(**datos)

    def test_dto_inicializa_campos_principales(self):
        """Verifica que los campos obligatorios se asignen correctamente."""
        self.assertEqual(self.accidente.FECHA_ACCIDENTE, "2024-01-01")
        self.assertEqual(self.accidente.HORA_ACCIDENTE, "12:00:00")
        self.assertEqual(self.accidente.GRAVEDAD_ACCIDENTE, "Leve")
        self.assertEqual(self.accidente.CLASE_ACCIDENTE, "Choque")
        self.assertEqual(self.accidente.AÑO_ACCIDENTE, 2024)
        self.assertEqual(self.accidente.MES_ACCIDENTE, "ENERO")
        self.assertEqual(self.accidente.DIA_ACCIDENTE, "LUNES")

    def test_direccion_se_parsea_como_objeto(self):
        """Verifica que un string crudo se convierta en ``DireccionParseada``."""
        direccion = self.accidente.SITIO_EXACTO_ACCIDENTE
        self.assertIsNotNone(direccion)
        self.assertEqual(direccion.tipo_via, "Calle")
        self.assertEqual(direccion.numero_via, "45")
        self.assertEqual(direccion.numero_cruce, "20")
        self.assertEqual(direccion.complemento, "10")

    def test_limpiar_mes_traduce_ingles_a_espanol(self):
        """``limpiar_mes`` transforma ``JANUARY`` en ``ENERO``."""
        dto = self._crear_accidente_dto(mes_accidente="JANUARY")
        self.assertEqual(dto.MES_ACCIDENTE, "ENERO")

    def test_limpiar_mes_no_modifica_mes_espanol(self):
        """``limpiar_mes`` deja pasar ``MARZO`` sin alterarlo."""
        dto = self._crear_accidente_dto(mes_accidente="MARZO")
        self.assertEqual(dto.MES_ACCIDENTE, "MARZO")

    def test_limpiar_dia_traduce_abreviatura_ingles_a_espanol(self):
        """``limpiar_dia`` transforma ``WED`` en ``MIERCOLES``."""
        dto = self._crear_accidente_dto(dia_accidente="WED")
        self.assertEqual(dto.DIA_ACCIDENTE, "MIERCOLES")

    def test_asegurar_entero_convierte_string_numerico(self):
        """``asegurar_entero`` convierte ``\"7\"`` en el entero ``7``."""
        dto = self._crear_accidente_dto(cantidad_accidentes="7")
        self.assertEqual(dto.CANTIDAD_ACCIDENTES, 7)

    def test_asegurar_entero_convierte_float_a_entero(self):
        """``asegurar_entero`` trunca ``2.5`` a ``2``."""
        dto = self._crear_accidente_dto(cant_heridos_en_sitio_accidente=2.5)
        self.assertEqual(dto.CANT_HERIDOS_EN_SITIO_ACCIDENTE, 2)

    def test_asegurar_entero_valor_corrupto_se_convierte_a_cero(self):
        """``asegurar_entero`` devuelve ``0`` para strings no numericos."""
        dto = self._crear_accidente_dto(cant_muertos_en_sitio_accidente="abc")
        self.assertEqual(dto.CANT_MUERTOS_EN_SITIO_ACCIDENTE, 0)

    def test_asegurar_entero_none_se_convierte_a_cero(self):
        """``asegurar_entero`` devuelve ``0`` cuando recibe ``None``."""
        dto = self._crear_accidente_dto(cantidad_accidentes=None)
        self.assertEqual(dto.CANTIDAD_ACCIDENTES, 0)

    def test_parsear_direccion_none_se_mantiene_none(self):
        """``parsear_direccion`` deja ``None`` igual cuando no hay direccion."""
        dto = self._crear_accidente_dto(sitio_exacto_accidente=None)
        self.assertIsNone(dto.SITIO_EXACTO_ACCIDENTE)

    def test_opcionales_default_cuando_se_omiten(self):
        """Campos opcionales omitidos toman el valor por defecto del modelo."""
        dto = self._crear_accidente_dto()
        self.assertEqual(dto.CANT_MUERTOS_EN_SITIO_ACCIDENTE, 0)
        self.assertEqual(dto.LATITUD, None)
        self.assertEqual(dto.LONGITUD, None)

    def test_falta_campo_obligatorio_levanta_validation_error(self):
        """Omitir ``fecha_accidente`` debe lanzar ``ValidationError``."""
        with self.assertRaises(ValidationError):
            AccidenteDTO(
                hora_accidente="12:00:00",
                gravedad_accidente="Leve",
                clase_accidente="Choque",
                a_o_accidente=2024,
                mes_accidente="ENERO",
                dia_accidente="LUNES",
                sitio_exacto_accidente="Calle 45 20 10",
                cant_heridos_en_sitio_accidente=1,
                cantidad_accidentes=1,
            )


if __name__ == "__main__":
    unittest.main()
