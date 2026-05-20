"""Configuracion del motor de base de datos y modelo ORM.

Este modulo centraliza la conexion a la base de datos (SQLite
o PostgreSQL segun configuracion) y define el mapeo
objeto-relacional (ORM) que permite tratar los registros de accidentes
como objetos de Python en lugar de escribir SQL directamente.

SQLAlchemy se encarga de traducir automaticamente las operaciones
que hagamos sobre objetos a instrucciones SQL, aislando al resto
del programa de los detalles del motor de base de datos.
"""

from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AccidenteDB(Base):
    """Modelo ORM que representa un accidente de transito en la base de datos.

    Cada instancia de esta clase corresponde a una fila en la tabla
    ``accidentes``.  Los nombres de las columnas siguen la misma
    convencion que el DTO de Pydantic para facilitar la conversion
    entre ambos mundos (objeto de memoria y registro persistente).

    La columna ``id`` es una clave primaria autoincremental generada
    por SQLite; no viene del dataset original sino que la creamos
    nosotros para poder identificar univocamente cada registro.
    """

    __tablename__ = "accidentes"

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
    cantidad_accidentes = Column(Integer, default=0)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)

    @classmethod
    def desde_dto(cls, dto):
        """Convierte un ``AccidenteDTO`` (Pydantic) en un ``AccidenteDB`` (SQLAlchemy).

        Este metodo es el puente entre la capa de validacion y la de
        persistencia: toma el objeto limpio que produjo el ETL y lo
        transforma en un registro listo para persistir en la base de datos.

        Parametros:
        - ``dto``: instancia de ``AccidenteDTO`` con los datos validados.

        Retorna una nueva instancia de ``AccidenteDB`` con los campos
        mapeados uno a uno.  La direccion se convierte a texto plano
        con ``str()`` para almacenarla como cadena.
        """
        return cls(
            fecha_accidente=dto.FECHA_ACCIDENTE,
            hora_accidente=dto.HORA_ACCIDENTE,
            gravedad_accidente=dto.GRAVEDAD_ACCIDENTE,
            clase_accidente=dto.CLASE_ACCIDENTE,
            a_o_accidente=dto.AÑO_ACCIDENTE,
            mes_accidente=dto.MES_ACCIDENTE,
            dia_accidente=dto.DIA_ACCIDENTE,
            sitio_exacto_accidente=str(dto.SITIO_EXACTO_ACCIDENTE)
            if dto.SITIO_EXACTO_ACCIDENTE
            else None,
            cant_heridos_en_sitio_accidente=dto.CANT_HERIDOS_EN_SITIO_ACCIDENTE,
            cant_muertos_en_sitio_accidente=dto.CANT_MUERTOS_EN_SITIO_ACCIDENTE,
            cantidad_accidentes=dto.CANTIDAD_ACCIDENTES,
            latitud=dto.LATITUD,
            longitud=dto.LONGITUD,
        )


def init_db():
    """Inicializa el esquema de la base de datos.

    Ejecuta ``Base.metadata.create_all()``, que inspecciona todas las
    clases que heredan de ``Base`` (en este caso ``AccidenteDB``) y
    crea sus tablas si aun no existen, sin importar el motor
    (SQLite o PostgreSQL).  Es seguro llamarla
    multiples veces porque SQLAlchemy verifica ``IF NOT EXISTS``
    internamente.
    """
    Base.metadata.create_all(bind=engine)
