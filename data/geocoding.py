"""Modulo de geocodificacion con cache local.

Consulta coordenadas para una direccion y guarda resultados repetidos en un
archivo JSON para no hacer la misma solicitud varias veces.
"""

import json
import os

import googlemaps

from config import GOOGLE_MAPS_KEY

from .direccion_parser import DireccionParseada


class GeoCoder:
    """
    Gestiona la consulta de coordenadas y el uso del cache local.

    `cache_file` indica donde se guardan las respuestas ya obtenidas.
    """

    def __init__(self, cache_file="data/geocache.json"):
        """Prepara el cache local y, si hay llave, el cliente de Google Maps.

        ``cache_file`` indica la ruta del archivo JSON donde se guardan
        las coordenadas ya consultadas.  Si ``GOOGLE_MAPS_KEY`` no esta
        definida en el entorno, ``self.gmaps`` se deja en ``None`` y el
        metodo ``obtener_coordenadas()`` retorna ``None`` sin intentar la
        llamada a la API.
        """
        self.cache_file = cache_file
        self.cache = self._cargar_cache()
        self._pendientes = 0
        if GOOGLE_MAPS_KEY:
            self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        else:
            self.gmaps = None

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

    def obtener_coordenadas(
        self, direccion: DireccionParseada
    ) -> tuple[float, float] | None:
        """
        Busca coordenadas para la direccion recibida.

        Retorna una tupla `(latitud, longitud)` o `None`.
        """
        query = str(direccion)
        if not query:
            return None

        # Usa primero el cache para evitar consultas repetidas.
        # Esta consulta debe ir antes de comprobar ``self.gmaps`` porque
        # el cache persiste coordenadas obtenidas en ejecuciones previas
        # y debe seguir siendo util aunque la llave de Google falte.
        if query in self.cache:
            return tuple(self.cache[query])

        if self.gmaps is None:
            return None

        try:
            result = self.gmaps.geocode(query)
            if result:
                # Extrae la ubicacion del primer resultado devuelto.
                location = result[0]["geometry"]["location"]
                coords = (location["lat"], location["lng"])

                self.cache[query] = coords
                self._pendientes += 1
                if self._pendientes >= 500:
                    self._guardar_cache()
                    self._pendientes = 0
                return coords

        except Exception as e:
            print(f"Error en Google Maps para '{query}': {e}")

        return None

    def guardar(self):
        """Persiste las coordenadas pendientes en el archivo de cache.

        Se llama al finalizar una tanda de geocodificaciones para
        asegurar que ninguna coordenada quede solo en memoria.
        """
        if self._pendientes > 0:
            self._guardar_cache()
            self._pendientes = 0
