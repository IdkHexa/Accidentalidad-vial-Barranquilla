"""Arranca el servidor FastAPI con Uvicorn usando la configuracion centralizada."""

import os
import sys

import uvicorn

# Asegura que la raiz del proyecto este en el path cuando se ejecuta como script.
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_HOST, APP_PORT


if __name__ == "__main__":
    uvicorn.run(
        "controllers.main_controller:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
    )
