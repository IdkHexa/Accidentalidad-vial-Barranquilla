from geopy.geocoders import Nominatim
from .direccion_parser import DireccionParseada

class GeoCoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="AccidentalidadBarranquilla_DACAD")
    
    def obtener_coordenadas(self, direccion: DireccionParseada) -> tuple[float, float] | None:
        if direccion.tipo_via and direccion.numero_via:
            query = f"{direccion.tipo_via} {direccion.numero_via} and {direccion.interseccion}, Barranquilla, Colombia"
        elif direccion.numero_cruce and direccion.complemento:
            
            query = f"{direccion.tipo_via} {direccion.numero_via}, Barranquilla, Colombia"
        location = self.geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude
        return None