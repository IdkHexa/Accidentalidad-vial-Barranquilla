"""Modulo de registro de eventos del sistema.

Centraliza la configuracion de logging para toda la aplicacion.
Usa el modulo estandar ``logging`` de Python para que cualquier
componente pueda obtener un logger con ``obtener_logger()`` y
escribir mensajes con formato consistente.

El logger escribe en consola (stderr) y opcionalmente en un archivo
``logs/app.log`` si el directorio existe.  El nivel por defecto
es INFO, pero puede cambiarse con la variable de entorno ``LOG_LEVEL``.
"""

import logging
import os
import sys

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_FECHA_FMT = "%Y-%m-%d %H:%M:%S"

_configurado = False


def configurar_logging(nivel: str | None = None, archivo: str | None = None):
    """Configura el logging global de la aplicacion.

    Parametros:
    - ``nivel``: nivel minimo de mensajes (DEBUG, INFO, WARNING, ERROR).
      Si es ``None``, lee la variable de entorno ``LOG_LEVEL`` o usa INFO.
    - ``archivo``: ruta al archivo de log.  Si es ``None``, usa
      ``logs/app.log``.  Si el directorio no existe, solo escribe en consola.
    """
    global _configurado
    if _configurado:
        return

    nivel_str = nivel or os.getenv("LOG_LEVEL", "INFO").upper()
    nivel_int = getattr(logging, nivel_str, logging.INFO)

    formateador = logging.Formatter(_FORMATO, datefmt=_FECHA_FMT)

    handler_consola = logging.StreamHandler(sys.stderr)
    handler_consola.setFormatter(formateador)
    handler_consola.setLevel(nivel_int)

    logging.basicConfig(level=nivel_int, handlers=[handler_consola])

    ruta_log = archivo or os.path.join("logs", "app.log")
    directorio = os.path.dirname(ruta_log)
    if directorio and os.path.isdir(directorio):
        handler_archivo = logging.FileHandler(ruta_log, encoding="utf-8")
        handler_archivo.setFormatter(formateador)
        handler_archivo.setLevel(nivel_int)
        logging.getLogger().addHandler(handler_archivo)

    _configurado = True


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
