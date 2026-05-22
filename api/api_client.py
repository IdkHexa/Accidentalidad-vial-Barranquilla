"""Cliente asincrono para consultar el dataset publico.

Este modulo concentra la comunicacion HTTP con la API y aplica paginacion para
traer los datos en lotes controlados.
"""

import httpx
from config import API_URL, DATASET_ID


class ApiClient:
    """Encapsula la consulta HTTP al portal de datos abiertos."""

    def __init__(self):
        """Crea el cliente asincrono con un tiempo de espera fijo."""
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_dataset_limit(self, dataset_id, limit):
        """
        Descarga hasta `limit` registros del dataset solicitado.

        Parametros:
        - `dataset_id`: identificador del recurso en Socrata.
        - `limit`: numero maximo de filas a recuperar.
        """
        url_final = API_URL if dataset_id == DATASET_ID else API_URL.replace(DATASET_ID, dataset_id)

        # `offset` indica desde que posicion inicia cada pagina.
        offset = 0
        data = []

        while offset < limit:
            # `paso` controla el tamano del lote en cada consulta.
            paso = min(1000, limit - offset)

            try:
                response = await self.client.get(
                    url_final,
                    params={
                        "$limit": paso,
                        "$offset": offset,
                        "$order": "fecha_accidente",
                    },
                )
                response.raise_for_status()

                lote = response.json()
                data.extend(lote)
                offset = offset + paso

                # Si la API devuelve menos filas de las pedidas, ya no hay mas datos.
                if len(lote) < paso:
                    break
            except Exception as e:
                # Ante un error se conserva lo ya descargado.
                print(f"Error al bajar datos de la API: {e}")
                break

        return data

    async def close(self):
        """Cierra el cliente HTTP al finalizar la consulta."""
        await self.client.aclose()
