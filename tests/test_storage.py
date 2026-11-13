"""Pruebas del repositorio DAO ``AccidenteRepository``.

Verifican la insercion, idempotencia, filtros, agregaciones estadisticas,
operaciones CRUD transaccionales y proyeccion para clustering en memoria.
"""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data.database import Base
from data.storage import AccidenteRepository
from models.entidades import AccidenteDTO


class TestAccidenteRepository(unittest.TestCase):
    """Prueba todas las operaciones del repositorio DAO."""

    def setUp(self):
        """Crea una base de datos SQLite en memoria limpia por prueba."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.Session()
        self.repository = AccidenteRepository(self.session)

    def tearDown(self):
        """Cierra sesion y motor tras cada prueba."""
        self.session.close()
        self.engine.dispose()

    def _crear_dto(self, año=2020, gravedad="Solo daños", **kwargs):
        """Construye un ``AccidenteDTO`` con valores por defecto."""
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
        """Inserta un accidente y verifica que ``contar()`` devuelva 1."""
        dto = self._crear_dto()
        insertados = self.repository.insertar_lote([dto])
        self.assertEqual(insertados, 1)
        self.assertEqual(self.repository.contar(), 1)

    def test_insertar_lote(self):
        """Inserta multiples accidentes y verifica que ``contar()`` devuelva el total."""
        dtos = [self._crear_dto(año=2018), self._crear_dto(año=2019), self._crear_dto(año=2020)]
        insertados = self.repository.insertar_lote(dtos)
        self.assertEqual(insertados, 3)
        self.assertEqual(self.repository.contar(), 3)

    def test_sincronizar_lote_es_idempotente(self):
        """Re-sincronizar el mismo lote no duplica registros existentes."""
        lote = [self._crear_dto(año=2024), self._crear_dto(año=2025)]
        self.assertEqual(self.repository.sincronizar_lote(lote), 2)
        self.assertEqual(self.repository.sincronizar_lote(lote), 0)
        self.assertEqual(self.repository.contar(), 2)

        lote.append(self._crear_dto(año=2026))
        self.assertEqual(self.repository.sincronizar_lote(lote), 1)
        self.assertEqual(self.repository.contar(), 3)

    def test_obtener_por_año(self):
        """Obtiene accidentes filtrados por año."""
        self.repository.insertar_lote(
            [self._crear_dto(año=2018), self._crear_dto(año=2019), self._crear_dto(año=2020)]
        )
        resultados = self.repository.obtener_por_año(2019)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].a_o_accidente, 2019)

    def test_obtener_por_gravedad(self):
        """Filtra accidentes por gravedad."""
        self.repository.insertar_lote(
            [self._crear_dto(gravedad="Con heridos"), self._crear_dto(gravedad="Con muertos")]
        )
        resultados = self.repository.obtener_por_gravedad("Con heridos")
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].gravedad_accidente, "Con heridos")

    def test_obtener_todos_orden_descendente(self):
        """Verifica orden descendente por ID."""
        self.repository.insertar_lote([self._crear_dto(), self._crear_dto()])
        resultados = self.repository.obtener_todos(limit=2)
        self.assertEqual(len(resultados), 2)
        self.assertGreater(resultados[0].id, resultados[1].id)

    def test_resumen_y_estadisticas_sql(self):
        """Verifica KPIs y agrupaciones por año, mes, dia y hora."""
        self.repository.insertar_lote([
            self._crear_dto(
                año=2025,
                hora_accidente="02:15:00:pm",
                gravedad="Con muertos",
                cant_muertos_en_sitio_accidente=1,
                cant_heridos_en_sitio_accidente=2,
            ),
            self._crear_dto(
                año=2026,
                hora_accidente="08:00:00:am",
                mes_accidente="SEPTIEMBRE",
                dia_accidente="SÁB",
            ),
        ])
        resumen = self.repository.obtener_resumen()
        self.assertEqual(resumen["total"], 2)
        self.assertEqual(resumen["muertos"], 1)
        self.assertEqual(resumen["heridos"], 2)
        self.assertEqual(resumen["año_inicio"], 2025)
        self.assertEqual(resumen["año_fin"], 2026)

        por_dia = {d["dia"]: d["total"] for d in self.repository.contar_por_dia()}
        self.assertEqual(por_dia["SABADO"], 1)
        self.assertEqual(por_dia["MIERCOLES"], 1)

        por_hora = {h["hora"]: h["total"] for h in self.repository.contar_por_hora()}
        self.assertEqual(por_hora[14], 1)
        self.assertEqual(por_hora[8], 1)

    def test_crud_crear_actualizar_y_eliminar(self):
        """Verifica ciclo CRUD completo en ``AccidenteRepository``."""
        creado = self.repository.crear({
            "fecha_accidente": "2026-10-01",
            "hora_accidente": "15:00",
            "gravedad_accidente": "Solo daños",
            "clase_accidente": "Choque",
            "a_o_accidente": 2026,
            "mes_accidente": "OCTUBRE",
            "dia_accidente": "JUEVES",
        })
        self.assertIsNotNone(creado.id)

        actualizado = self.repository.actualizar(creado.id, {"gravedad_accidente": "Con heridos", "cant_heridos_en_sitio_accidente": 1})
        self.assertEqual(actualizado.gravedad_accidente, "Con heridos")
        self.assertEqual(actualizado.cant_heridos_en_sitio_accidente, 1)

        self.assertTrue(self.repository.eliminar(creado.id))
        self.assertIsNone(self.repository.obtener_por_id(creado.id))

    def test_obtener_para_clustering_filtra_nulos(self):
        """Solo proyecta registros con coordenadas no nulas para DBSCAN."""
        self.repository.insertar_lote([
            self._crear_dto(latitud=10.98, longitud=-74.80),
            self._crear_dto(latitud=None, longitud=None),
        ])
        df = self.repository.obtener_para_clustering()
        self.assertEqual(len(df), 1)
        self.assertEqual(list(df.columns), [
            "latitud", "longitud", "año", "cantidad_accidentes",
            "cant_heridos_en_sitio_accidente", "cant_muertos_en_sitio_accidente",
            "gravedad_accidente",
        ])


if __name__ == "__main__":
    unittest.main()
