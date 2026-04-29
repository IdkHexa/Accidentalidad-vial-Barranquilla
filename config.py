# Archivo de configuración global del proyecto
import os
from dotenv import load_dotenv

# Cargamos las variables de entorno definidas en el archivo .env
load_dotenv()

# URL oficial del dataset de accidentalidad de la Alcaldía de Barranquilla
API_URL = "https://www.datos.gov.co/resource/yb9r-2dsi.json"

# Obtenemos la llave de Google Maps desde el sistema
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

# Validación: Si la llave no existe, lanzamos un aviso claro
if not GOOGLE_MAPS_KEY:
    print("ADVERTENCIA: No se encontró la GOOGLE_MAPS_KEY en el archivo .env")
    print("El geocodificador fallará si intentas usarlo sin una llave válida.")

# Este bloque solo se ejecuta si corres este archivo directamente
if __name__ == "__main__":
    print(f"Configuración Actual: ")
    print(f"API URL: {API_URL}")
    print(f"Google Key Cargada: {'SÍ' if GOOGLE_MAPS_KEY else 'NO'}")
