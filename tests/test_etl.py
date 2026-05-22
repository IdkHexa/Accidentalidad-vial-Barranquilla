"""Pruebas del pipeline ETL (``ejecutar_etl``).

``ejecutar_etl`` coordina la descarga, validacion, geocodificacion
y persistencia de los datos.  Todos los tests reemplazan las
dependencias externas (``ApiClient``, ``GeoCoder``, ``AccidenteRepository``)
por mocks para poder controlar cada escenario sin tocar internet ni la BD.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from data.etl import ejecutar_etl


class TestEtlPipeline(unittest.TestCase):
    """Ejercita ``ejecutar_etl`` en distintos escenarios.

    Cada test parchea ``ApiClient``, ``GeoCoder``, ``SessionLocal`` y
    ``AccidenteRepository`` para simular respuestas de la API, la
    geocodificacion y la base de datos sin depender de infraestructura real.
    """
    @patch("data.etl.AccidenteRepository")
    @patch("data.etl.SessionLocal")
    @patch("data.etl.GeoCoder")
    @patch("data.etl.ApiClient")
    def test_happy_path_inserta_registros_validos(
        self,
        mock_api_client_cls,
        mock_geocoder_cls,
        mock_session_cls,
        mock_repo_cls,
    ):
        """Registros validos con coordenadas propias pasan por el pipeline sin geocodificar."""
        mock_client = MagicMock()
        mock_client.get_dataset_limit = AsyncMock(
            return_value=[
                {
                    "fecha_accidente": "2024-01-01",
                    "hora_accidente": "12:00",
                    "gravedad_accidente": "Leve",
                    "clase_accidente": "Choque",
                    "a_o_accidente": 2024,
                    "mes_accidente": "ENERO",
                    "dia_accidente": "LUNES",
                    "sitio_exacto_accidente": "CL 45 20 10",
                    "cant_heridos_en_sitio_accidente": 0,
                    "cant_muertos_en_sitio_accidente": 0,
                    "cantidad_accidentes": 1,
                    "latitud": 10.0,
                    "longitud": -74.0,
                },
                {
                    "fecha_accidente": "2024-01-02",
                    "hora_accidente": "13:00",
                    "gravedad_accidente": "Leve",
                    "clase_accidente": "Choque",
                    "a_o_accidente": 2024,
                    "mes_accidente": "ENERO",
                    "dia_accidente": "MARTES",
                    "sitio_exacto_accidente": "CL 10 5 20",
                    "cant_heridos_en_sitio_accidente": 0,
                    "cant_muertos_en_sitio_accidente": 0,
                    "cantidad_accidentes": 1,
                    "latitud": 9.0,
                    "longitud": -75.0,
                },
            ]
        )
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder_cls.return_value = mock_geocoder

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo.insertar_lote.return_value = 2
        mock_repo_cls.return_value = mock_repo

        resultado = asyncio.run(ejecutar_etl(2, guardar_en_bd=True))

        self.assertEqual(len(resultado), 2)
        mock_repo.insertar_lote.assert_called_once()
        mock_geocoder.obtener_coordenadas.assert_not_called()

    @patch("data.etl.AccidenteRepository")
    @patch("data.etl.SessionLocal")
    @patch("data.etl.GeoCoder")
    @patch("data.etl.ApiClient")
    def test_geocoding_fallback_llama_al_geocoder(
        self,
        mock_api_client_cls,
        mock_geocoder_cls,
        mock_session_cls,
        mock_repo_cls,
    ):
        """Registros sin coordenadas se enriquecen llamando al geocodificador."""
        mock_client = MagicMock()
        mock_client.get_dataset_limit = AsyncMock(
            return_value=[
                {
                    "fecha_accidente": "2024-01-01",
                    "hora_accidente": "12:00",
                    "gravedad_accidente": "Leve",
                    "clase_accidente": "Choque",
                    "a_o_accidente": 2024,
                    "mes_accidente": "ENERO",
                    "dia_accidente": "LUNES",
                    "sitio_exacto_accidente": "CL 45 20 10",
                    "cant_heridos_en_sitio_accidente": 0,
                    "cant_muertos_en_sitio_accidente": 0,
                    "cantidad_accidentes": 1,
                    "latitud": None,
                    "longitud": None,
                }
            ]
        )
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder.obtener_coordenadas = MagicMock(return_value=(10.0, -74.0))
        mock_geocoder_cls.return_value = mock_geocoder

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo.insertar_lote.return_value = 1
        mock_repo_cls.return_value = mock_repo

        resultado = asyncio.run(ejecutar_etl(1, guardar_en_bd=True))

        self.assertEqual(len(resultado), 1)
        mock_geocoder.obtener_coordenadas.assert_called_once()
        self.assertEqual(resultado[0].LATITUD, 10.0)
        self.assertEqual(resultado[0].LONGITUD, -74.0)

    @patch("data.etl.AccidenteRepository")
    @patch("data.etl.SessionLocal")
    @patch("data.etl.GeoCoder")
    @patch("data.etl.ApiClient")
    def test_error_validacion_descarta_registro(self,
        mock_api_client_cls,
        mock_geocoder_cls,
        mock_session_cls,
        mock_repo_cls,
    ):
        """Un registro con un campo invalido se descarta sin romper el pipeline."""
        mock_client = MagicMock()
        mock_client.get_dataset_limit = AsyncMock(
            return_value=[
                {
                    "fecha_accidente": "2024-01-01",
                    "hora_accidente": "12:00",
                    "gravedad_accidente": "Leve",
                    "clase_accidente": "Choque",
                    "a_o_accidente": "nope",
                    "mes_accidente": "ENERO",
                    "dia_accidente": "LUNES",
                    "sitio_exacto_accidente": "CL 45 20 10",
                    "cant_heridos_en_sitio_accidente": 0,
                    "cant_muertos_en_sitio_accidente": 0,
                    "cantidad_accidentes": 1,
                    "latitud": 10.0,
                    "longitud": -74.0,
                }
            ]
        )
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder_cls.return_value = mock_geocoder

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        resultado = asyncio.run(ejecutar_etl(1, guardar_en_bd=True))

        self.assertEqual(len(resultado), 0)
        mock_repo.insertar_lote.assert_called_once_with([])

    @patch("data.etl.AccidenteRepository")
    @patch("data.etl.SessionLocal")
    @patch("data.etl.GeoCoder")
    @patch("data.etl.ApiClient")
    def test_api_falla_devuelve_lista_vacia(self,
        mock_api_client_cls,
        mock_geocoder_cls,
        mock_session_cls,
        mock_repo_cls,
    ):
        """Si la API lanza excepcion, se devuelve lista vacia sin crash."""
        mock_client = MagicMock()
        mock_client.get_dataset_limit = AsyncMock(side_effect=Exception("timeout"))
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder_cls.return_value = mock_geocoder

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        resultado = asyncio.run(ejecutar_etl(5, guardar_en_bd=True))

        self.assertEqual(len(resultado), 0)
        mock_repo.insertar_lote.assert_called_once_with([])

    @patch("data.etl.AccidenteRepository")
    @patch("data.etl.SessionLocal")
    @patch("data.etl.GeoCoder")
    @patch("data.etl.ApiClient")
    def test_guardar_en_bd_false_no_inserta(
        self,
        mock_api_client_cls,
        mock_geocoder_cls,
        mock_session_cls,
        mock_repo_cls,
    ):
        """Con ``guardar_en_bd=False`` se salta la persistencia sin errores."""
        mock_client = MagicMock()
        mock_client.get_dataset_limit = AsyncMock(
            return_value=[
                {
                    "fecha_accidente": "2024-01-01",
                    "hora_accidente": "12:00",
                    "gravedad_accidente": "Leve",
                    "clase_accidente": "Choque",
                    "a_o_accidente": 2024,
                    "mes_accidente": "ENERO",
                    "dia_accidente": "LUNES",
                    "sitio_exacto_accidente": "CL 45 20 10",
                    "cant_heridos_en_sitio_accidente": 0,
                    "cant_muertos_en_sitio_accidente": 0,
                    "cantidad_accidentes": 1,
                    "latitud": 10.0,
                    "longitud": -74.0,
                }
            ]
        )
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder_cls.return_value = mock_geocoder

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        resultado = asyncio.run(ejecutar_etl(1, guardar_en_bd=False))

        self.assertEqual(len(resultado), 1)
        mock_repo.insertar_lote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
