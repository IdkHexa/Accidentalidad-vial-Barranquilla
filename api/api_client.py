"""Cliente asincrono para consultar el dataset publico de Socrata.

Este modulo concentra la comunicacion HTTP con la API y aplica paginacion
determinista para recuperar los datos en lotes controlados.
"""

import httpx

from config import API_URL, DATASET_ID
from utils.logger import obtener_logger

logger = obtener_logger(__name__)


class ApiClient:
    """Encapsula la consulta HTTP al portal de datos abiertos."""

    def __init__(self):
        """Crea el cliente asincrono con un tiempo de espera fijo."""
        self.client = httpx.AsyncClient(timeout=30.0)

    def _resolver_url(self, dataset_id: str) -> str:
        """Construye el endpoint JSON de Socrata para ``dataset_id``."""
        return (
            API_URL
            if dataset_id == DATASET_ID
            else API_URL.replace(DATASET_ID, dataset_id)
        )

    async def obtener_total(self, dataset_id: str = DATASET_ID) -> int | None:
        """Consulta el total de registros disponibles en Socrata via ``$select=count(*)``."""
        url_final = self._resolver_url(dataset_id)
        try:
            response = await self.client.get(
                url_final,
                params={"$select": "count(*)"},
            )
            response.raise_for_status()
            payload = response.json()
            if payload and "count" in payload[0]:
                return int(payload[0]["count"])
        except Exception as exc:
            logger.warning("No se pudo consultar el total de Socrata: %s", exc)
        return None

    async def get_dataset_limit(
        self,
        dataset_id: str,
        limit: int,
        where: str | None = None,
    ):
        """Descarga hasta ``limit`` registros del dataset solicitado.

        Usa ``$order="fecha_accidente, :id"`` para garantizar un orden estable
        entre paginas incluso cuando hay multiples accidentes el mismo dia.

        Parametros:
        - ``dataset_id``: identificador del recurso en Socrata.
        - ``limit``: numero maximo de filas a recuperar.
        - ``where``: clausula SoQL opcional para filtrar en el servidor.
        """
        url_final = self._resolver_url(dataset_id)

        offset = 0
        data = []

        while offset < limit:
            paso = min(1000, limit - offset)
            params = {
                "$limit": paso,
                "$offset": offset,
                "$order": "fecha_accidente, :id",
            }
            if where:
                params["$where"] = where

            try:
                response = await self.client.get(url_final, params=params)
                response.raise_for_status()

                lote = response.json()
                data.extend(lote)
                offset += paso

                if len(lote) < paso:
                    break
            except Exception as exc:
                logger.error("Error al bajar datos de la API: %s", exc)
                print(f"Error al bajar datos de la API: {exc}")
                break

        return data

    async def close(self):
        """Cierra el cliente HTTP al finalizar la consulta."""
        await self.client.aclose()
