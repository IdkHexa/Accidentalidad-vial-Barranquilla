"""Pruebas de la configuracion del proyecto (``config.py``).

Verifica que ``DATABASE_URL`` se lea del entorno cuando esta definida
y que caiga al valor por defecto (SQLite) cuando no.
"""

import importlib
import os
import unittest
from unittest.mock import patch

import config


class TestConfigVariables(unittest.TestCase):
    """Verifica que las constantes de configuracion se carguen correctamente.

    ``config.py`` lee variables de entorno en el momento de la importacion;
    estos tests usan ``reload`` y ``patch.dict`` para simular distintos
    entornos sin modificar las variables del sistema real.
    """
    def test_api_url_es_la_correcta(self):
        """``API_URL`` es un string fijo que apunta al dataset de Socrata."""
        self.assertEqual(
            config.API_URL,
            "https://www.datos.gov.co/resource/yb9r-2dsi.json",
        )

    def test_database_url_se_lee_del_entorno(self):
        """Cuando ``DATABASE_URL`` existe en el entorno, se usa ese valor."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/db"}, clear=False):
            importlib.reload(config)
            self.assertEqual(config.DATABASE_URL, "postgresql://localhost/db")

    def test_database_url_por_defecto_cuando_no_existe(self):
        """Sin ``DATABASE_URL``, el valor por defecto es SQLite."""
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            importlib.reload(config)
            self.assertEqual(config.DATABASE_URL, "sqlite:///accidentalidad.db")


if __name__ == "__main__":
    unittest.main()
