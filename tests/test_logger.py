"""Pruebas del modulo de logging centralizado (``utils/logger.py``)."""

import tempfile
import unittest
from pathlib import Path

from utils.logger import configurar_logging, obtener_logger, reiniciar_logging


class TestLogger(unittest.TestCase):
    """Verifica la creacion de loggers y escritura en archivo rotativo."""

    def setUp(self):
        """Asegura un estado limpio del sistema de logging antes de cada prueba."""
        reiniciar_logging()

    def tearDown(self):
        """Limpia los handlers configurados durante cada prueba."""
        reiniciar_logging()

    def test_crea_directorio_y_escribe_en_archivo(self):
        """``configurar_logging`` crea la carpeta padre y persiste mensajes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_log = Path(tmpdir) / "sub" / "app.log"
            try:
                configurar_logging(nivel="INFO", archivo=str(ruta_log))

                logger = obtener_logger("test.logger")
                logger.info("Mensaje de prueba en Fase 1")
                for h in list(logger.root.handlers):
                    h.flush()

                self.assertTrue(ruta_log.exists())
                contenido = ruta_log.read_text(encoding="utf-8")
                self.assertIn("Mensaje de prueba en Fase 1", contenido)
            finally:
                # En Windows debe cerrarse el FileHandler antes de borrar el temp dir.
                reiniciar_logging()


if __name__ == "__main__":
    unittest.main()
