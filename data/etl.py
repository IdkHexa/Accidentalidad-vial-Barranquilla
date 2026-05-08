"""Proceso ETL principal del proyecto.

Este archivo coordina la extraccion desde la API, la validacion de registros y
el enriquecimiento de coordenadas cuando es necesario.
"""

from api.api_client import ApiClient
from models.entidades import AccidenteDTO
from data.geocoding import GeoCoder
from pydantic import ValidationError


async def ejecutar_etl(limite_registros):
    """
    Ejecuta la carga completa de registros.

    `limite_registros` define cuantas filas se solicitan a la API.
    """
    print(f"--- Iniciando ETL para {limite_registros} registros ---")

    cliente = ApiClient()
    geocoder = GeoCoder()
    validos = []
    geocodificados_nuevos = 0

    try:
        print("Paso 1: Extrayendo datos de la API...")
        datos_crudos = await cliente.get_dataset_limit("yb9r-2dsi", limite_registros)

        print(f"Paso 2: Transformando y geocodificando {len(datos_crudos)} registros...")
        for fila in datos_crudos:
            try:
                # Convierte cada fila a un objeto validado.
                obj = AccidenteDTO(**fila)

                # Si faltan coordenadas, intenta completarlas desde la direccion.
                if obj.LATITUD is None or obj.LONGITUD is None:
                    if obj.SITIO_EXACTO_ACCIDENTE:
                        coords = geocoder.obtener_coordenadas(obj.SITIO_EXACTO_ACCIDENTE)
                        if coords:
                            obj.LATITUD, obj.LONGITUD = coords
                            geocodificados_nuevos += 1

                validos.append(obj)
            except ValidationError:
                # Omite filas invalidas sin detener toda la carga.
                continue

    except Exception as e:
        print(f"Error fatal durante el proceso ETL: {e}")
    finally:
        # Libera la conexion HTTP al terminar.
        await cliente.close()

    print("--- ETL finalizado ---")
    print(f"Registros totales listos: {len(validos)}")
    print(f"Coordenadas obtenidas mediante Google/cache: {geocodificados_nuevos}")

    return validos
