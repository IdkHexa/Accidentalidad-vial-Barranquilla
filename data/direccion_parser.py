from enum import Enum
import re
import dataclasses

# Diccionario para convertir abreviaturas (CL, CRA) en palabras completas (Calle, Carrera)
# Esto ayuda a que Google entienda mejor la dirección
MAPEO_DIRECCIONES = {
    'CL': 'Calle',
    'CLL': 'Calle',
    'CR': 'Carrera',
    'KRA': 'Carrera',
    'KR': 'Carrera',
    'CRA': 'Carrera',
    'AV': 'Avenida',
    'DIAG': 'Diagonal',
    'DG': 'Diagonal',
    'TV': 'Transversal',
    'TRV': 'Transversal',
    'TR': 'Transversal',
    'CLLE': 'Calle',
    'CALLE': 'Calle',
    'CARRERA': 'Carrera',
    'AVENIDA': 'Avenida',
    'DIAGONAL': 'Diagonal',
    'VIA': 'Via',
    'TRANSVERSAL': 'Transversal',
}

# Usamos un dataclass para guardar los pedacitos de la dirección de forma organizada
@dataclasses.dataclass
class DireccionParseada:
    tipo_via: str | None = None      # Ej: Calle, Carrera
    numero_via: str | None = None    # Ej: 45, 45B
    numero_cruce: str | None = None  # Ej: 20
    complemento: str | None = None   # Ej: 10 (la placa)
    interseccion: str | None = None  # Ej: Carrera 46
    raw: str | None = None           # La dirección original sin procesar

    # Esta función se activa cuando hacemos str(objeto)
    # Sirve para armar la "pregunta" que le enviaremos a Google
    def __str__(self):
        # Caso 1: Dirección estándar (Calle 45 20 10)
        if self.tipo_via and self.numero_via and self.numero_cruce:
            query = f"{self.tipo_via} {self.numero_via} {self.numero_cruce}"
            if self.complemento:
                query += f" - {self.complemento}"
            return f"{query}, Barranquilla, Colombia"
            
        # Caso 2: Intersección (Calle 72 con Carrera 46)
        if self.tipo_via and self.interseccion:
            return f"{self.tipo_via} con {self.interseccion}, Barranquilla, Colombia"
            
        # Caso 3: Si no pudimos parsearla, mandamos lo que tengamos + la ciudad
        if self.raw:
            return f"{self.raw}, Barranquilla, Colombia"
            
        return "" 

# Enumeración para clasificar qué tan buena es la dirección
class TipoDireccion (Enum):
    EXACTA = "exacta"
    INTERSECCION = "interseccion"
    REFERENCIA = "referencia"
    CORREDOR = "corredor" # KM, Vías
    INSUFICIENTE = "insuficiente"

# Función para limpiar el texto antes de intentar entenderlo
def limpiar_direccion(direccion: str) -> str:
    # 1. Pasamos todo a MAYÚSCULAS para no tener líos de comparación
    direccion = direccion.upper()
    # 2. Quitamos símbolos comunes y los cambiamos por espacios
    direccion = re.sub(r'[.,#\-]', ' ', direccion)

    # 3. Quitamos palabras que son "ruido" y no ayudan a la ubicación
    ruido = ['FRENTE', 'BARR', 'BARRIO', 'ESQUINA', 'ESQ', 'NO', 'NUMERO', 'AL', 'DEL']
    for r in ruido:
        direccion = re.sub(r'\b' + r + r'\b', '', direccion)

    # 4. Cambiamos abreviaturas por palabras completas usando el diccionario de arriba
    for abr, full in MAPEO_DIRECCIONES.items():
        direccion = re.sub(r'\b' + abr + r'\b', full, direccion)
        
    # 5. Quitamos espacios dobles que hayan quedado
    return " ".join(direccion.split())

# El "cerebro" del parser: un Regex que busca Tipo, Vía, Cruce y Placa
# El [A-Z]? es para atrapar letras como la de "Calle 45B"
PATRON_ESTANDAR = re.compile(
    r'(?P<tipo>Calle|Carrera|Avenida|Diagonal|Transversal|Via)' 
    r'\s+(?P<via>\d+[A-Z]?)'                                     
    r'(?:\s+(?P<cruce>\d+[A-Z]?))?'                             
    r'(?:\s+(?P<placa>\d+))?'                                   
    r'.*$', re.IGNORECASE)

# Función principal que recibe un texto y devuelve un objeto DireccionParseada
def parsear_texto(direccion: str) -> DireccionParseada:
    # Primero limpiamos el texto
    texto_limpio = limpiar_direccion(direccion)
    
    # Intentamos ver si es una intersección (buscando "CON" o "Y")
    for conector in [" CON ", " Y "]:
        if conector in texto_limpio:
            partes = texto_limpio.split(conector)
            return DireccionParseada(
                tipo_via=partes[0].strip(), 
                interseccion=partes[1].strip(),
                raw=direccion
            )

    # Si no es intersección, intentamos el patrón estándar (Calle 45...)
    # Usamos search para encontrar la dirección aunque haya texto antes
    match = PATRON_ESTANDAR.search(texto_limpio)
    if match:
        return DireccionParseada(
            tipo_via=match.group("tipo"),
            numero_via=match.group("via"),
            numero_cruce=match.group("cruce"),
            complemento=match.group("placa"),
            raw=direccion
        )
    
    # Si nada funcionó, devolvemos el objeto solo con el raw original
    return DireccionParseada(raw=direccion)

# Bloque de prueba para cuando corremos este archivo directamente
if __name__ == "__main__":
    prueba_1 = parsear_texto("CL 45 # 20 - 10")
    prueba_2 = parsear_texto("KRA 43 CON CALLE 84")
    prueba_3 = parsear_texto("Direccion Inventada 123")
    
    print(f"Estándar: {prueba_1.tipo_via} {prueba_1.numero_via}")
    print(f"Intersección: {prueba_2.tipo_via} con {prueba_2.interseccion}")
    print(f"Fallida (Raw): {prueba_3.raw}")
