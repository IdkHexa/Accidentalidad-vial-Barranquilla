"""Modelos de datos del proyecto.

Define la estructura tipada con la que se representan los registros cargados
desde la API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from data.direccion_parser import parsear_texto, DireccionParseada


class AccidenteDTO(BaseModel):
    """
    DTO que representa un registro de accidente validado.

    Campos principales:
    - `FECHA_ACCIDENTE`, `HORA_ACCIDENTE`: datos de fecha y hora.
    - `GRAVEDAD_ACCIDENTE`, `CLASE_ACCIDENTE`: clasificaciones del registro.
    - `SITIO_EXACTO_ACCIDENTE`: direccion convertida a `DireccionParseada`.
    - `LATITUD`, `LONGITUD`: coordenadas del punto.
    """

    FECHA_ACCIDENTE: str = Field(..., alias="fecha_accidente")
    HORA_ACCIDENTE: str = Field(..., alias="hora_accidente")
    GRAVEDAD_ACCIDENTE: str = Field(..., alias="gravedad_accidente")
    CLASE_ACCIDENTE: str = Field(..., alias="clase_accidente")
    AÑO_ACCIDENTE: int = Field(..., alias="a_o_accidente")
    MES_ACCIDENTE: str = Field(..., alias="mes_accidente")
    DIA_ACCIDENTE: str = Field(..., alias="dia_accidente")

    # Valores opcionales que pueden faltar en la fuente original.
    SITIO_EXACTO_ACCIDENTE: Optional[DireccionParseada] = Field(default=None, alias="sitio_exacto_accidente")
    CANT_HERIDOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_heridos_en_sitio_accidente")
    CANT_MUERTOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_muertos_en_sitio_accidente")
    CANTIDAD_ACCIDENTES: int = Field(default=0, alias="cantidad_accidentes")

    LATITUD: Optional[float] = Field(default=None, alias="latitud")
    LONGITUD: Optional[float] = Field(default=None, alias="longitud")

    @field_validator("MES_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_mes(cls, v):
        """Normaliza el mes para dejar una sola forma de escritura."""
        if isinstance(v, str):
            mes = v.strip().upper()
            traducciones = {
                "JANUARY": "ENERO",
                "FEBRUARY": "FEBRERO",
                "MARCH": "MARZO",
                "APRIL": "ABRIL",
                "MAY": "MAYO",
                "JUNE": "JUNIO",
                "JULY": "JULIO",
                "AUGUST": "AGOSTO",
                "SEPTEMBER": "SEPTIEMBRE",
                "OCTOBER": "OCTUBRE",
                "NOVEMBER": "NOVIEMBRE",
                "DECEMBER": "DICIEMBRE",
            }
            return traducciones.get(mes, mes)
        return str(v)

    @field_validator("DIA_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_dia(cls, v):
        """Normaliza el nombre del dia de la semana."""
        if isinstance(v, str):
            dia = v.strip().upper()
            traducciones = {
                "MON": "LUNES",
                "TUE": "MARTES",
                "WED": "MIERCOLES",
                "THU": "JUEVES",
                "FRI": "VIERNES",
                "SAT": "SABADO",
                "SUN": "DOMINGO",
            }
            return traducciones.get(dia, dia)
        return str(v)

    @field_validator(
        "CANT_MUERTOS_EN_SITIO_ACCIDENTE",
        "CANT_HERIDOS_EN_SITIO_ACCIDENTE",
        "CANTIDAD_ACCIDENTES",
        mode="before",
    )
    @classmethod
    def asegurar_entero(cls, v):
        """Convierte a entero los valores numericos recibidos como texto o decimal."""
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0

    @field_validator("SITIO_EXACTO_ACCIDENTE", mode="before")
    @classmethod
    def parsear_direccion(cls, v):
        """Transforma la direccion original a una estructura uniforme."""
        if isinstance(v, str):
            return parsear_texto(v)
        return v
