"""Módulo principal y punto de entrada para la sincronización de tareas de ClickUp.

Coordina la lectura del snapshot previo, la consulta concurrente a la API de ClickUp,
la generación de la tabla gráfica en JPEG y la composición del texto del changelog
en el portapapeles del sistema.
"""

import os
import time
import asyncio
from typing import Optional
import pyperclip
from dotenv import load_dotenv

from modulos.memoria import cargar_tareas_ayer, guardar_tareas_hoy
from modulos.api_clickup import obtener_tareas_api_async
from modulos.changelog import generar_texto_changelog
from generador_imagen import exportar_tabla_imagen

load_dotenv()


def _obtener_pie_mensaje(tiempo_calculo: float, autor: Optional[str] = None) -> str:
    """Genera la línea de pie de página con el tiempo de cálculo y autor configurable.

    Si no se proporciona un autor explícito, consulta la variable de entorno
    `AUTOR_NOMBRE` (o `CHANGELOG_AUTOR`). Si no está definida o contiene solo
    espacios en blanco, retorna un mensaje genérico seguro sin fallar.

    Args:
        tiempo_calculo: Tiempo transcurrido en segundos durante la ejecución.
        autor: Nombre opcional del autor para pruebas o sobreescritura directa.

    Returns:
        Cadena formateada en Markdown para el pie del changelog.
    """
    if autor is None:
        autor = os.getenv("AUTOR_NOMBRE") or os.getenv("CHANGELOG_AUTOR") or ""

    autor_limpio = autor.strip()
    if autor_limpio:
        return f"\n`Mensaje automatizado por {autor_limpio} en {tiempo_calculo:.2f} segundos`"
    return f"\n`Mensaje automatizado en {tiempo_calculo:.2f} segundos`"


async def ejecutar_async() -> None:
    """Orquesta la sincronización asíncrona completa de tareas y changelog.

    Carga el estado del día anterior, consulta la API de ClickUp concurrentemente,
    dispara la generación de la imagen en un hilo secundario, ensambla el texto
    del changelog, lo copia al portapapeles y guarda el snapshot actual.
    """
    tiempo_inicio = time.time()  # Medición de tiempo de ejecución
    
    tareas_ayer = cargar_tareas_ayer()
    
    print("Obteniendo tareas de ClickUp...")
    tareas_hoy = await obtener_tareas_api_async()

    if not tareas_hoy:
        print("No se encontraron datos en ClickUp para procesar.")
        return

    print("Generando imagen y changelog...")
    
    tarea_imagen = asyncio.to_thread(exportar_tabla_imagen, tareas_hoy, "Tareas_ClickUp.jpg")
    
    texto_final = generar_texto_changelog(tareas_ayer, tareas_hoy)
    
    await tarea_imagen

    tiempo_calculo = time.time() - tiempo_inicio
    texto_final += _obtener_pie_mensaje(tiempo_calculo)

    try:
        pyperclip.copy(texto_final)
        print("\n¡Copiado al portapapeles con éxito!")
    except Exception as e:
        print(f"\nNo se pudo copiar al portapapeles: {e}")

    guardar_tareas_hoy(tareas_hoy)

    print("\n========================================")
    print("Output listo:")
    print("========================================\n")
    print(texto_final)


def ejecutar() -> None:
    """Punto de entrada síncrono que envuelve la ejecución de `ejecutar_async`."""
    asyncio.run(ejecutar_async())


if __name__ == "__main__":
    ejecutar()