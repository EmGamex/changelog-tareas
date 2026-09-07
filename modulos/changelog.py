"""Motor de auditoría de diferencias y generación de reportes Changelog en Markdown.

Compara el snapshot previo de tareas contra el snapshot actual, clasificando
tareas completadas, nuevas asignaciones y modificaciones de campos.
"""

from datetime import datetime, date
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from modulos.tarea import (
    Tarea,
    ESTADOS_COMPLETADOS,
    ETIQUETAS_IGNORADAS,
    DIAS_SEMANA_ESPANOL,
    auditar_cambios,
)

try:
    from modulos import _changelog_nativo
    MOTOR_NATIVO_DISPONIBLE: bool = True
except ImportError:
    _changelog_nativo = None  # type: ignore[assignment]
    MOTOR_NATIVO_DISPONIBLE = False

TareaEntrada = Union[Tarea, Mapping[str, Any]]
MapaTareas = Mapping[str, TareaEntrada]


def _normalizar_a_tarea(id_tarea: str, item: TareaEntrada) -> Tarea:
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


def _normalizar_mapa_tareas(tareas: Optional[MapaTareas]) -> Dict[str, Tarea]:
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


def tiene_etiqueta_ignorada(tarea: Optional[TareaEntrada]) -> bool:
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


def es_tarea_nueva(t_hoy: TareaEntrada, hoy_date: date) -> bool:
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
                completadas.append(f"• *{t_ayer.name}* ({t_ayer.materia}) se completó (archivada/cerrada).")
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

    return f"• *{t_hoy.name}* ({t_hoy.materia}) se agregó a la lista{tag_part}{fecha_part}."


def _clasificar_evento_tarea(
    t_hoy: Tarea,
    t_ayer: Optional[Tarea],
    hoy_date: date
) -> Tuple[Optional[str], Optional[str]]:
    """Determina la categoría y el texto descriptivo de cambio para una tarea presente hoy.

    Args:
        t_hoy: Tarea en el estado del snapshot actual.
        t_ayer: Tarea en el estado del snapshot previo (si existía).
        hoy_date: Fecha de referencia para cálculos temporales.

    Returns:
        Tupla (categoria, texto) donde categoria es 'completadas', 'nuevas', 'actualizaciones' o None.
    """
    auto_completed = t_hoy.completada_por_inactividad(hoy_date)
    esta_cerrada = (t_hoy.status in ESTADOS_COMPLETADOS) or auto_completed
    es_nueva = t_hoy.es_nueva(hoy_date)

    if esta_cerrada:
        if auto_completed:
            return "completadas", f"• *{t_hoy.name}* ({t_hoy.materia}) se completó por inactividad."
        if es_nueva:
            return "nuevas", f"• *{t_hoy.name}* ({t_hoy.materia}) se creó y completó el día de hoy."
        if not t_ayer or t_ayer.status not in ESTADOS_COMPLETADOS:
            return "completadas", f"• *{t_hoy.name}* ({t_hoy.materia}) se completó de la lista."
        return None, None

    if es_nueva:
        return "nuevas", _generar_texto_tarea_nueva(t_hoy, hoy_date)

    if t_ayer:
        cambios = auditar_cambios(t_ayer, t_hoy, hoy_date)
        if cambios:
            detalles = ", ".join(cambios)
            return "actualizaciones", f"• *{t_hoy.name}* ({t_hoy.materia}): {detalles}."

    return None, None


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

    secciones = [
        ("> Tareas completadas", completadas),
        ("> Nuevas tareas añadidas", nuevas),
        ("> Actualizaciones y correcciones", actualizaciones),
    ]

    for titulo, lista in secciones:
        if lista:
            output.append(f"\n{titulo}")
            output.extend(lista)
            hubo_cambios = True

    if not hubo_cambios:
        output.append("\n• Sin novedades ni cambios en las tareas respecto al día anterior. Que milagro.")

    return "\n".join(output)


def generar_texto_changelog_python(
    tareas_ayer: Optional[MapaTareas],
    tareas_hoy: Optional[MapaTareas],
    fecha_referencia: Optional[datetime] = None
) -> str:
    """Genera el changelog utilizando la implementación pura en Python.

    Args:
        tareas_ayer: Mapeo de tareas del día de ayer indexadas por ID.
        tareas_hoy: Mapeo de tareas de hoy indexadas por ID.
        fecha_referencia: Fecha/hora de referencia opcional para pruebas y determinismo.

    Returns:
        Changelog completo en formato Markdown listo para su presentación o envío.
    """
    hoy = fecha_referencia if fecha_referencia is not None else datetime.now()
    hoy_date = hoy.date()

    dia_semana = DIAS_SEMANA_ESPANOL[hoy.weekday()]
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
        categoria, texto = _clasificar_evento_tarea(t_hoy, t_ayer, hoy_date)

        if not categoria or not texto:
            continue

        if categoria == "completadas":
            completadas.append(texto)
        elif categoria == "nuevas":
            nuevas.append(texto)
        elif categoria == "actualizaciones":
            actualizaciones.append(texto)

    return construir_texto_final(dia_semana, fecha_encabezado, completadas, nuevas, actualizaciones)


def generar_texto_changelog_nativo(
    tareas_ayer: Optional[MapaTareas],
    tareas_hoy: Optional[MapaTareas],
    fecha_referencia: Optional[datetime] = None
) -> str:
    """Genera el changelog utilizando la extensión acelerada nativa en C++.

    Args:
        tareas_ayer: Mapeo de tareas del día de ayer indexadas por ID.
        tareas_hoy: Mapeo de tareas de hoy indexadas por ID.
        fecha_referencia: Fecha/hora de referencia opcional para pruebas y determinismo.

    Returns:
        Changelog completo en formato Markdown.

    Raises:
        RuntimeError: Si el módulo compilado nativo no está disponible.
    """
    if not MOTOR_NATIVO_DISPONIBLE or _changelog_nativo is None:
        raise RuntimeError("El motor nativo en C++ (_changelog_nativo) no está disponible en este entorno.")

    hoy = fecha_referencia if fecha_referencia is not None else datetime.now()

    # Preparamos los diccionarios para la interfaz C++
    ayer_dict: Dict[str, Any] = {}
    if tareas_ayer:
        for tid, t in tareas_ayer.items():
            ayer_dict[str(tid)] = t.a_diccionario() if isinstance(t, Tarea) else dict(t)

    hoy_dict: Dict[str, Any] = {}
    if tareas_hoy:
        for tid, t in tareas_hoy.items():
            hoy_dict[str(tid)] = t.a_diccionario() if isinstance(t, Tarea) else dict(t)

    return _changelog_nativo.generar_texto_changelog_cpp(
        ayer_dict,
        hoy_dict,
        hoy.year,
        hoy.month,
        hoy.day
    )


def generar_texto_changelog(
    tareas_ayer: Optional[MapaTareas],
    tareas_hoy: Optional[MapaTareas],
    fecha_referencia: Optional[datetime] = None,
    usar_nativo: bool = True
) -> str:
    """Orquesta la evaluación del estado de tareas entre ayer y hoy para generar el changelog.

    Intenta utilizar el motor nativo en C++ si está disponible; de lo contrario,
    recurre automáticamente a la implementación pura en Python.

    Args:
        tareas_ayer: Mapeo de tareas del día de ayer indexadas por ID.
        tareas_hoy: Mapeo de tareas de hoy indexadas por ID.
        fecha_referencia: Fecha/hora de referencia opcional para pruebas y determinismo.
        usar_nativo: Booleano que indica si se debe preferir el motor nativo C++.

    Returns:
        Changelog completo en formato Markdown listo para su presentación o envío.
    """
    if usar_nativo and MOTOR_NATIVO_DISPONIBLE:
        try:
            return generar_texto_changelog_nativo(tareas_ayer, tareas_hoy, fecha_referencia)
        except Exception:
            pass  # Fallback seguro a Python ante cualquier excepción imprevista

    return generar_texto_changelog_python(tareas_ayer, tareas_hoy, fecha_referencia)