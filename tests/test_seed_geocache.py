"""Pruebas del script de precarga de coordenadas (``seed_geocache.py``).

``obtener_total`` descubre cuantos registros tiene la API, y
``precargar_geocache`` recorre las direcciones geocodificando solo
las que aun no estan en el cache.  Los tests mockean el cliente
HTTP y el geocodificador para no depender de servicios externos.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from seed_geocache import obtener_total, precargar_geocache


class TestSeedGeocache(unittest.TestCase):
    """Ejercita las funciones de precarga de coordenadas.

    ``obtener_total`` se testea con un cliente mockeado que simula
    la respuesta de Socrata, y ``precargar_geocache`` se prueba en
    modo ``dry_run`` para verificar que no se hagan llamadas reales
    a Google Maps.
    """
    def test_obtener_total_devuelve_entero(self):
        """``obtener_total`` parsea correctamente el JSON de Socrata."""
        mock_cliente = MagicMock()
        mock_cliente.client.get = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [{"count": "28431"}]
        mock_response.raise_for_status = MagicMock()
        mock_cliente.client.get.return_value = mock_response

        total = asyncio.run(obtener_total(mock_cliente))

        self.assertEqual(total, 28431)

    @patch("seed_geocache.ApiClient")
    @patch("seed_geocache.GeoCoder")
    def test_precargar_geocache_dry_run_cuenta_direcciones(self, mock_geocoder_cls, mock_api_client_cls):
        """``dry_run=True`` no llama a Google Maps, solo cuenta."""
        mock_client = MagicMock()
        mock_client.client = MagicMock()
        mock_client.client.get = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [{"count": "4"}]
        mock_response.raise_for_status = MagicMock()
        mock_client.client.get.return_value = mock_response
        mock_client.get_dataset_limit = AsyncMock(
            return_value=[
                {"sitio_exacto_accidente": "CL 50 44"},
                {"sitio_exacto_accidente": "CL 50 44"},
                {"sitio_exacto_accidente": "CL 10 5 20"},
                {"sitio_exacto_accidente": ""},
            ]
        )
        mock_client.close = AsyncMock()
        mock_api_client_cls.return_value = mock_client

        mock_geocoder = MagicMock()
        mock_geocoder.cache = {"Calle 50 44, Barranquilla, Colombia": [10.0, -74.0]}
        mock_geocoder_cls.return_value = mock_geocoder

        asyncio.run(precargar_geocache(dry_run=True))

        mock_geocoder.obtener_coordenadas.assert_not_called()


if __name__ == "__main__":
    unittest.main()
