from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Esta clase sirve para darle estructura a los datos que bajamos
class AccidenteDTO(BaseModel):
    # Campos obligatorios (si faltan, el registro no sirve)
    FECHA_ACCIDENTE: str = Field(..., alias="fecha_accidente")
    HORA_ACCIDENTE: str = Field(..., alias="hora_accidente")
    GRAVEDAD_ACCIDENTE: str = Field(..., alias="gravedad_accidente")
    CLASE_ACCIDENTE: str = Field(..., alias="clase_accidente")
    AÑO_ACCIDENTE: int = Field(..., alias="a_o_accidente") # El alias es por cómo viene en la API
    MES_ACCIDENTE: str = Field(..., alias="mes_accidente")
    DIA_ACCIDENTE: str = Field(..., alias="dia_accidente")

    # Campos opcionales (tienen un valor por defecto por si vienen vacíos)
    SITIO_EXACTO_ACCIDENTE: str = Field(default="N/A", alias="sitio_exacto_accidente")
    CANT_HERIDOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_heridos_en_sitio_accidente")
    CANT_MUERTOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_muertos_en_sitio_accidente")
    CANTIDAD_ACCIDENTES: int = Field(default=0, alias="cantidad_accidentes")

    # Campos de ubicación
    LATITUD: Optional[float] = Field(default=None, alias="latitud")
    LONGITUD: Optional[float] = Field(default=None, alias="longitud")

    # Función para limpiar el nombre del mes y traducirlo
    @field_validator("MES_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_mes(cls, v):
        if isinstance(v, str):
            # Pasamos a mayúsculas y quitamos espacios
            mes = v.strip().upper()
            # Diccionario para traducir a español
            traducciones = {
                "JANUARY": "ENERO", "FEBRUARY": "FEBRERO", "MARCH": "MARZO",
                "APRIL": "ABRIL", "MAY": "MAYO", "JUNE": "JUNIO",
                "JULY": "JULIO", "AUGUST": "AGOSTO", "SEPTEMBER": "SEPTIEMBRE",
                "OCTOBER": "OCTUBRE", "NOVEMBER": "NOVIEMBRE", "DECEMBER": "DICIEMBRE"
            }
            return traducciones.get(mes, mes)
        return str(v)

    # Función para limpiar el día (la API manda nombres cortos como TUE)
    @field_validator("DIA_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_dia(cls, v):
        if isinstance(v, str):
            dia = v.strip().upper()
            traducciones = {
                "MON": "LUNES", "TUE": "MARTES", "WED": "MIERCOLES",
                "THU": "JUEVES", "FRI": "VIERNES", "SAT": "SABADO", "SUN": "DOMINGO"
            }
            return traducciones.get(dia, dia)
        return str(v)

    # Función para que los números siempre sean enteros (por si vienen como 1.0)
    @field_validator("CANT_MUERTOS_EN_SITIO_ACCIDENTE", "CANT_HERIDOS_EN_SITIO_ACCIDENTE", "CANTIDAD_ACCIDENTES", mode="before")
    @classmethod
    def asegurar_entero(cls, v):
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0