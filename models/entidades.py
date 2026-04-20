from pydantic import BaseModel, Field

class AccidenteDTO(BaseModel):
    FECHA_ACCIDENTE: str = Field(..., alias="fecha_accidente")
    HORA_ACCIDENTE: str = Field(..., alias="hora_accidente")
    GRAVEDAD_ACCIDENTE: str = Field(..., alias="gravedad_accidente")
    CLASE_ACCIDENTE: str = Field(..., alias="clase_accidente")
    DIA_ACCIDENTE: str = Field(..., alias="dia_accidente")
    MES_ACCIDENTE: str = Field(..., alias="mes_accidente")
    AÑO_ACCIDENTE: str = Field(..., alias="año_accidente")
    TIPO_ACCIDENTE: str = Field(..., alias="tipo_accidente")
    DESCRIPCION_ACCIDENTE: str = Field(..., alias="descripcion_accidente")

    