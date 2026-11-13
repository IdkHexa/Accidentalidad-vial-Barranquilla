"""Modulo de registro de eventos del sistema.

Centraliza la configuracion de logging para toda la aplicacion.
Usa el modulo estandar ``logging`` de Python para que cualquier
componente pueda obtener un logger con ``obtener_logger()`` y
escribir mensajes con formato consistente.

El logger escribe en consola (stderr) y en un archivo rotativo
``logs/app.log`` dentro de la raiz del proyecto.  El nivel por defecto
es INFO, pero puede cambiarse con la variable de entorno ``LOG_LEVEL``.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_FECHA_FMT = "%Y-%m-%d %H:%M:%S"
_BASE_DIR = Path(__file__).resolve().parent.parent

_configurado = False
_handlers_propios: list[logging.Handler] = []


def configurar_logging(nivel: str | None = None, archivo: str | None = None):
    """Configura el logging global de la aplicacion.

    Adjunta los handlers directamente al logger raiz para que funcione
    incluso cuando servidores ASGI como Uvicorn ya inicializaron logging
    previamente.

    Parametros:
    - ``nivel``: nivel minimo de mensajes (DEBUG, INFO, WARNING, ERROR).
      Si es ``None``, lee la variable de entorno ``LOG_LEVEL`` o usa INFO.
    - ``archivo``: ruta al archivo de log.  Si es ``None``, usa
      ``logs/app.log`` en la raiz del proyecto.
    """
    global _configurado
    if _configurado:
        return

    nivel_str = (nivel or os.getenv("LOG_LEVEL", "INFO")).upper()
    nivel_int = getattr(logging, nivel_str, logging.INFO)

    formateador = logging.Formatter(_FORMATO, datefmt=_FECHA_FMT)
    root_logger = logging.getLogger()
    if root_logger.level == logging.NOTSET or root_logger.level > nivel_int:
        root_logger.setLevel(nivel_int)

    handler_consola = logging.StreamHandler(sys.stderr)
    handler_consola.setFormatter(formateador)
    handler_consola.setLevel(nivel_int)
    root_logger.addHandler(handler_consola)
    _handlers_propios.append(handler_consola)

    ruta_log = Path(archivo) if archivo else _BASE_DIR / "logs" / "app.log"
    if ruta_log.parent:
        os.makedirs(ruta_log.parent, exist_ok=True)

    handler_archivo = RotatingFileHandler(
        ruta_log,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler_archivo.setFormatter(formateador)
    handler_archivo.setLevel(nivel_int)
    root_logger.addHandler(handler_archivo)
    _handlers_propios.append(handler_archivo)

    _configurado = True


def reiniciar_logging():
    """Cierra y remueve los handlers propios para permitir reconfigurar en pruebas."""
    global _configurado
    root_logger = logging.getLogger()
    for handler in _handlers_propios:
        root_logger.removeHandler(handler)
        handler.close()
    _handlers_propios.clear()
    _configurado = False


def obtener_logger(nombre: str) -> logging.Logger:
    """Retorna un logger con el nombre del modulo que lo solicita.

    Si el logging global aun no fue configurado, lo inicializa
    automaticamente con los valores por defecto.

    Parametros:
    - ``nombre``: nombre del logger, tipicamente ``__name__`` del
      modulo que lo invoca.

    Retorna una instancia de ``logging.Logger`` lista para usar.
    """
    configurar_logging()
    return logging.getLogger(nombre)
