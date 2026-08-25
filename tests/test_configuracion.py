"""Suite de pruebas unitarias para el módulo de configuración y autodescubrimiento.

Valida la lectura y serialización de variables de entorno (.env), el autodescubrimiento
jerárquico de listas en ClickUp y la resolución segura ante valores faltantes o corruptos.
"""

import os
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from modulos.configuracion import (
    obtener_token_api,
    obtener_nombre_autor,
    guardar_listas_en_env,
    autodescubrir_listas_clickup_async,
    obtener_mapa_listas_async,
)


class TestConfiguracion(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para las funciones de configuración y descubrimiento."""

    def setUp(self):
        """Prepara el entorno respaldando las variables de prueba."""
        self.orig_listas = os.environ.get("CLICKUP_LISTAS_MATERIAS")
        self.orig_autor = os.environ.get("AUTOR_NOMBRE")

    def tearDown(self):
        """Restaura el entorno tras cada prueba."""
        if self.orig_listas is not None:
            os.environ["CLICKUP_LISTAS_MATERIAS"] = self.orig_listas
        else:
            os.environ.pop("CLICKUP_LISTAS_MATERIAS", None)

        if self.orig_autor is not None:
            os.environ["AUTOR_NOMBRE"] = self.orig_autor
        else:
            os.environ.pop("AUTOR_NOMBRE", None)

    def test_obtener_nombre_autor(self):
        """Verifica la lectura limpia del autor desde variable de entorno."""
        os.environ["AUTOR_NOMBRE"] = "  Emmanuel  "
        self.assertEqual(obtener_nombre_autor(), "Emmanuel")

        os.environ["AUTOR_NOMBRE"] = "   "
        self.assertEqual(obtener_nombre_autor(), "")

    async def test_obtener_mapa_listas_desde_env_valido(self):
        """Verifica que se lean las listas directamente desde la variable de entorno JSON."""
        mapa_esperado = {"12345": "Física Avanzada", "67890": "Química Orgánica"}
        os.environ["CLICKUP_LISTAS_MATERIAS"] = json.dumps(mapa_esperado)

        mock_client = MagicMock()
        resultado = await obtener_mapa_listas_async(mock_client)
        self.assertEqual(resultado, mapa_esperado)
        mock_client.get.assert_not_called()

    @patch("modulos.configuracion.guardar_listas_en_env")
    @patch("modulos.configuracion.autodescubrir_listas_clickup_async")
    async def test_obtener_mapa_listas_ejecuta_autodescubrimiento_si_no_existe_env(
        self, mock_descubrir, mock_guardar
    ):
        """Verifica que se ejecute el autodescubrimiento y persistencia si no existe la variable."""
        os.environ.pop("CLICKUP_LISTAS_MATERIAS", None)
        descubiertas = {"111": "Historia", "222": "Biología"}
        mock_descubrir.return_value = descubiertas

        mock_client = MagicMock()
        resultado = await obtener_mapa_listas_async(mock_client)

        self.assertEqual(resultado, descubiertas)
        mock_descubrir.assert_awaited_once_with(mock_client)
        mock_guardar.assert_called_once_with(descubiertas)

    @patch("modulos.configuracion.guardar_listas_en_env")
    @patch("modulos.configuracion.autodescubrir_listas_clickup_async")
    async def test_obtener_mapa_listas_retorna_vacio_si_falla_autodescubrimiento(
        self, mock_descubrir, mock_guardar
    ):
        """Verifica que retorne un diccionario vacío de forma segura si no se detectan listas."""
        os.environ.pop("CLICKUP_LISTAS_MATERIAS", None)
        mock_descubrir.return_value = {}

        mock_client = MagicMock()
        resultado = await obtener_mapa_listas_async(mock_client)

        self.assertEqual(resultado, {})
        mock_guardar.assert_not_called()

    async def test_autodescubrir_listas_clickup_async_exitoso(self):
        """Verifica el recorrido completo de Teams -> Spaces -> Lists / Folders."""
        mock_client = AsyncMock()

        resp_team = MagicMock()
        resp_team.status_code = 200
        resp_team.json.return_value = {"teams": [{"id": "team_1"}]}

        resp_space = MagicMock()
        resp_space.status_code = 200
        resp_space.json.return_value = {"spaces": [{"id": "space_1"}]}

        resp_list = MagicMock()
        resp_list.status_code = 200
        resp_list.json.return_value = {
            "lists": [{"id": "list_directa_1", "name": "Matemáticas"}]
        }

        resp_folder = MagicMock()
        resp_folder.status_code = 200
        resp_folder.json.return_value = {
            "folders": [
                {
                    "id": "folder_1",
                    "name": "Semestre 1",
                    "lists": [{"id": "list_folder_1", "name": "Filosofía"}],
                }
            ]
        }

        async def fake_get(url, **kwargs):
            if url.endswith("/team"):
                return resp_team
            elif "/space" in url and "/list" not in url and "/folder" not in url:
                return resp_space
            elif url.endswith("/list"):
                return resp_list
            elif url.endswith("/folder"):
                return resp_folder
            raise ValueError(f"URL no esperada: {url}")

        mock_client.get.side_effect = fake_get

        resultado = await autodescubrir_listas_clickup_async(mock_client)
        esperado = {
            "list_directa_1": "Matemáticas",
            "list_folder_1": "Filosofía",
        }
        self.assertEqual(resultado, esperado)

    @patch("dotenv.set_key")
    def test_guardar_listas_en_env(self, mock_set_key):
        """Verifica que se serialicen las listas y se guarde en el archivo .env."""
        listas = {"123": "Arte", "456": "Música"}
        guardar_listas_en_env(listas, ruta_env=".env")

        self.assertIn("CLICKUP_LISTAS_MATERIAS", os.environ)
        mock_set_key.assert_called_once()
        args, kwargs = mock_set_key.call_args
        self.assertEqual(args[0], ".env")
        self.assertEqual(args[1], "CLICKUP_LISTAS_MATERIAS")
        self.assertEqual(json.loads(args[2]), listas)


if __name__ == "__main__":
    unittest.main()
