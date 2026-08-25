"""Motor de auditoría de diferencias y generación de reportes Changelog en Markdown.

Compara el snapshot previo de tareas contra el snapshot actual, clasificando
tareas completadas, nuevas asignaciones y modificaciones de campos.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Mapping, Optional, Union

from modulos.tarea import (
    Tarea,
    ESTADOS_COMPLETADOS,
    ETIQUETAS_IGNORADAS,
    auditar_cambios,
)


def _normalizar_a_tarea(id_tarea: str, item: Union[Tarea, Mapping[str, Any]]) -> Tarea:
    """Convierte un diccionario o instancia existente a un objeto Tarea.

    Args:
        id_tarea: Identificador de la tarea.
        item: Objeto Tarea o diccionario con datos de la tarea.

    Returns:
        Instancia de Tarea.
    """
    if isinstance(item, Tarea):
        return item
    return Tarea.desde_diccionario(id_tarea, dict(item))


def _normalizar_mapa_tareas(
    tareas: Mapping[str, Union[Tarea, Mapping[str, Any]]]
) -> Dict[str, Tarea]:
    """Normaliza un mapeo de tareas (que pueden ser dicts o Tareas) a un diccionario {id: Tarea}.

    Args:
        tareas: Mapeo indexado por id.

    Returns:
        Diccionario indexado por id con instancias de Tarea.
    """
    return {
        task_id: _normalizar_a_tarea(task_id, info)
        for task_id, info in (tareas or {}).items()
    }


def tiene_etiqueta_ignorada(tarea: Optional[Union[Tarea, Mapping[str, Any]]]) -> bool:
    """Verifica si una tarea contiene alguna etiqueta que deba ser ignorada (e.g. 'personal').

    Args:
        tarea: Objeto Tarea o diccionario que representa la información de la tarea.

    Returns:
        True si la tarea contiene alguna de las etiquetas ignoradas, False en caso contrario.
    """
    if not tarea:
        return False
    if isinstance(tarea, Tarea):
        return tarea.tiene_etiqueta_ignorada()
    return _normalizar_a_tarea("", tarea).tiene_etiqueta_ignorada()


def obtener_fecha_visual(raw_date: Any, hoy_date: date) -> str:
    """Convierte una fecha cruda a un formato natural en español (Hoy, Mañana, Lunes, etc.).

    Args:
        raw_date: La fecha en bruto (ejemplo: '05/08/2026 15:30').
        hoy_date: La fecha actual de referencia para calcular el formato relativo.

    Returns:
        Una cadena formateada con la fecha natural o 'No asignada'.
    """
    tarea_temp = Tarea(id="", name="", materia="", due_date=str(raw_date or ""))
    return tarea_temp.fecha_visual(hoy_date)


def es_tarea_nueva(t_hoy: Union[Tarea, Mapping[str, Any]], hoy_date: date) -> bool:
    """Verifica de forma segura si una tarea fue creada el día de hoy.

    Args:
        t_hoy: Objeto Tarea o diccionario con los datos actuales.
        hoy_date: La fecha de hoy contra la cual se compara la fecha de creación.

    Returns:
        True si la tarea fue creada hoy, False en caso contrario.
    """
    if isinstance(t_hoy, Tarea):
        return t_hoy.es_nueva(hoy_date)
    return _normalizar_a_tarea("", t_hoy).es_nueva(hoy_date)


# --- FUNCIONES AUXILIARES PARA EL CHANGELOG ---

def _buscar_tareas_archivadas(
    tareas_ayer: Dict[str, Tarea],
    tareas_hoy: Dict[str, Tarea]
) -> List[str]:
    """Detecta tareas que estaban en la lista de ayer pero desaparecieron el día de hoy.

    Args:
        tareas_ayer: Diccionario de tareas normalizadas del día anterior.
        tareas_hoy: Diccionario de tareas normalizadas de hoy.

    Returns:
        Una lista de strings describiendo las tareas que se consideraron
        completadas/archivadas por haber desaparecido de la lista.
    """
    completadas: List[str] = []
    for task_id, t_ayer in tareas_ayer.items():
        if t_ayer.tiene_etiqueta_ignorada():
            continue
        if task_id not in tareas_hoy:
            if t_ayer.status not in ESTADOS_COMPLETADOS:
                completadas.append(f"• *{t_ayer.name}* ({t_ayer.materia}) se completó (archivada/cerrada).\n")
        elif tareas_hoy[task_id].tiene_etiqueta_ignorada():
            continue
    return completadas


def _generar_texto_tarea_nueva(t_hoy: Tarea, hoy_date: date) -> str:
    """Genera el texto descriptivo en Markdown para una tarea recién agregada.

    Args:
        t_hoy: Instancia de Tarea con los datos actuales.
        hoy_date: La fecha actual de referencia.

    Returns:
        Cadena formateada en Markdown con los detalles de la nueva tarea.
    """
    tag_part = f" con etiqueta *{t_hoy.tags}*" if t_hoy.tags else ""
    fecha_visual = t_hoy.fecha_visual(hoy_date)
    fecha_part = f" y fecha límite para el *{fecha_visual}*" if t_hoy.due_date else " (sin fecha límite)"

    return f"• *{t_hoy.name}* ({t_hoy.materia}) se agregó a la lista{tag_part}{fecha_part}.\n"


def construir_texto_final(
    dia_semana: str,
    fecha_encabezado: str,
    completadas: List[str],
    nuevas: List[str],
    actualizaciones: List[str]
) -> str:
    """Ensambla las secciones de tareas y cambios en un único string formateado en Markdown.

    Args:
        dia_semana: Nombre del día de la semana actual.
        fecha_encabezado: Fecha actual formateada como string.
        completadas: Lista de líneas de texto con tareas completadas.
        nuevas: Lista de líneas de texto con nuevas tareas.
        actualizaciones: Lista de líneas de texto con actualizaciones.

    Returns:
        El changelog completo en formato Markdown.
    """
    output: List[str] = [f"`Changelog - {dia_semana} ({fecha_encabezado})`"]
    hubo_cambios = False

    for titulo, lista in [
        ("\n> Tareas completadas", completadas),
        ("> Nuevas tareas añadidas", nuevas),
        ("> Actualizaciones y correcciones", actualizaciones),
    ]:
        if lista:
            output.append(titulo)
            output.extend(lista)
            hubo_cambios = True

    if not hubo_cambios:
        output.append("\n• Sin novedades ni cambios en las tareas respecto al día anterior. Que milagro.")

    return "\n".join(output)


def generar_texto_changelog(
    tareas_ayer: Mapping[str, Union[Tarea, Mapping[str, Any]]],
    tareas_hoy: Mapping[str, Union[Tarea, Mapping[str, Any]]]
) -> str:
    """Orquesta la evaluación del estado de tareas entre ayer y hoy para generar el changelog.

    Args:
        tareas_ayer: Mapeo de tareas del día de ayer indexadas por ID.
        tareas_hoy: Mapeo de tareas de hoy indexadas por ID.

    Returns:
        Changelog completo en formato Markdown listo para su presentación o envío.
    """
    hoy = datetime.now()
    hoy_date = hoy.date()

    dias_espanol = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dia_semana = dias_espanol[hoy.weekday()]
    fecha_encabezado = hoy.strftime("%d/%m/%Y")

    mapa_ayer = _normalizar_mapa_tareas(tareas_ayer)
    mapa_hoy = _normalizar_mapa_tareas(tareas_hoy)

    completadas = _buscar_tareas_archivadas(mapa_ayer, mapa_hoy)
    nuevas: List[str] = []
    actualizaciones: List[str] = []

    for task_id, t_hoy in mapa_hoy.items():
        if t_hoy.tiene_etiqueta_ignorada():
            continue

        t_ayer = mapa_ayer.get(task_id)
        auto_completed = t_hoy.completada_por_inactividad(hoy_date)
        if auto_completed:
            t_hoy.status = "complete"

        es_nueva = t_hoy.es_nueva(hoy_date)

        if t_hoy.status in ESTADOS_COMPLETADOS:
            if auto_completed:
                completadas.append(f"• Se completo la tarea {t_hoy.name} ({t_hoy.materia}) por inactividad\n")
            elif es_nueva:
                nuevas.append(f"• *{t_hoy.name}* ({t_hoy.materia}) se creó y completó el día de hoy.\n")
            elif not t_ayer or t_ayer.status not in ESTADOS_COMPLETADOS:
                completadas.append(f"• *{t_hoy.name}* ({t_hoy.materia}) se completó de la lista.\n")
            continue

        if es_nueva:
            nuevas.append(_generar_texto_tarea_nueva(t_hoy, hoy_date))
            continue

        if t_ayer:
            cambios_detectados = auditar_cambios(t_ayer, t_hoy, hoy_date)
            if cambios_detectados:
                detalles = ", ".join(cambios_detectados)
                actualizaciones.append(f"• *{t_hoy.name}* ({t_hoy.materia}): {detalles}.\n")

    return construir_texto_final(dia_semana, fecha_encabezado, completadas, nuevas, actualizaciones)