import httpx
from config import API_URL

# Clase para conectarnos a la API de datos abiertos
class ApiClient:
    def __init__(self):
        # Configuramos el cliente con un tiempo de espera de 30 segundos
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_dataset_limit(self, dataset_id, limit):
        # Armamos la URL usando el ID que nos pasaron (ej. accidentalidad)
        url_final = f"https://www.datos.gov.co/resource/{dataset_id}.json"
        
        offset = 0 # Empezamos desde el primer registro
        data = []  # Lista vacía para ir guardando todo
        
        # Bucle para ir pidiendo datos por pedazos (paginación)
        while offset < limit:
            # Pedimos máximo 1000 por cada vuelta
            paso = min(1000, limit - offset)
            
            try:
                # Hacemos la petición a Internet
                response = await self.client.get(
                    url_final, 
                    params={
                        "$limit": paso, 
                        "$offset": offset, 
                        "$order": "fecha_accidente"
                    }
                )
                # Si la página falla, esto lanza un error
                response.raise_for_status()
                
                # Guardamos lo que bajamos en nuestra lista
                lote = response.json()
                data.extend(lote)
                
                # Sumamos al offset para pedir los siguientes en la otra vuelta
                offset = offset + paso
                
                # Si bajamos menos de lo que pedimos, es que ya no hay más datos
                if len(lote) < paso:
                    break
            except Exception as e:
                # Si algo falla (como el internet), avisamos y paramos el bucle
                print(f"Error al bajar datos: {e}")
                break
                
        return data

    async def close(self):
        # Función para cerrar la conexión cuando terminemos
        await self.client.aclose()
