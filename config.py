"""Configuracion general del proyecto.

Centraliza los valores usados para acceder al dataset de Socrata,
la base de datos (PostgreSQL o respaldo en SQLite), servicios externos
y parametros de ejecucion del servidor web.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Directorio raiz del proyecto, independiente del directorio de trabajo actual.
BASE_DIR = Path(__file__).resolve().parent

# Carga las variables del archivo .env ubicado en la raiz del proyecto.
load_dotenv(BASE_DIR / ".env")

# Identificador del dataset en el portal de datos abiertos de Colombia.
DATASET_ID = "yb9r-2dsi"

# URL del dataset consultado por la aplicacion.
API_URL = f"https://www.datos.gov.co/resource/{DATASET_ID}.json"

# Llave usada por el modulo de geocodificacion.
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

# Informa si falta la llave del servicio externo.
if not GOOGLE_MAPS_KEY:
    print("ADVERTENCIA: No se encontro la GOOGLE_MAPS_KEY en el archivo .env")
    print("El geocodificador fallara si intentas usarlo sin una llave valida.")

# Credenciales de PostgreSQL (con alias heredados para compatibilidad).
POSTGRES_USER = os.getenv("POSTGRES_USER") or os.getenv("POSTGRE_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRE_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB") or os.getenv("POSTGRE_DB")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "8448")

POSTGRE_USER = POSTGRES_USER
POSTGRE_PASSWORD = POSTGRES_PASSWORD
POSTGRE_DB = POSTGRES_DB

# Configuracion de red para el servidor FastAPI / Uvicorn.
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8080"))


def _resolver_database_url() -> str:
    """Resuelve la cadena de conexion a la base de datos.

    Prioriza ``DATABASE_URL`` cuando tiene un valor explicito en el entorno.
    Si ``DATABASE_URL`` no fue definida en el entorno y existen credenciales de
    PostgreSQL, construye la URI de forma segura con ``URL.create``. Si la
    variable fue vaciada explicitamente o faltan credenciales, usa SQLite local.
    """
    url_explicita = os.getenv("DATABASE_URL")
    if url_explicita:
        return url_explicita

    if (
        "DATABASE_URL" not in os.environ
        and POSTGRES_USER
        and POSTGRES_PASSWORD
        and POSTGRES_DB
    ):
        return URL.create(
            drivername="postgresql+psycopg2",
            username=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=POSTGRES_DB,
        ).render_as_string(hide_password=False)

    return "sqlite:///accidentalidad.db"


DATABASE_URL = _resolver_database_url()

if __name__ == "__main__":
    # Muestra la configuracion cargada sin exponer credenciales.
    print("Configuracion actual:")
    print(f"API URL: {API_URL}")
    print(f"Google Key Cargada: {'SI' if GOOGLE_MAPS_KEY else 'NO'}")
    print(f"Servidor web: {APP_HOST}:{APP_PORT}")
    print(f"Motor BD: {DATABASE_URL.split('://', 1)[0]}")
