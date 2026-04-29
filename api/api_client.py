import httpx
from config import API_URL

# Esta clase es nuestro "navegador" para ir a la página de datos abiertos y bajar los JSON
class ApiClient:
    def __init__(self):
        # Configuramos el cliente con un tiempo de espera de 30 segundos (por si el internet está lento)
        self.client = httpx.AsyncClient(timeout=30.0)

    # Esta función se encarga de pedir los datos por pedazos (paginación)
    async def get_dataset_limit(self, dataset_id, limit):
        # Armamos la URL usando el ID que nos pasaron (ej. 'yb9r-2dsi' para accidentes)
        url_final = f"https://www.datos.gov.co/resource/{dataset_id}.json"
        
        offset = 0 # Empezamos desde el primer registro de la fila
        data = []  # Lista vacía donde iremos metiendo cada fila que bajemos
        
        # Bucle para ir pidiendo datos por pedazos (máximo 1000 por vuelta para no saturar)
        while offset < limit:
            # Calculamos cuántos faltan para no pasarnos del límite que pidió el usuario
            paso = min(1000, limit - offset)
            
            try:
                # Hacemos la petición real a Internet (es asíncrona para no congelar el programa)
                response = await self.client.get(
                    url_final, 
                    params={
                        "$limit": paso, 
                        "$offset": offset, 
                        "$order": "fecha_accidente" # Pedimos que vengan ordenados por fecha
                    }
                )
                # Si la página web devuelve un error (como 404), esto lanza una excepción
                response.raise_for_status()
                
                # Convertimos el texto de internet en una lista de diccionarios de Python
                lote = response.json()
                data.extend(lote) # Metemos el lote nuevo en nuestra lista maestra
                
                # Sumamos al offset para que en la próxima vuelta pida los registros siguientes
                offset = offset + paso
                
                # Si bajamos menos de lo que pedimos, es porque la API ya no tiene más datos
                if len(lote) < paso:
                    break
            except Exception as e:
                # Si algo falla (se cortó el wifi, etc.), avisamos y devolvemos lo que tengamos
                print(f"Error al bajar datos de la API: {e}")
                break
                
        return data

    # Función importante para cerrar la conexión y liberar recursos de la PC
    async def close(self):
        await self.client.aclose()
