from pydantic import BaseModel, Field, field_validator
from typing import Optional
from data.direccion_parser import parsear_texto, DireccionParseada

# Esta clase es un DTO (Data Transfer Object). Sirve para que los datos 
# que bajamos de Internet tengan una estructura fija y limpia en nuestro código.
class AccidenteDTO(BaseModel):
    # Definimos los campos que esperamos de la API de Barranquilla.
    # El 'alias' es el nombre real que viene en el JSON de la API.
    FECHA_ACCIDENTE: str = Field(..., alias="fecha_accidente")
    HORA_ACCIDENTE: str = Field(..., alias="hora_accidente")
    GRAVEDAD_ACCIDENTE: str = Field(..., alias="gravedad_accidente")
    CLASE_ACCIDENTE: str = Field(..., alias="clase_accidente")
    AÑO_ACCIDENTE: int = Field(..., alias="a_o_accidente") # La API usa 'a_o' para la 'ñ'
    MES_ACCIDENTE: str = Field(..., alias="mes_accidente")
    DIA_ACCIDENTE: str = Field(..., alias="dia_accidente")

    # Campos opcionales: Si no vienen, Pydantic les pone el valor de 'default'
    # SITIO_EXACTO_ACCIDENTE guardará el objeto que creamos con nuestro parser
    SITIO_EXACTO_ACCIDENTE: Optional[DireccionParseada] = Field(default=None, alias="sitio_exacto_accidente")
    CANT_HERIDOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_heridos_en_sitio_accidente")
    CANT_MUERTOS_EN_SITIO_ACCIDENTE: int = Field(default=0, alias="cant_muertos_en_sitio_accidente")
    CANTIDAD_ACCIDENTES: int = Field(default=0, alias="cantidad_accidentes")

    # Campos para el mapa (latitud y longitud)
    LATITUD: Optional[float] = Field(default=None, alias="latitud")
    LONGITUD: Optional[float] = Field(default=None, alias="longitud")

    # Validador para normalizar y traducir los meses que vienen de la API
    @field_validator("MES_ACCIDENTE", mode="before")
    @classmethod
    def limpiar_mes(cls, v):
        if isinstance(v, str):
            # Limpiamos espacios y pasamos a mayúsculas
            mes = v.strip().upper()
            # Mapa de traducción porque la API a veces manda meses en inglés
            traducciones = {
                "JANUARY": "ENERO", "FEBRUARY": "FEBRERO", "MARCH": "MARZO",
                "APRIL": "ABRIL", "MAY": "MAYO", "JUNE": "JUNIO",
                "JULY": "JULIO", "AUGUST": "AGOSTO", "SEPTEMBER": "SEPTIEMBRE",
                "OCTOBER": "OCTUBRE", "NOVEMBER": "NOVIEMBRE", "DECEMBER": "DICIEMBRE"
            }
            # Si el mes está en el mapa lo traduce, si no, lo deja igual
            return traducciones.get(mes, mes)
        return str(v)

    # Validador para traducir los días de la semana (ej: MON -> LUNES)
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

    # Este validador asegura que campos numéricos siempre sean enteros 
    # (a veces la API los manda como decimales como 1.0)
    @field_validator("CANT_MUERTOS_EN_SITIO_ACCIDENTE", "CANT_HERIDOS_EN_SITIO_ACCIDENTE", "CANTIDAD_ACCIDENTES", mode="before")
    @classmethod
    def asegurar_entero(cls, v):
        try:
            return int(float(v))
        except (ValueError, TypeError):
            # Si el dato está mal o vacío, ponemos 0 por defecto
            return 0
    
    # Este es el validador más importante: conecta este modelo con nuestro 'direccion_parser'
    @field_validator("SITIO_EXACTO_ACCIDENTE", mode="before")
    @classmethod
    def parsear_direccion(cls, v):
        if isinstance(v, str):
            # Cuando llega un texto de dirección, lo pasamos por nuestro parser automático
            return parsear_texto(v)
        return v