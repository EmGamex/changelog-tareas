"""Pruebas unitarias para validar la paridad exacta entre el motor C++ nativo y Python."""

import unittest
from datetime import datetime

from modulos.changelog import (
    MOTOR_NATIVO_DISPONIBLE,
    generar_texto_changelog_python,
    generar_texto_changelog_nativo,
    generar_texto_changelog,
)
from modulos.tarea import Tarea


class TestChangelogCppParidad(unittest.TestCase):
    """Verifica que el motor C++ nativo produzca salidas idénticas a la versión en Python."""

    def setUp(self):
        self.assertTrue(
            MOTOR_NATIVO_DISPONIBLE,
            "El módulo nativo C++ (_changelog_nativo) debe estar compilado y disponible para las pruebas.",
        )

    def _assert_paridad(self, ayer, hoy, fecha_ref):
        salida_py = generar_texto_changelog_python(ayer, hoy, fecha_referencia=fecha_ref)
        salida_cpp = generar_texto_changelog_nativo(ayer, hoy, fecha_referencia=fecha_ref)
        salida_auto = generar_texto_changelog(ayer, hoy, fecha_referencia=fecha_ref, usar_nativo=True)

        self.assertEqual(salida_cpp, salida_py, "La salida del motor C++ no coincide con la versión Python.")
        self.assertEqual(salida_auto, salida_py, "La función generar_texto_changelog con motor nativo no coincide.")

    def test_sin_cambios(self):
        """Verifica paridad cuando no hay cambios."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        tareas = {
            "1": {
                "name": "Tarea Sin Cambios",
                "materia": "Historia",
                "status": "to do",
                "tags": "",
                "due_date": "28/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        self._assert_paridad(tareas, tareas, fecha_ref)

    def test_tareas_archivadas_y_completadas(self):
        """Verifica paridad al detectar tareas desaparecidas (archivadas) y marcadas como completadas."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        ayer = {
            "1": {
                "name": "Tarea que desaparece",
                "materia": "Química",
                "status": "to do",
                "tags": "",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            },
            "2": {
                "name": "Tarea que se completa",
                "materia": "Física",
                "status": "to do",
                "tags": "",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            },
            "3": {
                "name": "Tarea personal ignorada",
                "materia": "Personal",
                "status": "to do",
                "tags": "personal",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        hoy = {
            "2": {
                "name": "Tarea que se completa",
                "materia": "Física",
                "status": "complete",
                "tags": "",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        self._assert_paridad(ayer, hoy, fecha_ref)

    def test_nuevas_tareas_con_etiquetas_y_fechas(self):
        """Verifica paridad en tareas creadas hoy con distintas combinaciones de fechas y etiquetas."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        ayer = {}
        hoy = {
            "1": {
                "name": "Nueva con fecha hoy",
                "materia": "Cálculo",
                "status": "to do",
                "tags": "urgente",
                "due_date": "22/08/2026 15:00",
                "content": "",
                "date_created": "22/08/2026 09:00",
            },
            "2": {
                "name": "Nueva sin fecha",
                "materia": "Literatura",
                "status": "to do",
                "tags": "",
                "due_date": "",
                "content": "",
                "date_created": "22/08/2026 09:00",
            },
            "3": {
                "name": "Creada y completada hoy",
                "materia": "Biología",
                "status": "closed",
                "tags": "",
                "due_date": "22/08/2026",
                "content": "",
                "date_created": "22/08/2026 09:00",
            }
        }
        self._assert_paridad(ayer, hoy, fecha_ref)

    def test_auditoria_modificaciones(self):
        """Verifica paridad en detección de cambios de nombre, fecha y etiquetas."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        ayer = {
            "1": Tarea(
                id="1",
                name="Ensayo v1",
                materia="Filosofía",
                status="to do",
                tags="borrador",
                due_date="23/08/2026 18:00",
            )
        }
        hoy = {
            "1": Tarea(
                id="1",
                name="Ensayo Final",
                materia="Filosofía",
                status="to do",
                tags="digital, obligatorio",
                due_date="25/08/2026 20:00",
            )
        }
        self._assert_paridad(ayer, hoy, fecha_ref)

    def test_autocompletado_inactividad(self):
        """Verifica paridad en tareas vencidas por inactividad."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        ayer = {
            "1": {
                "name": "Tarea Vencida",
                "materia": "Historia",
                "status": "to do",
                "tags": "",
                "due_date": "20/08/2026",
                "content": "",
                "date_created": "15/08/2026",
            }
        }
        hoy = {
            "1": {
                "name": "Tarea Vencida",
                "materia": "Historia",
                "status": "to do",
                "tags": "",
                "due_date": "20/08/2026",
                "content": "",
                "date_created": "15/08/2026",
            }
        }
        self._assert_paridad(ayer, hoy, fecha_ref)


if __name__ == "__main__":
    unittest.main()
