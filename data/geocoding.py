"""Modulo de geocodificacion con cache local.

Consulta coordenadas para una direccion y guarda resultados repetidos en un
archivo JSON para no repetir solicitudes externas. Las escrituras usan
reemplazo atomico y bloqueo de hilos para evitar corrupcion del cache.
"""

import json
import os
from pathlib import Path
import tempfile
import threading

import googlemaps

from config import GOOGLE_MAPS_KEY

from .direccion_parser import DireccionParseada


class GeoCoder:
    """Gestiona la consulta de coordenadas y el uso seguro del cache local.

    ``cache_file`` indica donde se guardan las respuestas ya obtenidas.
    """

    def __init__(self, cache_file="data/geocache.json"):
        """Prepara el cache local y, si hay llave, el cliente de Google Maps.

        Parametros:
        - ``cache_file``: ruta del archivo JSON donde se guardan las coordenadas
          ya consultadas. Si ``GOOGLE_MAPS_KEY`` no esta definida, ``self.gmaps``
          queda en ``None`` y solo se resuelven direcciones ya cacheadas.
        """
        self.cache_file = cache_file
        self._lock = threading.Lock()
        self.cache = self._cargar_cache()
        self._pendientes = 0
        if GOOGLE_MAPS_KEY:
            self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY, timeout=10)
        else:
            self.gmaps = None

    def _cargar_cache(self):
        """Lee el archivo JSON del cache si ya existe."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _guardar_cache(self):
        """Persiste el cache en disco de forma atomica mediante archivo temporal."""
        ruta = Path(self.cache_file)
        directorio = ruta.parent if ruta.parent != Path("") else Path(".")
        os.makedirs(directorio, exist_ok=True)

        fd, ruta_tmp = tempfile.mkstemp(
            dir=str(directorio), prefix=".geocache_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4)
            os.replace(ruta_tmp, self.cache_file)
        except Exception:
            if os.path.exists(ruta_tmp):
                os.remove(ruta_tmp)
            raise

    def obtener_coordenadas(
        self, direccion: DireccionParseada
    ) -> tuple[float, float] | None:
        """Busca coordenadas para la direccion recibida.

        Retorna una tupla ``(latitud, longitud)`` o ``None``.
        """
        query = str(direccion)
        if not query:
            return None

        # Usa primero el cache antes de verificar ``self.gmaps`` para seguir
        # resolviendo direcciones historicas aunque no exista llave de Google.
        with self._lock:
            if query in self.cache:
                return tuple(self.cache[query])

        if self.gmaps is None:
            return None

        try:
            result = self.gmaps.geocode(query)
            if result:
                location = result[0]["geometry"]["location"]
                coords = (location["lat"], location["lng"])

                with self._lock:
                    self.cache[query] = coords
                    self._pendientes += 1
                    if self._pendientes >= 500:
                        self._guardar_cache()
                        self._pendientes = 0
                return coords

        except Exception as e:
            mensaje = str(e)
            print(f"Error en Google Maps para '{query}': {mensaje}")
            if "REQUEST_DENIED" in mensaje:
                # Evita cientos de reintentos fallidos si la llave no tiene facturacion.
                self.gmaps = None

        return None

    def guardar(self):
        """Persiste las coordenadas pendientes en el archivo de cache."""
        with self._lock:
            if self._pendientes > 0:
                self._guardar_cache()
                self._pendientes = 0
