"""Configuracion del motor de base de datos y modelo ORM.

Este modulo centraliza la conexion a la base de datos (PostgreSQL o SQLite
en pruebas) y define el mapeo objeto-relacional (ORM) e indices secundarios
para consultar registros de accidentalidad sin escribir SQL crudo.
"""

from sqlalchemy import Column, Float, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import config

engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AccidenteDB(Base):
    """Modelo ORM que representa un accidente de transito en la base de datos.

    Cada instancia de esta clase corresponde a una fila en la tabla
    ``accidentes``. Incluye indices sobre las columnas de filtro y
    agregacion (``a_o_accidente``, ``gravedad_accidente``, ``fecha_accidente``
    y el par ``latitud, longitud``) para acelerar consultas analiticas.
    """

    __tablename__ = "accidentes"
    __table_args__ = (
        Index("ix_accidentes_anio", "a_o_accidente"),
        Index("ix_accidentes_gravedad", "gravedad_accidente"),
        Index("ix_accidentes_fecha", "fecha_accidente"),
        Index("ix_accidentes_coords", "latitud", "longitud"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_accidente = Column(String(50), nullable=False)
    hora_accidente = Column(String(20), nullable=False)
    gravedad_accidente = Column(String(50), nullable=False)
    clase_accidente = Column(String(50), nullable=False)
    a_o_accidente = Column(Integer)
    mes_accidente = Column(String(20))
    dia_accidente = Column(String(20))
    sitio_exacto_accidente = Column(Text, nullable=True)
    cant_heridos_en_sitio_accidente = Column(Integer, default=0)
    cant_muertos_en_sitio_accidente = Column(Integer, default=0)
    cantidad_accidentes = Column(Integer, default=1)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    @classmethod
    def desde_dto(cls, dto):
        """Convierte un ``AccidenteDTO`` (Pydantic) en un ``AccidenteDB`` (SQLAlchemy).

        Parametros:
        - ``dto``: instancia de ``AccidenteDTO`` con los datos validados.

        Retorna una nueva instancia de ``AccidenteDB`` lista para persistir.
        """
        sitio_texto = (
            str(dto.SITIO_EXACTO_ACCIDENTE).strip()
            if dto.SITIO_EXACTO_ACCIDENTE is not None
            else ""
        )
        return cls(
            fecha_accidente=dto.FECHA_ACCIDENTE,
            hora_accidente=dto.HORA_ACCIDENTE,
            gravedad_accidente=dto.GRAVEDAD_ACCIDENTE,
            clase_accidente=dto.CLASE_ACCIDENTE,
            a_o_accidente=dto.AÑO_ACCIDENTE,
            mes_accidente=dto.MES_ACCIDENTE,
            dia_accidente=dto.DIA_ACCIDENTE,
            sitio_exacto_accidente=sitio_texto or None,
            cant_heridos_en_sitio_accidente=dto.CANT_HERIDOS_EN_SITIO_ACCIDENTE,
            cant_muertos_en_sitio_accidente=dto.CANT_MUERTOS_EN_SITIO_ACCIDENTE,
            cantidad_accidentes=dto.CANTIDAD_ACCIDENTES,
            latitud=dto.LATITUD,
            longitud=dto.LONGITUD,
        )


def init_db(target_engine=None):
    """Inicializa de forma idempotente tablas e indices de la base de datos.

    Crea la tabla ``accidentes`` si no existe y garantiza que los indices
    secundarios definidos en ``AccidenteDB`` tambien existan sobre tablas
    creadas previamente.
    """
    motor = target_engine or engine
    Base.metadata.create_all(bind=motor)
    for indice in AccidenteDB.__table__.indexes:
        indice.create(bind=motor, checkfirst=True)
