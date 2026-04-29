import googlemaps
import json
import os
from .direccion_parser import DireccionParseada
from config import GOOGLE_MAPS_KEY

# Esta clase es la que se encarga de hablar con Google y manejar el caché
class GeoCoder:
    def __init__(self, cache_file="data/geocache.json"):
        # Conectamos con Google usando nuestra llave secreta
        self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        # Guardamos la ruta del archivo donde guardaremos las consultas para no repetir
        self.cache_file = cache_file
        # Al empezar, cargamos lo que ya tenemos guardado en el archivo
        self.cache = self._cargar_cache()
    
    # Función para leer el archivo de caché (el "baúl" de direcciones)
    def _cargar_cache(self):
        # Si el archivo existe en la carpeta...
        if os.path.exists(self.cache_file):
            # Lo abrimos y lo cargamos como un diccionario de Python
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Si no existe, devolvemos un diccionario vacío para empezar de cero
        return {}

    # Función para guardar el diccionario en el archivo JSON
    def _guardar_cache(self):
        # Intentamos guardar los datos para no perderlos si el programa se cierra
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            # Lo guardamos con sangría (indent=4) para que sea fácil de leer por humanos
            json.dump(self.cache, f, ensure_ascii=False, indent=4)

    def obtener_coordenadas(self, direccion: DireccionParseada) -> tuple[float, float] | None:
        # Convertimos el objeto de dirección en un texto que Google entienda (usando su __str__)
        query = str(direccion)
        if not query: return None
        
        # Si ya buscamos esta dirección antes, la sacamos del caché (ahorra dinero)
        if query in self.cache:
            # Convertimos la lista del JSON de vuelta a una tupla de Python
            return tuple(self.cache[query])

        # Si no está en el caché, le preguntamos a Google (con cuidado de errores)
        try:
            # Llamamos al servicio de Google Maps
            result = self.gmaps.geocode(query)
            
            # Si Google encontró algo...
            if result:
                # Navegamos por el JSON gigante que devuelve Google para hallar latitud y longitud
                location = result[0]['geometry']['location']
                coords = (location['lat'], location['lng'])
                
                # Guardamos el resultado en nuestro "baúl" para la próxima vez
                self.cache[query] = coords
                self._guardar_cache() # Lo escribimos en el disco duro de una vez
                
                return coords
                
        except Exception as e:
            # Si el internet falla o la llave está mal, avisamos por consola
            print(f"Error en Google Maps para '{query}': {e}")
            
        return None
