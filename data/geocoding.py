"""Modulo de geocodificacion con cache local.

Consulta coordenadas para una direccion y guarda resultados repetidos en un
archivo JSON para no hacer la misma solicitud varias veces.
"""

import googlemaps
import json
import os
from .direccion_parser import DireccionParseada
from config import GOOGLE_MAPS_KEY


class GeoCoder:
    """
    Gestiona la consulta de coordenadas y el uso del cache local.

    `cache_file` indica donde se guardan las respuestas ya obtenidas.
    """

    def __init__(self, cache_file="data/geocache.json"):
        # Crea el cliente del servicio externo y carga el cache existente.
        self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        self.cache_file = cache_file
        self.cache = self._cargar_cache()

    def _cargar_cache(self):
        """Lee el archivo JSON del cache si ya existe."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _guardar_cache(self):
        """Escribe en disco el contenido actual del cache."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)

    def obtener_coordenadas(self, direccion: DireccionParseada) -> tuple[float, float] | None:
        """
        Busca coordenadas para la direccion recibida.

        Retorna una tupla `(latitud, longitud)` o `None`.
        """
        query = str(direccion)
        if not query:
            return None

        # Usa primero el cache para evitar consultas repetidas.
        if query in self.cache:
            return tuple(self.cache[query])

        try:
            result = self.gmaps.geocode(query)
            if result:
                # Extrae la ubicacion del primer resultado devuelto.
                location = result[0]["geometry"]["location"]
                coords = (location["lat"], location["lng"])

                self.cache[query] = coords
                self._guardar_cache()
                return coords

        except Exception as e:
            print(f"Error en Google Maps para '{query}': {e}")

        return None
