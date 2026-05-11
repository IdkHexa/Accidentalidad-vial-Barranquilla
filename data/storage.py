"""Repositorio DAO para operaciones de almacenamiento persistente.

Implementa el patron de diseno Repositorio (Data Access Object) que
encapsula la logica de acceso a la base de datos.  En lugar de esparcir
consultas SQL por todo el codigo, centralizamos aqui todas las
operaciones CRUD sobre la entidad ``AccidenteDB``.

Ventajas de este enfoque:
- Si en el futuro cambiamos SQLite por PostgreSQL, solo hay que
  modificar la configuracion del engine; el repositorio permanece igual.
- El resto del programa nunca necesita importar ``session`` ni
  ``AccidenteDB`` directamente; solo habla con el repositorio.
"""

from data.database import AccidenteDB


class AccidenteRepository:
    """Repositorio DAO para la entidad ``AccidenteDB``.

    Cada metodo encapsula una operacion de base de datos: insercion
    por lotes, conteo, consultas con filtro, etc.  Recibe una sesion
    de SQLAlchemy en el constructor, lo que permite usar una sesion
    distinta por cada operacion (o compartir la misma en una transaccion).
    """

    def __init__(self, session):
        """Guarda la sesion activa con la que trabajara el repositorio.

        Parametros:
        - ``session``: una instancia de ``SessionLocal`` de SQLAlchemy.
        """
        self.session = session

    def insertar_lote(self, accidentes_dto) -> int:
        """Inserta una lista completa de accidentes en la base de datos.

        Convierte cada ``AccidenteDTO`` en un ``AccidenteDB`` usando
        el metodo ``desde_dto`` y luego los agrega todos en una sola
        transaccion con ``add_all()``, lo que es mucho mas eficiente
        que hacer un ``add()`` por cada registro.

        Parametros:
        - ``accidentes_dto``: lista de objetos ``AccidenteDTO``.

        Retorna la cantidad de registros insertados.
        """
        objetos_db = [AccidenteDB.desde_dto(dto) for dto in accidentes_dto]
        self.session.add_all(objetos_db)
        self.session.commit()
        return len(objetos_db)

    def contar(self) -> int:
        """Cuenta cuantos registros hay almacenados en total.

        Util para mostrar estadisticas en la interfaz o para decidir
        si es necesario volver a sincronizar datos.

        Retorna un entero con la cantidad de filas en la tabla.
        """
        return self.session.query(AccidenteDB).count()

    def obtener_todos(self, limit=100):
        """Obtiene los registros mas recientes, ordenados por ID descendente.

        El orden descendente asegura que los ultimos accidentes
        insertados aparezcan primero, que suele ser lo que se quiere
        mostrar en una vista general.

        Parametros:
        - ``limit``: maximo de registros a devolver (default 100).

        Retorna una lista de objetos ``AccidenteDB``.
        """
        return (
            self.session.query(AccidenteDB)
            .order_by(AccidenteDB.id.desc())
            .limit(limit)
            .all()
        )

    def obtener_por_gravedad(self, gravedad: str):
        """Busca accidentes que coincidan con una gravedad especifica.

        La gravedad es un campo categorico que puede tener valores
        como "Fatal", "Grave" o "Leve" segun los datos de la API.
        Este filtro sera util para los graficos de la interfaz.

        Parametros:
        - ``gravedad``: texto con el tipo de gravedad a buscar.

        Retorna una lista de objetos ``AccidenteDB`` filtrados.
        """
        return (
            self.session.query(AccidenteDB)
            .filter(AccidenteDB.gravedad_accidente == gravedad)
            .all()
        )

    def obtener_por_año(self, año: int):
        """Filtra los accidentes ocurridos en un año determinado.

        Sirve para alimentar las vistas que muestran la evolucion
        temporal de la accidentalidad (por ejemplo, un grafico de
        barras por año).

        Parametros:
        - ``año``: entero con el año a consultar (ej: 2018).

        Retorna una lista de objetos ``AccidenteDB`` del año indicado.
        """
        return (
            self.session.query(AccidenteDB)
            .filter(AccidenteDB.a_o_accidente == año)
            .all()
        )
