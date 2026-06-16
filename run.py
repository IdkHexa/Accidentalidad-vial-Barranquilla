"""Arranca el servidor FastAPI con uvicorn."""
import sys, os

# Asegura que la raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from data.database import init_db
init_db()   # Crea tablas si no existen

import uvicorn

if __name__ == "__main__":
    uvicorn.run("controllers.main_controller:app", host="0.0.0.0", port=8000, reload=True)
