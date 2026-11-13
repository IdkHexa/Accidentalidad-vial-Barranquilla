"""Parser de direcciones usado durante la transformacion de datos.

Convierte direcciones en texto libre a una estructura mas uniforme para
alimentar tanto al geocodificador como a las consultas de ubicacion.
"""

import dataclasses
from enum import Enum
import re

# Relaciona abreviaturas frecuentes con una forma estandar.
MAPEO_DIRECCIONES = {
    "CL": "Calle",
    "CLL": "Calle",
    "CR": "Carrera",
    "KRA": "Carrera",
    "KR": "Carrera",
    "CRA": "Carrera",
    "AV": "Avenida",
    "DIAG": "Diagonal",
    "DG": "Diagonal",
    "TV": "Transversal",
    "TRV": "Transversal",
    "TR": "Transversal",
    "CLLE": "Calle",
    "CALLE": "Calle",
    "CARRERA": "Carrera",
    "AVENIDA": "Avenida",
    "VIA": "Via",
    "DIAGONAL": "Diagonal",
    "TRANSVERSAL": "Transversal",
}


@dataclasses.dataclass
class DireccionParseada:
    """Guarda una direccion separada en partes.

    Campos principales:
    - ``tipo_via``: nombre de la via principal.
    - ``numero_via``: numero de la via principal.
    - ``numero_cruce``: numero de la via cruzada.
    - ``complemento``: numero final o placa.
    - ``interseccion``: segunda via cuando la direccion viene como cruce.
    - ``raw``: texto original recibido.
    """

    tipo_via: str | None = None
    numero_via: str | None = None
    numero_cruce: str | None = None
    complemento: str | None = None
    interseccion: str | None = None
    raw: str | None = None

    def __str__(self):
        """Convierte el objeto a una cadena util para la consulta geocodificada."""
        if self.tipo_via and self.numero_via and self.numero_cruce:
            query = f"{self.tipo_via} {self.numero_via} {self.numero_cruce}"
            if self.complemento:
                query += f" - {self.complemento}"
            return f"{query}, Barranquilla, Colombia"

        if self.tipo_via and self.interseccion:
            return f"{self.tipo_via} con {self.interseccion}, Barranquilla, Colombia"

        if self.raw and self.raw.strip():
            return f"{self.raw.strip()}, Barranquilla, Colombia"

        return ""


class TipoDireccion(Enum):
    """Clasifica la forma general de una direccion."""

    EXACTA = "exacta"
    INTERSECCION = "interseccion"
    REFERENCIA = "referencia"
    CORREDOR = "corredor"
    INSUFICIENTE = "insuficiente"


def limpiar_direccion(direccion: str | None) -> str:
    """Normaliza el texto antes del parseo eliminando ruido y tildes comunes.

    ``direccion`` es la cadena original tomada del dataset (puede ser ``None``).
    """
    if not direccion or not isinstance(direccion, str):
        return ""

    texto = direccion.upper().replace("VÍA", "VIA")
    texto = re.sub(r"[.,#\-]", " ", texto)

    # Elimina palabras que no aportan a la direccion principal.
    ruido = ["FRENTE", "BARR", "BARRIO", "ESQUINA", "ESQ", "NO", "NUMERO", "AL", "DEL"]
    for palabra in ruido:
        texto = re.sub(r"\b" + palabra + r"\b", "", texto)

    for abr, full in MAPEO_DIRECCIONES.items():
        texto = re.sub(r"\b" + abr + r"\b", full, texto)

    return " ".join(texto.split())


# Expresion regular para reconocer el formato mas comun de direccion.
PATRON_ESTANDAR = re.compile(
    r"(?P<tipo>Calle|Carrera|Avenida|Diagonal|Transversal|Via)"
    r"\s+(?P<via>\d+(?:[A-Z])?(?:\s+BIS)?)"
    r"(?:\s+(?P<cruce>\d+(?:[A-Z])?(?:\s+BIS)?))?"
    r"(?:\s+(?P<placa>\d+))?"
    r".*$",
    re.IGNORECASE,
)


def parsear_texto(direccion: str | None) -> DireccionParseada:
    """Interpreta una direccion y devuelve un objeto estructurado.

    El proceso limpia el texto, busca intersecciones (partiendo solo por la
    primera ocurrencia del conector para no perder datos) y luego intenta
    aplicar el patron estandar.
    """
    if not direccion or not isinstance(direccion, str) or not direccion.strip():
        return DireccionParseada(raw=None)

    texto_limpio = limpiar_direccion(direccion)

    for conector in [" CON ", " Y "]:
        if conector in texto_limpio:
            partes = texto_limpio.split(conector, 1)
            return DireccionParseada(
                tipo_via=partes[0].strip(),
                interseccion=partes[1].strip(),
                raw=direccion,
            )

    match = PATRON_ESTANDAR.search(texto_limpio)
    if match:
        return DireccionParseada(
            tipo_via=match.group("tipo"),
            numero_via=match.group("via"),
            numero_cruce=match.group("cruce"),
            complemento=match.group("placa"),
            raw=direccion,
        )

    # Si no hay coincidencia, se conserva el texto original.
    return DireccionParseada(raw=direccion)


if __name__ == "__main__":
    # Casos simples para comprobar la salida del parser.
    prueba_1 = parsear_texto("CL 45 # 20 - 10")
    prueba_2 = parsear_texto("KRA 43 CON CALLE 84")
    prueba_3 = parsear_texto("Direccion Inventada 123")

    print(f"Estandar: {prueba_1.tipo_via} {prueba_1.numero_via}")
    print(f"Interseccion: {prueba_2.tipo_via} con {prueba_2.interseccion}")
    print(f"Fallida (Raw): {prueba_3.raw}")
