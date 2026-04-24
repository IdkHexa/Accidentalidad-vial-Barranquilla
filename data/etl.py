import asyncio
from api.api_client import ApiClient
from models.entidades import AccidenteDTO
from pydantic import ValidationError

# Función principal que organiza todo el trabajo
async def ejecutar_etl(limite_registros):
    print(f"--- Iniciando ETL para {limite_registros} registros ---")
    
    # Paso 1: Creamos el cliente para conectarnos
    cliente = ApiClient()
    validos = []
    
    try:
        # Paso 2: Usamos el cliente para bajar los datos crudos
        print("Paso 1: Extrayendo datos de la API...")
        datos_crudos = await cliente.get_dataset_limit("yb9r-2dsi", limite_registros)
        
        # Paso 3: Pasamos los datos crudos por el modelo para limpiarlos
        print(f"Paso 2: Transformando y Limpiando {len(datos_crudos)} registros...")
        for fila in datos_crudos:
            try:
                # Al meter la fila al DTO, se limpian los meses, dias y numeros
                obj = AccidenteDTO(**fila)
                validos.append(obj)
            except ValidationError:
                # Si un registro está muy roto y Pydantic no lo deja pasar, lo saltamos
                continue 
                
    except Exception as e:
        # Si algo explota (como falta de internet), avisamos qué pasó
        print(f"Error fatal durante el proceso: {e}")
    finally:
        # Paso 4: Pase lo que pase, debemos cerrar el cliente al final
        await cliente.close()
    
    print(f"ETL Finalizado con éxito. Registros listos: {len(validos)}")
    
    # Devolvemos la lista de objetos ya limpios y listos
    return validos