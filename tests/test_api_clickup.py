"""Suite de pruebas unitarias para el cliente HTTP y procesador de tareas de ClickUp.

Valida el parseo de campos, formateo de fechas, paginación y consulta concurrente
con mapa de materias resuelto.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from modulos.api_clickup import (
    _obtener_headers,
    _formatear_fecha_limite,
    _formatear_fecha_creacion,
    _procesar_tarea,
    _obtener_tareas_de_lista_async,
    _procesar_lista_directa,
    obtener_tareas_api_async,
)


class TestApiClickup(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para las funciones de extracción y normalización de tareas."""

    def test_obtener_headers(self):
        """Verifica la construcción de los encabezados HTTP."""
        headers = _obtener_headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_formatear_fecha_limite_y_creacion(self):
        """Verifica la transformación de timestamps en milisegundos."""
        # Timestamp vacío
        self.assertEqual(_formatear_fecha_limite(None), "")
        self.assertEqual(_formatear_fecha_creacion(None), "")

        # Timestamp específico (ej. 20/08/2026 10:00 AM UTC aprox)
        # 1787133600000 -> 20/08/2026
        ts = "1787133600000"
        fecha_limite = _formatear_fecha_limite(ts)
        self.assertTrue(len(fecha_limite) > 0)
        self.assertIn("2026", fecha_limite)

    def test_procesar_tarea_extraccion_campos(self):
        """Verifica la normalización de la estructura de tarea de ClickUp."""
        raw_task = {
            "id": "abc123",
            "name": "Entrega Ensayo",
            "status": {"status": "In Progress"},
            "tags": [{"name": "digital"}, {"name": "urgente"}],
            "due_date": "1787500800000",
            "description": "Texto del ensayo",
            "date_created": "1787400000000",
        }
        task_id, procesada = _procesar_tarea(raw_task, "Lengua")
        self.assertEqual(task_id, "abc123")
        self.assertEqual(procesada["name"], "Entrega Ensayo")
        self.assertEqual(procesada["materia"], "Lengua")
        self.assertEqual(procesada["status"], "in progress")
        self.assertEqual(procesada["tags"], "digital, urgente")
        self.assertEqual(procesada["content"], "Texto del ensayo")

    def test_procesar_tarea_sin_id_retorna_none(self):
        """Verifica que tareas sin ID válido sean descartadas limpiamente."""
        task_id, procesada = _procesar_tarea({}, "Matemáticas")
        self.assertIsNone(task_id)
        self.assertIsNone(procesada)

    async def test_obtener_tareas_de_lista_async_paginacion(self):
        """Verifica que la paginación itere hasta encontrar una página vacía."""
        mock_client = AsyncMock()

        resp_pag0 = MagicMock()
        resp_pag0.status_code = 200
        resp_pag0.json.return_value = {"tasks": [{"id": "t1", "name": "Tarea 1"}]}

        resp_pag1 = MagicMock()
        resp_pag1.status_code = 200
        resp_pag1.json.return_value = {"tasks": []}

        mock_client.get.side_effect = [resp_pag0, resp_pag1]

        tareas = await _obtener_tareas_de_lista_async(mock_client, "lista_100")
        self.assertEqual(len(tareas), 1)
        self.assertEqual(tareas[0]["id"], "t1")
        self.assertEqual(mock_client.get.call_count, 2)

    @patch("modulos.api_clickup.obtener_mapa_listas_async")
    async def test_obtener_tareas_api_async_concurrencia(self, mock_obtener_mapa):
        """Verifica la consulta concurrente a las listas mapeadas."""
        mock_obtener_mapa.return_value = {"l1": "Matemáticas", "l2": "Física"}

        with patch("modulos.api_clickup._procesar_lista_directa") as mock_proc:
            mock_proc.side_effect = [
                {"t1": {"name": "T1", "materia": "Matemáticas"}},
                {"t2": {"name": "T2", "materia": "Física"}},
            ]
            resultado = await obtener_tareas_api_async()

            self.assertEqual(len(resultado), 2)
            self.assertIn("t1", resultado)
            self.assertIn("t2", resultado)

    @patch("modulos.api_clickup.obtener_mapa_listas_async")
    async def test_obtener_tareas_api_async_sin_listas(self, mock_obtener_mapa):
        """Verifica que retorne un diccionario vacío si no hay listas configuradas."""
        mock_obtener_mapa.return_value = {}
        resultado = await obtener_tareas_api_async()
        self.assertEqual(resultado, {})


if __name__ == "__main__":
    unittest.main()
