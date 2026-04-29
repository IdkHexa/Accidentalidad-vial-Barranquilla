import asyncio
from api.api_client import ApiClient
from models.entidades import AccidenteDTO
from data.geocoding import GeoCoder 
from pydantic import ValidationError

# Esta es la función principal que orquesta todo el trabajo (Extraer, Transformar y Geocodificar)
async def ejecutar_etl(limite_registros):
    print(f"--- Iniciando ETL para {limite_registros} registros ---")
    
    # Paso 1: Inicializamos nuestras herramientas (El navegador de API y el Geocodificador)
    cliente = ApiClient()
    geocoder = GeoCoder() # El geocodificador ya trae su propio sistema de caché
    validos = []          # Aquí guardaremos los objetos limpios
    geocodificados_nuevos = 0
    
    try:
        # Paso 2: EXTRACCIÓN - Bajamos los datos crudos desde la API de Socrata
        print("Paso 1: Extrayendo datos de la API...")
        datos_crudos = await cliente.get_dataset_limit("yb9r-2dsi", limite_registros)
        
        # Paso 3: TRANSFORMACIÓN - Convertimos los diccionarios en objetos DTO y geocodificamos
        print(f"Paso 2: Transformando y Geocodificando {len(datos_crudos)} registros...")
        for fila in datos_crudos:
            try:
                # Al meter la fila al DTO, Pydantic valida tipos y limpia campos automáticamente
                obj = AccidenteDTO(**fila)
                
                # REGLA DE NEGOCIO: Si el registro no trae latitud o longitud desde la API...
                if obj.LATITUD is None or obj.LONGITUD is None:
                    # ...usamos nuestro módulo para pedir coordenadas a Google/Caché
                    if obj.SITIO_EXACTO_ACCIDENTE:
                        coords = geocoder.obtener_coordenadas(obj.SITIO_EXACTO_ACCIDENTE)
                        if coords:
                            # Si las hallamos, las guardamos en el objeto
                            obj.LATITUD, obj.LONGITUD = coords
                            geocodificados_nuevos += 1
                
                validos.append(obj)
            except ValidationError:
                # Si un registro está muy roto y Pydantic no lo deja pasar, lo saltamos silenciosamente
                continue 
                
    except Exception as e:
        # Si ocurre un error grave (ej: sin internet), avisamos y detenemos el proceso
        print(f"Error fatal durante el proceso ETL: {e}")
    finally:
        # Paso 4: Pase lo que pase, debemos cerrar la conexión para no dejar procesos colgando
        await cliente.close()
    
    print(f"--- ETL Finalizado ---")
    print(f"Registros totales listos: {len(validos)}")
    print(f"Coordenadas obtenidas mediante Google/Caché: {geocodificados_nuevos}")
    
    # Devolvemos la lista de accidentes ya limpios y ubicados en el mapa
    return validos
