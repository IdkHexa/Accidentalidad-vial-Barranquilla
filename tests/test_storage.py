"""Pruebas del repositorio DAO.

Verifican la insercion, el conteo y los filtros de
``AccidenteRepository`` usando una base de datos en memoria.
"""

import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data.database import AccidenteDB, Base
from data.direccion_parser import parsear_texto
from data.storage import AccidenteRepository
from models.entidades import AccidenteDTO


class TestAccidenteRepository(unittest.TestCase):
    """Prueba las operaciones basicas del repositorio DAO."""

    def setUp(self):
        """
        Crea una base de datos SQLite en memoria, crea las tablas
        y prepara una sesión y un repositorio para cada test.
        """

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.Session()
        self.repository = AccidenteRepository(self.session)

    def tearDown(self):
        """Cierra la sesión al final de cada test."""
        self.session.close()
        self.engine.dispose()

    def _crear_dto(self, año=2020, gravedad="Leve", **kwargs):
        """Crea un ``AccidenteDTO`` con valores por defecto.

        - ``año``: año del accidente.
        - ``gravedad``: gravedad del accidente.
        - ``kwargs``: campos adicionales para sobrescribir.

        Retorna un ``AccidenteDTO`` listo para insertar.
        """

        datos = {
            "fecha_accidente": f"{año}-01-15T00:00:00.000",
            "hora_accidente": "12:30:00",
            "gravedad_accidente": gravedad,
            "clase_accidente": "Choque",
            "a_o_accidente": año,
            "mes_accidente": "ENERO",
            "dia_accidente": "MIERCOLES",
            "sitio_exacto_accidente": "CL 45 20 10",
            "cant_heridos_en_sitio_accidente": 0,
            "cant_muertos_en_sitio_accidente": 0,
            "cantidad_accidentes": 1,
            "latitud": 10.987,
            "longitud": -74.789,
        }
        datos.update(kwargs)
        return AccidenteDTO(**datos)

    def test_insertar_y_contar(self):
        """Inserta un solo accidente y verifica que ``contar()`` devuelva 1."""
        dto = self._crear_dto()
        insertados = self.repository.insertar_lote([dto])
        self.assertEqual(insertados, 1)
        self.assertEqual(self.repository.contar(), 1)

    def test_insertar_lote(self):
        """Inserta multiples accidentes y verifica que ``contar()`` devuelva el total."""
        dto_1 = self._crear_dto(año=2018)
        dto_2 = self._crear_dto(año=2019)
        dto_3 = self._crear_dto(año=2020)
        insertados = self.repository.insertar_lote([dto_1, dto_2, dto_3])
        self.assertEqual(insertados, 3)
        self.assertEqual(self.repository.contar(), 3)

    def test_obtener_por_año(self):
        """Obtiene accidentes por año y verifica que el resultado tenga la cantidad correcta."""
        dto_2018 = self._crear_dto(año=2018)
        dto_2019_1 = self._crear_dto(año=2019)
        dto_2020 = self._crear_dto(año=2020)
        self.repository.insertar_lote([dto_2018, dto_2019_1, dto_2020])

        resultados = self.repository.obtener_por_año(2019)
        self.assertEqual(len(resultados), 1)
        for r in resultados:
            self.assertEqual(r.a_o_accidente, 2019)

    def test_obtener_por_gravedad(self):
        """Filtra accidentes por gravedad y verifica que solo retorne los que coinciden."""
        dto_leve = self._crear_dto(gravedad="Leve")
        dto_grave = self._crear_dto(gravedad="Grave")
        self.repository.insertar_lote([dto_leve, dto_grave])

        resultados = self.repository.obtener_por_gravedad("Leve")
        self.assertEqual(len(resultados), 1)
        for r in resultados:
            self.assertEqual(r.gravedad_accidente, "Leve")

    def test_obtener_todos_orden_descendente(self):
        """Verifica que ``obtener_todos()`` devuelva los registros del mas reciente al mas antiguo."""
        dto_1 = self._crear_dto()
        dto_2 = self._crear_dto()
        self.repository.insertar_lote([dto_1, dto_2])
        resultados = self.repository.obtener_todos(limit=2)
        self.assertEqual(len(resultados), 2)
        # El segundo insertado tiene ID mayor, debe aparecer primero
        self.assertGreater(resultados[0].id, resultados[1].id)


if __name__ == "__main__":
    unittest.main()
