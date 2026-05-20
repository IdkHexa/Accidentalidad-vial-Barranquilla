"""Configuracion general del proyecto.

Centraliza los valores usados para acceder al dataset y a servicios externos.
"""

import os

from dotenv import load_dotenv

# Carga las variables del archivo .env.
load_dotenv()

# URL del dataset consultado por la aplicacion.
API_URL = "https://www.datos.gov.co/resource/yb9r-2dsi.json"

# Llave usada por el modulo de geocodificacion.
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

# Informa si falta la llave del servicio externo.
if not GOOGLE_MAPS_KEY:
    print("ADVERTENCIA: No se encontro la GOOGLE_MAPS_KEY en el archivo .env")
    print("El geocodificador fallara si intentas usarlo sin una llave valida.")

POSTGRE_USER = os.getenv("POSTGRE_USER")
POSTGRE_PASSWORD = os.getenv("POSTGRE_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
POSTGRE_DB = os.getenv("POSTGRE_DB")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    DATABASE_URL = "sqlite:///accidentalidad.db"

if __name__ == "__main__":
    # Muestra la configuracion cargada para una verificacion basica.
    print("Configuracion actual:")
    print(f"API URL: {API_URL}")
    print(f"Google Key Cargada: {'SI' if GOOGLE_MAPS_KEY else 'NO'}")
    print(f"Base de datos: {DATABASE_URL}")
