"""Pruebas unitarias del mapeo DTO a ORM (``AccidenteDB.desde_dto``).

Verifica que cada campo del ``AccidenteDTO`` de Pydantic se asigne
a la columna correcta del modelo SQLAlchemy, especialmente aquellos
cuyo nombre cambia entre la capa de validacion y la de persistencia.
"""

import unittest
from data.database import AccidenteDB
from models.entidades import AccidenteDTO


class TestAccidenteDBMapping(unittest.TestCase):
    """Ejercita el metodo ``desde_dto`` de ``AccidenteDB``.

    ``desde_dto`` es un puente entre dos mundos: el Pydantic con
    acentos (``AÑO_ACCIDENTE``) y el ORM sin acentos
    (``a_o_accidente``).  Cada test verifica que un grupo de campos
    se mapee correctamente, incluyendo los casos borde como
    ``None`` en la direccion.
    """
    def setUp(self):
        """Crea un DTO completo y lo transforma a ORM para usar en multiples tests."""
        self.dto = AccidenteDTO(
            fecha_accidente="2024-01-01",
            hora_accidente="12:00",
            gravedad_accidente="Leve",
            clase_accidente="Choque",
            a_o_accidente=2024,
            mes_accidente="ENERO",
            dia_accidente="LUNES",
            sitio_exacto_accidente="CL 45 20 10",
            cant_heridos_en_sitio_accidente=2,
            cant_muertos_en_sitio_accidente=1,
            cantidad_accidentes=3,
            latitud=10.959,
            longitud=-74.825,
        )
        self.db = AccidenteDB.desde_dto(self.dto)

    def test_mapea_campos_principales(self):
        """Los campos de fecha, hora, gravedad y clase pasan sin alteracion."""
        self.assertEqual(self.db.fecha_accidente, self.dto.FECHA_ACCIDENTE)
        self.assertEqual(self.db.hora_accidente, self.dto.HORA_ACCIDENTE)
        self.assertEqual(self.db.gravedad_accidente, self.dto.GRAVEDAD_ACCIDENTE)
        self.assertEqual(self.db.clase_accidente, self.dto.CLASE_ACCIDENTE)
        self.assertEqual(self.db.a_o_accidente, self.dto.AÑO_ACCIDENTE)
        self.assertEqual(self.db.mes_accidente, self.dto.MES_ACCIDENTE)
        self.assertEqual(self.db.dia_accidente, self.dto.DIA_ACCIDENTE)

    def test_mapea_enteros_y_coordenadas(self):
        """Los contadores y la ubicacion geografica se copian sin transformacion."""
        self.assertEqual(self.db.cant_heridos_en_sitio_accidente, self.dto.CANT_HERIDOS_EN_SITIO_ACCIDENTE)
        self.assertEqual(self.db.cant_muertos_en_sitio_accidente, self.dto.CANT_MUERTOS_EN_SITIO_ACCIDENTE)
        self.assertEqual(self.db.cantidad_accidentes, self.dto.CANTIDAD_ACCIDENTES)
        self.assertEqual(self.db.latitud, self.dto.LATITUD)
        self.assertEqual(self.db.longitud, self.dto.LONGITUD)

    def test_direccion_stringifica_objeto(self):
        """Un ``DireccionParseada`` se convierte a texto plano en el ORM."""
        self.assertIsInstance(self.db.sitio_exacto_accidente, str)
        self.assertIn("Calle 45 20", self.db.sitio_exacto_accidente)

    def test_direccion_none_se_preserva_none(self):
        """Cuando la direccion original es ``None``, la columna tambien lo es."""
        dto = AccidenteDTO(
            fecha_accidente="2024-01-01",
            hora_accidente="12:00",
            gravedad_accidente="Leve",
            clase_accidente="Choque",
            a_o_accidente=2024,
            mes_accidente="ENERO",
            dia_accidente="LUNES",
            sitio_exacto_accidente=None,
            cant_heridos_en_sitio_accidente=2,
            cant_muertos_en_sitio_accidente=1,
            cantidad_accidentes=3,
            latitud=10.959,
            longitud=-74.825,
        )
        db = AccidenteDB.desde_dto(dto)
        self.assertIsNone(db.sitio_exacto_accidente)


if __name__ == "__main__":
    unittest.main()
