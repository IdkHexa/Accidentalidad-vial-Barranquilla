"""Tuberia ETL (Extraccion, Transformacion y Carga) del proyecto.

Este modulo orquesta el flujo completo de datos desde que salen de
la API de Socrata hasta que quedan almacenados en la base de datos
SQLite.  El proceso se divide en tres etapas:

1. **Extraccion**: Se conecta al portal de datos abiertos y descarga
   los registros en lotes paginados.
2. **Transformacion**: Cada fila JSON se valida contra el esquema de
   Pydantic (``AccidenteDTO``) y se enriquecen las coordenadas
   faltantes mediante geocodificacion.  Los errores de validacion
   se contabilizan por campo y se reportan al final del proceso.
3. **Carga**: Los objetos ya limpios se persisten en ``accidentalidad.db``
   a traves del repositorio DAO.
"""

from collections import Counter

from pydantic import ValidationError

from api.api_client import ApiClient
from data.database import SessionLocal
from data.geocoding import GeoCoder
from data.storage import AccidenteRepository
from models.entidades import AccidenteDTO


async def ejecutar_etl(limite_registros, guardar_en_bd=True):
    """Ejecuta el pipeline completo de extraccion, transformacion y carga.

    La funcion es asincrona porque la llamada a la API de Socrata
    se hace con ``httpx.AsyncClient``, lo que permite que el programa
    no se bloquee mientras espera la respuesta de internet.

    Los registros que no superan la validacion de Pydantic no
    interrumpen el proceso: se descartan, se contabiliza el campo
    que fallo y se reporta el total al finalizar.

    Parametros:
    - ``limite_registros``: cantidad maxima de filas a descargar.
    - ``guardar_en_bd``: si es ``True``, al finalizar la transformacion
      los datos se persisten en SQLite mediante ``AccidenteRepository``.

    Retorna la lista de objetos ``AccidenteDTO`` procesados.
    """
    print(f"--- Iniciando ETL para {limite_registros} registros ---")

    cliente = ApiClient()
    geocoder = GeoCoder()
    validos = []
    geocodificados_nuevos = 0
    errores_por_campo = Counter()

    try:
        print("Paso 1: Extrayendo datos de la API...")
        datos_crudos = await cliente.get_dataset_limit("yb9r-2dsi", limite_registros)

        print(
            f"Paso 2: Transformando y geocodificando {len(datos_crudos)} registros..."
        )

        for fila in datos_crudos:
            try:
                # Convierte el diccionario crudo en un ``AccidenteDTO``.
                # Pydantic valida tipos, traduce meses y parsea la direccion
                # automaticamente gracias a los ``field_validator``.
                obj = AccidenteDTO(**fila)

                # Si el registro no trae coordenadas desde la API, se
                # intentan obtener mediante geocodificacion (Google Maps
                # o cache local) usando la direccion ya parseada.
                if obj.LATITUD is None or obj.LONGITUD is None:
                    if obj.SITIO_EXACTO_ACCIDENTE:
                        coords = geocoder.obtener_coordenadas(
                            obj.SITIO_EXACTO_ACCIDENTE
                        )
                        if coords:
                            obj.LATITUD, obj.LONGITUD = coords
                            geocodificados_nuevos += 1

                validos.append(obj)

            except ValidationError as e:
                for error in e.errors():
                    campo = ".".join(str(p) for p in error["loc"])
                    errores_por_campo[campo] += 1

    except Exception as e:
        print(f"Error fatal durante el proceso ETL: {e}")
    finally:
        # Libera los recursos del cliente HTTP (cierra conexiones
        # abiertas para evitar fugas de memoria en bucles largos).
        await cliente.close()

    if guardar_en_bd:
        print("Paso 3: Guardando en base de datos...")
        session = SessionLocal()
        try:
            repo = AccidenteRepository(session)
            total_insertado = repo.insertar_lote(validos)
            print(f"  -> {total_insertado} registros insertados.")

        except Exception as e:
            # Si algo falla durante la insercion, hacemos rollback para
            # dejar la base de datos en un estado consistente.
            session.rollback()
            print(f"Error al insertar en base de datos: {e}")

        finally:
            # La sesion debe cerrarse siempre, haya funcionado o no,
            # para devolver la conexion al pool de SQLAlchemy.
            session.close()

    print("--- ETL finalizado ---")
    print(f"Registros totales listos: {len(validos)}")
    print(f"Coordenadas obtenidas mediante Google/cache: {geocodificados_nuevos}")

    total_errores = sum(errores_por_campo.values())
    if total_errores > 0:
        print("Registros descartados por validación: ")
        for campo, cantidad in errores_por_campo.most_common():
            print(f" - {campo}: {cantidad} errores")

    return validos
