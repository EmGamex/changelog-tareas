"""Gestión de persistencia local y ciclo de vida de snapshots de tareas en JSON.

Controla la rotación de archivos diarios entre ayer y hoy, así como la regla
de congelamiento de historial durante los fines de semana.
"""

from datetime import datetime
import os
import json
from typing import Any, Dict

ARCHIVO_AYER: str = "clickup_snapshot_ayer.json"
ARCHIVO_HOY: str = "clickup_snapshot_hoy.json"


def cargar_tareas_ayer() -> Dict[str, Any]:
    """Carga el estado de las tareas del día anterior para realizar comparaciones.

    Si se detecta un cambio de día (y no es fin de semana), el archivo actual de
    'Hoy' rota para convertirse en el de 'Ayer'. Si es fin de semana, el historial
    se mantiene congelado sin cambios.

    Returns:
        Un diccionario con la estructura y datos de las tareas cargadas de ayer.
        Si no hay archivo de ayer o ocurre un error en la carga, retorna un
        diccionario vacío.
    """
    ahora = datetime.now()
    es_fin_de_semana = ahora.weekday() >= 5 
    fecha_hoy = ahora.strftime("%d/%m/%Y")

    if not es_fin_de_semana and os.path.exists(ARCHIVO_HOY):
        timestamp_mod = os.path.getmtime(ARCHIVO_HOY)
        fecha_mod = datetime.fromtimestamp(timestamp_mod).strftime("%d/%m/%Y")

        if fecha_mod != fecha_hoy:
            if os.path.exists(ARCHIVO_AYER):
                os.remove(ARCHIVO_AYER)
            os.rename(ARCHIVO_HOY, ARCHIVO_AYER)
            print("[SISTEMA] ¡Día nuevo detectado! El estado de ayer se ha actualizado.")
    elif es_fin_de_semana:
        print("[SISTEMA] Fin de semana detectado. Se mantiene el historial congelado.")

    if os.path.exists(ARCHIVO_AYER):
        try:
            with open(ARCHIVO_AYER, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Advertencia: No se pudo leer el historial base ({e}).")

    return {}


def guardar_tareas_hoy(tareas: Dict[str, Any]) -> None:
    """Guarda el estado actual de las tareas del día de hoy en un archivo JSON.

    Esta acción no se ejecuta si se detecta que es fin de semana.

    Args:
        tareas: Diccionario con los datos de las tareas obtenidas en la ejecución actual.
    """
    if datetime.now().weekday() >= 5:
        print("[SISTEMA] Fin de semana detectado. No se modificará el archivo de hoy.")
        return

    try:
        with open(ARCHIVO_HOY, 'w', encoding='utf-8') as f:
            json.dump(tareas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error al guardar el snapshot actual: {e}")