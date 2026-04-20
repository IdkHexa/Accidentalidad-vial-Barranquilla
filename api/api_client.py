import httpx
import asyncio
from config import API_URL
from models.entidades import AccidenteDTO

class ApiClient:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def get_data(self, url):
        response = await self.client.get(url)
        return response.json()

    async def get_dataset(self, dataset_id):
        response = await self.client.get(API_URL, params={"$limit": 5, "$offset": 0})
        return response.json()

    async def close(self):
        await self.client.aclose()

async def probar():
    api_client = ApiClient()
    data = await api_client.get_dataset("yb9r-2dsi")
    
    for item in data:
        accidente = AccidenteDTO(**item)
        print(accidente)

    await api_client.close()

if __name__ == "__main__":
    asyncio.run(probar())
