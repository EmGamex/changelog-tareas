"""Suite de pruebas unitarias para el modelo de dominio Tarea y módulos asociados.

Valida reglas de negocio, autocompletado por inactividad, fechas relativas,
auditoría de diferencias y preparación de datos para la tabla visual.
"""

import unittest
from datetime import datetime, timedelta, date

from modulos.tarea import (
    Tarea,
    ESTADOS_COMPLETADOS,
    ETIQUETAS_IGNORADAS,
    auditar_cambios,
)
from modulos.changelog import (
    generar_texto_changelog,
    tiene_etiqueta_ignorada,
    obtener_fecha_visual,
    es_tarea_nueva,
)
from generador_imagen import preparar_datos_tareas
from main import _obtener_pie_mensaje


class TestModuloTarea(unittest.TestCase):
    """Pruebas unitarias para el modelo de dominio Tarea y sus reglas de negocio."""

    def test_etiquetas_ignoradas(self):
        """Verifica que las tareas con etiqueta 'personal' sean ignoradas."""
        t_personal = Tarea(
            id="1",
            name="Comprar víveres",
            materia="Extracurricular",
            tags="personal, urgente",
        )
        self.assertTrue(t_personal.tiene_etiqueta_ignorada())
        self.assertTrue(tiene_etiqueta_ignorada(t_personal))

        t_academica = Tarea(
            id="2",
            name="Ejercicios de Álgebra",
            materia="Matemáticas",
            tags="digital, obligatorio",
        )
        self.assertFalse(t_academica.tiene_etiqueta_ignorada())
        self.assertFalse(tiene_etiqueta_ignorada(t_academica))

    def test_estados_completados_canonicos(self):
        """Verifica que los estados canónicos (closed, complete, entregada, hecha) se clasifiquen como completados."""
        for estado in ["closed", "complete", "entregada", "hecha", "COMPLETE", " Hecha "]:
            t = Tarea(id="1", name="Tarea", materia="Física", status=estado)
            self.assertTrue(
                t.esta_completada(),
                f"El estado '{estado}' debería considerarse completado.",
            )

        t_pendiente = Tarea(id="2", name="Tarea", materia="Física", status="in progress")
        self.assertFalse(t_pendiente.esta_completada())

    def test_autocompletado_por_inactividad_fecha_vencida(self):
        """Verifica que una tarea con fecha de vencimiento anterior a hoy se clasifique como completada por inactividad."""
        hoy = date(2026, 8, 22)
        ayer = hoy - timedelta(days=1)
        manana = hoy + timedelta(days=1)

        t_vencida = Tarea(
            id="1",
            name="Guía de estudio",
            materia="Filosofía",
            status="to do",
            due_date=ayer.strftime("%d/%m/%Y 18:00"),
        )
        self.assertTrue(t_vencida.esta_completada(hoy_date=hoy))
        self.assertTrue(t_vencida.completada_por_inactividad(hoy_date=hoy))

        t_vigente = Tarea(
            id="2",
            name="Lectura 3",
            materia="Filosofía",
            status="to do",
            due_date=manana.strftime("%d/%m/%Y 18:00"),
        )
        self.assertFalse(t_vigente.esta_completada(hoy_date=hoy))
        self.assertFalse(t_vigente.completada_por_inactividad(hoy_date=hoy))

    def test_formateo_fechas_relativas(self):
        """Verifica el formateo natural de fechas relativas en español."""
        hoy = date(2026, 8, 24)  # Lunes
        manana = hoy + timedelta(days=1)
        en_tres_dias = hoy + timedelta(days=3)  # Jueves
        en_dos_semanas = hoy + timedelta(days=14)

        t_hoy = Tarea(id="1", name="T", materia="M", due_date=hoy.strftime("%d/%m/%Y 15:30"))
        self.assertEqual(t_hoy.fecha_visual(hoy_date=hoy), "Hoy a las 15:30")

        t_manana = Tarea(id="2", name="T", materia="M", due_date=manana.strftime("%d/%m/%Y 10:00"))
        self.assertEqual(t_manana.fecha_visual(hoy_date=hoy), "Mañana a las 10:00")

        t_semana = Tarea(id="3", name="T", materia="M", due_date=en_tres_dias.strftime("%d/%m/%Y 08:00"))
        self.assertEqual(t_semana.fecha_visual(hoy_date=hoy), "Jueves a las 08:00")

        t_lejana = Tarea(id="4", name="T", materia="M", due_date=en_dos_semanas.strftime("%d/%m/%Y 00:00"))
        self.assertEqual(t_lejana.fecha_visual(hoy_date=hoy), en_dos_semanas.strftime("%d/%m/%Y"))

        t_vacia = Tarea(id="5", name="T", materia="M", due_date="")
        self.assertEqual(t_vacia.fecha_visual(hoy_date=hoy), "No asignada")

    def test_serializacion_y_deserializacion_diccionario(self):
        """Verifica la conversión bidireccional entre Tarea y diccionario JSON."""
        datos_originales = {
            "name": "Proyecto Final",
            "materia": "Laboratorio I",
            "status": "in progress",
            "tags": "digital, examen",
            "due_date": "28/08/2026 23:59",
            "content": "Lineamientos del proyecto",
            "date_created": "22/08/2026 12:00",
        }
        tarea = Tarea.desde_diccionario("1001", datos_originales)
        self.assertEqual(tarea.id, "1001")
        self.assertEqual(tarea.name, "Proyecto Final")
        self.assertEqual(tarea.materia, "Laboratorio I")
        self.assertEqual(tarea.status, "in progress")

        diccionario_exportado = tarea.a_diccionario()
        self.assertEqual(diccionario_exportado, datos_originales)

    def test_auditoria_de_cambios(self):
        """Verifica la detección de modificaciones en nombre, fecha y etiquetas."""
        hoy = date(2026, 8, 22)
        t_ayer = Tarea(
            id="1",
            name="Ensayo borrador",
            materia="Lengua y literatura",
            tags="borrador",
            due_date="23/08/2026 18:00",
        )
        t_hoy = Tarea(
            id="1",
            name="Ensayo final",
            materia="Lengua y literatura",
            tags="final, digital",
            due_date="25/08/2026 20:00",
        )
        cambios = auditar_cambios(t_ayer, t_hoy, hoy)
        self.assertEqual(len(cambios), 3)
        self.assertTrue(any("se cambió el nombre" in c for c in cambios))
        self.assertTrue(any("se cambió la fecha" in c for c in cambios))
        self.assertTrue(any("cambió sus etiquetas" in c for c in cambios))

    def test_generador_changelog_integracion(self):
        """Verifica la generación del texto markdown del changelog."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        ayer_dict = {
            "1": {
                "name": "Tarea Activa",
                "materia": "Matemáticas",
                "status": "to do",
                "tags": "",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            },
            "2": {
                "name": "Tarea a Completar",
                "materia": "Física fundamental",
                "status": "to do",
                "tags": "",
                "due_date": "24/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        hoy_dict = {
            "1": {
                "name": "Tarea Activa Modificada",
                "materia": "Matemáticas",
                "status": "to do",
                "tags": "urgente",
                "due_date": "26/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            },
            "2": {
                "name": "Tarea a Completar",
                "materia": "Física fundamental",
                "status": "complete",
                "tags": "",
                "due_date": "24/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        changelog = generar_texto_changelog(ayer_dict, hoy_dict, fecha_referencia=fecha_ref)
        self.assertIn("`Changelog - Sábado (22/08/2026)`", changelog)
        self.assertIn("> Tareas completadas", changelog)
        self.assertIn("• *Tarea a Completar* (Física fundamental) se completó de la lista.", changelog)
        self.assertIn("> Actualizaciones y correcciones", changelog)
        self.assertIn("Tarea Activa Modificada", changelog)

    def test_generador_changelog_sin_cambios(self):
        """Verifica el mensaje estándar cuando no hay novedades respecto al día anterior."""
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
        changelog = generar_texto_changelog(tareas, tareas, fecha_referencia=fecha_ref)
        self.assertIn("• Sin novedades ni cambios en las tareas respecto al día anterior. Que milagro.", changelog)

    def test_generador_changelog_autocompletado_inactividad_sin_mutacion(self):
        """Verifica que las tareas vencidas se clasifiquen como completadas por inactividad sin mutar el objeto."""
        fecha_ref = datetime(2026, 8, 22, 10, 0)
        t_vencida = Tarea(
            id="10",
            name="Reporte Vencido",
            materia="Química",
            status="to do",
            due_date="20/08/2026",
        )
        hoy_map = {"10": t_vencida}
        changelog = generar_texto_changelog({}, hoy_map, fecha_referencia=fecha_ref)
        self.assertIn("• *Reporte Vencido* (Química) se completó por inactividad.", changelog)
        self.assertEqual(t_vencida.status, "to do")

    def test_preparar_datos_imagen(self):
        """Verifica el filtrado y ordenamiento de tareas para el generador de imágenes."""
        tareas = {
            "1": {
                "name": "Tarea Lejana",
                "materia": "Matemáticas",
                "status": "to do",
                "tags": "digital",
                "due_date": "30/08/2026",
                "content": "Detalles",
                "date_created": "20/08/2026",
            },
            "2": {
                "name": "Tarea Cercana",
                "materia": "Filosofía",
                "status": "to do",
                "tags": "",
                "due_date": "23/08/2026",
                "content": "Detalles",
                "date_created": "20/08/2026",
            },
            "3": {
                "name": "Tarea Ignorada",
                "materia": "Filosofía",
                "status": "to do",
                "tags": "personal",
                "due_date": "22/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            },
            "4": {
                "name": "Tarea Cerrada",
                "materia": "Inglés",
                "status": "complete",
                "tags": "",
                "due_date": "25/08/2026",
                "content": "",
                "date_created": "20/08/2026",
            }
        }
        hoy = date(2026, 8, 22)
        resultado = preparar_datos_tareas(tareas, hoy_date=hoy)
        # Solo deben quedar las 2 tareas activas no personales
        self.assertEqual(len(resultado), 2)
        # La primera debe ser la más cercana ("Tarea Cercana")
        self.assertEqual(resultado[0]["name"], "Tarea Cercana")
        self.assertEqual(resultado[1]["name"], "Tarea Lejana")

    def test_pie_mensaje_con_autor_configurado(self):
        """Verifica el pie de mensaje cuando se define un autor explícito o por variable de entorno."""
        pie = _obtener_pie_mensaje(1.234, autor="Juan")
        self.assertEqual(pie, "\n`Mensaje automatizado por Juan en 1.23 segundos`")

        pie_otro = _obtener_pie_mensaje(0.5, autor="Carlos")
        self.assertEqual(pie_otro, "\n`Mensaje automatizado por Carlos en 0.50 segundos`")

    def test_pie_mensaje_sin_autor_o_vacio(self):
        """Verifica que el pie de mensaje no falle y genere un formato seguro cuando el autor está vacío o ausente."""
        pie_vacio = _obtener_pie_mensaje(2.0, autor="")
        self.assertEqual(pie_vacio, "\n`Mensaje automatizado en 2.00 segundos`")

        pie_espacios = _obtener_pie_mensaje(2.0, autor="   ")
        self.assertEqual(pie_espacios, "\n`Mensaje automatizado en 2.00 segundos`")


if __name__ == "__main__":
    unittest.main()

