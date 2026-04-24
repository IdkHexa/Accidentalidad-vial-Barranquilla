from enum import Enum
import re
import dataclasses

MAPEO_DIRECCIONES = {
    'CL': 'Calle',
    'CR': 'Carrera',
    'CRA': 'Carrera',
    'AV': 'Avenida',
    'DG': 'Diagonal',
    'TV': 'Transversal',
    'KR': 'Carrera',
    'KRA': 'Carrera',
    'TRV': 'Transversal',
    'TR': 'Transversal',
    'CLLE': 'Calle',
    'CALLE': 'Calle',
    'CARRERA': 'Carrera',
    'AVENIDA': 'Avenida',
    'DIAGONAL': 'Diagonal',
    'TRANSVERSAL': 'Transversal',
}

@dataclasses.dataclass
class DireccionParseada:
    tipo_via: str | None = None
    numero_via: str | None = None
    numero_cruce: str | None = None
    complemento: str | None = None
    interseccion: str | None = None
    raw: str | None = None  
    
class TipoDireccion (Enum):
    EXACTA = "exacta"
    INTERSECCION = "interseccion"
    REFERENCIA = "referencia"
    CORREDOR = "corredor" # KM, Vías
    INSUFICIENTE = "insuficiente"

def limpiar_direccion(direccion: str) -> str:
    direccion = re.sub(r'[.,#\-]', ' ', direccion)

    for abr, full in MAPEO_DIRECCIONES.items():
        direccion = re.sub(r'\b' + abr + r'\b', full, direccion, flags=re.IGNORECASE)
    return " ".join(direccion.split())

PATRON_ESTANDAR = re.compile(
    r'^(?P<tipo>Calle|Carrera|Avenida|Diagonal|Transversal)' 
    r'\s+(?P<via>\d+[a-zA-Z]?)'                              
    r'\s+(?P<cruce>\d+[a-zA-Z]?)'                            
    r'\s+(?P<placa>\d+)'                                     
    r'$', re.IGNORECASE)

def parsear_texto(direccion: str) -> DireccionParseada:
    texto_limpio = limpiar_direccion(direccion)
    if " CON " in texto_limpio:
        partes = texto_limpio.split(" CON ")
        return DireccionParseada(
            tipo_via=partes[0].strip(), 
            interseccion=partes[1].strip(),
            raw=direccion
        )
    match = PATRON_ESTANDAR.match(texto_limpio)
    if match:
        return DireccionParseada(
            tipo_via=match.group("tipo"),
            numero_via=match.group("via"),
            numero_cruce=match.group("cruce"),
            complemento=match.group("placa"),
            raw=direccion
        )
    return DireccionParseada(raw=direccion)

if __name__ == "__main__":
    prueba_1 = parsear_texto("CL 45 # 20 - 10")
    prueba_2 = parsear_texto("KRA 43 CON CALLE 84")
    prueba_3 = parsear_texto("Direccion Inventada 123") # Debería devolver objeto vacío
    
    print(f"Estándar: {prueba_1.tipo_via} {prueba_1.numero_via}")
    print(f"Intersección: {prueba_2.tipo_via} con {prueba_2.interseccion}")
    print(f"Fallida (Raw): {prueba_3.raw}")
