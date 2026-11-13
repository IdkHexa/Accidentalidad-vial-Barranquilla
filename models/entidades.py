"""Modelos de datos del proyecto.

Define la estructura tipada con la que se representan los registros cargados
desde la API publica de Socrata o ingresados manualmente.
"""

from typing import Optional
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator

from data.direccion_parser import DireccionParseada, parsear_texto


def _normalizar_texto(texto: str) -> str:
    """Convierte a mayusculas y elimina tildes para unificar categorias."""
    limpio = texto.strip().upper()
    descompuesto = unicodedata.normalize("NFD", limpio)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


class AccidenteDTO(BaseModel):
    """DTO que representa un registro de accidente validado.

    Campos principales:
    - ``FECHA_ACCIDENTE``, ``HORA_ACCIDENTE``: datos de fecha y hora.
    - ``GRAVEDAD_ACCIDENTE``, ``CLASE_ACCIDENTE``: clasificaciones del registro.
    - ``SITIO_EXACTO_ACCIDENTE``: direccion convertida a ``DireccionParseada``.
    - ``LATITUD``, ``LONGITUD``: coordenadas del punto.
    """

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    FECHA_ACCIDENTE: str = Field(..., alias="fecha_accidente")
    HORA_ACCIDENTE: str = Field(..., alias="hora_accidente")
    GRAVEDAD_ACCIDENTE: str = Field(..., alias="gravedad_accidente")
    CLASE_ACCIDENTE: str = Field(..., alias="clase_accidente")
    AÑO_ACCIDENTE: int = Field(..., alias="a_o_accidente")
    MES_ACCIDENTE: str = Field(..., alias="mes_accidente")
    DIA_ACCIDENTE: str = Field(..., alias="dia_accidente")

    # Valores opcionales que pueden faltar en la fuente original.
    SITIO_EXACTO_ACCIDENTE: Optional[DireccionParseada] = Field(
        default=None, alias="sitio_exacto_accidente"
    )
    CANT_HERIDOS_EN_SITIO_ACCIDENTE: int = Field(
        default=0, ge=0, alias="cant_heridos_en_sitio_accidente"
    )
    CANT_MUERTOS_EN_SITIO_ACCIDENTE: int = Field(
        default=0, ge=0, alias="cant_muertos_en_sitio_accidente"
    )
    CANTIDAD_ACCIDENTES: int = Field(
        default=1, ge=0, alias="cantidad_accidentes"
    )

    LATITUD: Optional[float] = Field(default=None, alias="latitud")
    LONGITUD: Optional[float] = Field(default=None, alias="longitud")

    @field_validator("MES_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_mes(cls, v):
        """Normaliza el mes a su nombre completo en espanol sin tildes."""
        if v is None:
            raise ValueError("El mes del accidente no puede ser nulo")
        mes = _normalizar_texto(str(v))
        traducciones = {
            "JANUARY": "ENERO",
            "JAN": "ENERO",
            "ENE": "ENERO",
            "FEBRUARY": "FEBRERO",
            "FEB": "FEBRERO",
            "MARCH": "MARZO",
            "MAR": "MARZO",
            "APRIL": "ABRIL",
            "APR": "ABRIL",
            "ABR": "ABRIL",
            "MAY": "MAYO",
            "JUNE": "JUNIO",
            "JUN": "JUNIO",
            "JULY": "JULIO",
            "JUL": "JULIO",
            "AUGUST": "AGOSTO",
            "AUG": "AGOSTO",
            "AGO": "AGOSTO",
            "SEPTEMBER": "SEPTIEMBRE",
            "SEP": "SEPTIEMBRE",
            "OCTOBER": "OCTUBRE",
            "OCT": "OCTUBRE",
            "NOVEMBER": "NOVIEMBRE",
            "NOV": "NOVIEMBRE",
            "DECEMBER": "DICIEMBRE",
            "DEC": "DICIEMBRE",
            "DIC": "DICIEMBRE",
        }
        return traducciones.get(mes, mes)

    @field_validator("DIA_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_dia(cls, v):
        """Normaliza el dia de la semana a formato canonico sin tildes."""
        if v is None:
            raise ValueError("El dia del accidente no puede ser nulo")
        dia = _normalizar_texto(str(v))
        traducciones = {
            "MON": "LUNES",
            "MONDAY": "LUNES",
            "LUN": "LUNES",
            "TUE": "MARTES",
            "TUESDAY": "MARTES",
            "MAR": "MARTES",
            "WED": "MIERCOLES",
            "WEDNESDAY": "MIERCOLES",
            "MIE": "MIERCOLES",
            "THU": "JUEVES",
            "THURSDAY": "JUEVES",
            "JUE": "JUEVES",
            "FRI": "VIERNES",
            "FRIDAY": "VIERNES",
            "VIE": "VIERNES",
            "SAT": "SABADO",
            "SATURDAY": "SABADO",
            "SAB": "SABADO",
            "SUN": "DOMINGO",
            "SUNDAY": "DOMINGO",
            "DOM": "DOMINGO",
        }
        return traducciones.get(dia, dia)

    @field_validator(
        "CANT_MUERTOS_EN_SITIO_ACCIDENTE",
        "CANT_HERIDOS_EN_SITIO_ACCIDENTE",
        "CANTIDAD_ACCIDENTES",
        mode="before",
    )
    @classmethod
    def asegurar_entero(cls, v):
        """Convierte a entero no negativo los valores recibidos como texto o decimal."""
        try:
            return max(0, int(float(v)))
        except (ValueError, TypeError):
            return 0

    @field_validator("SITIO_EXACTO_ACCIDENTE", mode="before")
    @classmethod
    def parsear_direccion(cls, v):
        """Transforma la direccion original a una estructura uniforme."""
        if isinstance(v, str):
            return parsear_texto(v)
        return v
