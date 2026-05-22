"""Pruebas unitarias del cliente HTTP contra la API de Socrata.

Dado que ``ApiClient`` hace peticiones HTTP reales, todos los tests
mockean ``httpx.AsyncClient`` para evitar dependencia de red y
poder controlar exactamente lo que devuelve la API en cada escenario.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from api.api_client import ApiClient


class TestApiClient(unittest.TestCase):
    """Ejercita la paginacion, el manejo de errores y el cierre del cliente.

    Cada test crea una instancia de ``ApiClient`` con el ``AsyncClient``
    reemplazado por un ``MagicMock``, lo que permite simular respuestas
    HTTP sin tocar internet.
    """
    def setUp(self):
        """Reemplaza ``httpx.AsyncClient`` por un mock antes de cada test.

        ``self.mock_instance`` es el objeto que se usara como
        ``client.client`` dentro de ``ApiClient``.  ``get`` y ``aclose``
        son ``AsyncMock`` para poder simular llamadas asincronas.
        """
        self.patcher = patch("api.api_client.httpx.AsyncClient")
        self.mock_async_client = self.patcher.start()
        self.mock_instance = MagicMock()
        self.mock_instance.get = AsyncMock()
        self.mock_instance.aclose = AsyncMock()
        self.mock_async_client.return_value = self.mock_instance

    def tearDown(self):
        """Restaura ``httpx.AsyncClient`` a su implementacion original."""
        self.patcher.stop()

    def test_limite_menor_a_pagina(self):
        """Con limit=500, hace UNA llamada con $limit=500 y termina."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": i} for i in range(500)]
        mock_resp.raise_for_status = MagicMock()
        self.mock_instance.get.return_value = mock_resp

        client = ApiClient()
        resultado = asyncio.run(client.get_dataset_limit("yb9r-2dsi", 500))

        self.assertEqual(len(resultado), 500)
        self.assertEqual(self.mock_instance.get.call_count, 1)
        primer_llamado = self.mock_instance.get.call_args_list[0]
        self.assertEqual(primer_llamado.kwargs["params"], {"$limit": 500, "$offset": 0, "$order": "fecha_accidente"})

    def test_limite_igual_a_pagina(self):
        """Con limit=1000, hace UNA llamada y no pide más."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": i} for i in range(1000)]
        mock_resp.raise_for_status = MagicMock()
        self.mock_instance.get.return_value = mock_resp

        client = ApiClient()
        resultado = asyncio.run(client.get_dataset_limit("yb9r-2dsi", 1000))

        self.assertEqual(len(resultado), 1000)
        self.assertEqual(self.mock_instance.get.call_count, 1)
        primer_llamado = self.mock_instance.get.call_args_list[0]
        self.assertEqual(primer_llamado.kwargs["params"], {"$limit": 1000, "$offset": 0, "$order": "fecha_accidente"})

    def test_paginacion_multiple(self):
        """Con limit=2500, hace 3 llamadas: 1000 + 1000 + 500."""
        mock_resp_1 = MagicMock()
        mock_resp_1.json.return_value = [{"id": i} for i in range(1000)]
        mock_resp_1.raise_for_status = MagicMock()

        mock_resp_2 = MagicMock()
        mock_resp_2.json.return_value = [{"id": i} for i in range(1000)]
        mock_resp_2.raise_for_status = MagicMock()

        mock_resp_3 = MagicMock()
        mock_resp_3.json.return_value = [{"id": i} for i in range(500)]
        mock_resp_3.raise_for_status = MagicMock()

        self.mock_instance.get.side_effect = [mock_resp_1, mock_resp_2, mock_resp_3]

        client = ApiClient()
        resultado = asyncio.run(client.get_dataset_limit("yb9r-2dsi", 2500))

        self.assertEqual(len(resultado), 2500)
        self.assertEqual(self.mock_instance.get.call_count, 3)

        params_1 = self.mock_instance.get.call_args_list[0].kwargs["params"]
        params_2 = self.mock_instance.get.call_args_list[1].kwargs["params"]
        params_3 = self.mock_instance.get.call_args_list[2].kwargs["params"]

        self.assertEqual(params_1, {"$limit": 1000, "$offset": 0, "$order": "fecha_accidente"})
        self.assertEqual(params_2, {"$limit": 1000, "$offset": 1000, "$order": "fecha_accidente"})
        self.assertEqual(params_3, {"$limit": 500, "$offset": 2000, "$order": "fecha_accidente"})

    def test_api_devuelve_menos_registros(self):
        """Si la API solo tiene 100 registros, se corta ahi aunque pidamos 500."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": i} for i in range(100)]
        mock_resp.raise_for_status = MagicMock()
        self.mock_instance.get.return_value = mock_resp

        client = ApiClient()
        resultado = asyncio.run(client.get_dataset_limit("yb9r-2dsi", 500))

        self.assertEqual(len(resultado), 100)
        self.assertEqual(self.mock_instance.get.call_count, 1)

    def test_error_http_no_interrumpe_proceso(self):
        """Un error HTTP muestra el mensaje y devuelve lo descargado hasta ahi."""
        self.mock_instance.get.side_effect = Exception("timeout")

        client = ApiClient()
        resultado = asyncio.run(client.get_dataset_limit("yb9r-2dsi", 500))

        self.assertEqual(len(resultado), 0)
        self.assertEqual(self.mock_instance.get.call_count, 1)

    def test_close_cierra_cliente_http(self):
        """close() llama a aclose() del cliente interno."""
        client = ApiClient()
        asyncio.run(client.close())

        self.mock_instance.aclose.assert_called_once()


if __name__ == "__main__":
    unittest.main()
