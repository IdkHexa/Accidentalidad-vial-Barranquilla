"""Pruebas de integracion HTTP del controlador FastAPI."""

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from controllers.main_controller import app, get_repository, invalidar_cache_clusters
from data.database import Base
from data.storage import AccidenteRepository


class TestMainController(unittest.TestCase):
    """Ejercita los endpoints REST, HTML y CRUD con SQLite aislado en memoria."""

    def setUp(self):
        """Configura una base en memoria compartida por sesion y reemplaza ``get_repository``."""
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        def override_repo():
            db = self.Session()
            try:
                yield AccidenteRepository(db)
            finally:
                db.close()

        app.dependency_overrides[get_repository] = override_repo
        invalidar_cache_clusters()
        self.client = TestClient(app)

    def tearDown(self):
        """Restaura dependencias de FastAPI y libera el motor en memoria."""
        app.dependency_overrides.clear()
        invalidar_cache_clusters()
        self.engine.dispose()

    def test_health_y_paginas_html(self):
        """Las rutas principales y ``/health`` responden 200 OK."""
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        for ruta in ("/", "/dashboard", "/mapa", "/registro"):
            resp = self.client.get(ruta)
            self.assertEqual(resp.status_code, 200, f"Fallo HTML en {ruta}")

    def test_post_con_coordenadas_vacias_y_crud_completo(self):
        """``POST /api/accidentes`` acepta latitud/longitud vacias sin lanzar 422."""
        payload_form = {
            "fecha_accidente": "2026-09-30",
            "hora_accidente": "14:20",
            "gravedad_accidente": "Con heridos",
            "clase_accidente": "Choque",
            "a_o_accidente": "2026",
            "mes_accidente": "septiembre",
            "dia_accidente": "miércoles",
            "sitio_exacto_accidente": "CL 72 # 43-10",
            "cant_heridos_en_sitio_accidente": "1",
            "cant_muertos_en_sitio_accidente": "0",
            "cantidad_accidentes": "1",
            "latitud": "",
            "longitud": "",
        }
        res_post = self.client.post("/api/accidentes", data=payload_form)
        self.assertEqual(res_post.status_code, 201)
        accidente_id = res_post.json()["id"]

        res_list = self.client.get("/api/accidentes?limit=10")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.json()), 1)
        self.assertEqual(res_list.json()[0]["dia"], "MIERCOLES")

        res_put = self.client.put(
            f"/api/accidentes/{accidente_id}",
            json={"gravedad_accidente": "Solo daños", "cant_heridos_en_sitio_accidente": 0},
        )
        self.assertEqual(res_put.status_code, 200)

        res_del = self.client.delete(f"/api/accidentes/{accidente_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(self.client.delete(f"/api/accidentes/{accidente_id}").status_code, 404)

    def test_endpoints_estadisticas_y_clusters_con_bd_vacia(self):
        """Ningun endpoint estadistico ni DBSCAN falla cuando no hay filas."""
        endpoints = [
            "/api/stats/resumen",
            "/api/stats/años",
            "/api/stats/por_año",
            "/api/stats/por_gravedad",
            "/api/stats/por_clase",
            "/api/stats/por_mes",
            "/api/stats/por_dia",
            "/api/stats/por_hora",
            "/api/stats/clusters",
            "/api/mapa/puntos",
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, 200, f"Fallo en {ep}: {resp.text}")


if __name__ == "__main__":
    unittest.main()
