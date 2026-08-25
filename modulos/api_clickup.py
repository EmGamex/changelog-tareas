"""Cliente HTTP asíncrono para la consulta de tareas en la API v2 de ClickUp.

Gestiona la autenticación mediante token, la paginación automática de tareas
abiertas y cerradas, y la normalización de la estructura JSON recibida.
"""

import asyncio
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from modulos.configuracion import API_TOKEN, BASE_URL, obtener_mapa_listas_async


# --- FUNCIONES AUXILIARES DE RED Y FORMATEO ---

def _obtener_headers() -> Dict[str, str]:
    """Genera las cabeceras requeridas para autenticarse con la API de ClickUp.

    Returns:
        Un diccionario con los headers HTTP correspondientes.
    """
    return {
        "Authorization": API_TOKEN or "",
        "Content-Type": "application/json"
    }


def _formatear_fecha_limite(due_raw: Any) -> str:
    """Convierte la fecha límite en milisegundos de ClickUp a un string legible.

    Si la fecha límite coincide con la medianoche (12:00 AM) o con las 04:00 AM
    (común como default en ClickUp), se omite la hora y se retorna solo la fecha.

    Args:
        due_raw: Timestamp en milisegundos provisto por la API, o None.

    Returns:
        Una cadena formateada (e.g. "DD/MM/YYYY hh:mm AM/PM" o "DD/MM/YYYY")
        o vacío si no se provee la fecha.
    """
    if not due_raw:
        return ""
    fecha_completa = datetime.fromtimestamp(int(due_raw) / 1000).strftime("%d/%m/%Y %I:%M %p")
    if " 04:00 AM" in fecha_completa or " 12:00 AM" in fecha_completa:
        return datetime.fromtimestamp(int(due_raw) / 1000).strftime("%d/%m/%Y")
    return fecha_completa


def _formatear_fecha_creacion(created_raw: Any) -> str:
    """Convierte la fecha de creación en milisegundos de ClickUp a un string legible.

    Args:
        created_raw: Timestamp en milisegundos provisto por la API, o None.

    Returns:
        Una cadena formateada en formato "DD/MM/YYYY HH:MM", o vacío si es None.
    """
    if not created_raw:
        return ""
    return datetime.fromtimestamp(int(created_raw) / 1000).strftime("%d/%m/%Y %H:%M")


def _procesar_tarea(task: Dict[str, Any], list_name: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Extrae y limpia la información de una tarea cruda de ClickUp.

    Args:
        task: Diccionario con la información cruda de la tarea según la API de ClickUp.
        list_name: Nombre de la lista/materia a la que pertenece la tarea.

    Returns:
        Una tupla con (task_id, tarea_procesada).
        Si la tarea no tiene ID válido, retorna (None, None).
    """
    task_id = task.get('id')
    if not task_id:
        return None, None

    tags_list = [t.get('name', '').strip() for t in task.get('tags', [])]
    tags_clean = ", ".join(tags_list)

    tarea_procesada = {
        'name': task.get('name', '').strip(),
        'materia': list_name,
        'status': task.get('status', {}).get('status', '').lower().strip(),
        'tags': tags_clean,
        'due_date': _formatear_fecha_limite(task.get('due_date')),
        'content': task.get('description', '').strip(),
        'date_created': _formatear_fecha_creacion(task.get('date_created'))
    }
    return task_id, tarea_procesada


# --- FUNCIONES ASÍNCRONAS DE RED ---

async def _obtener_tareas_de_lista_async(client: httpx.AsyncClient, list_id: str) -> List[Dict[str, Any]]:
    """Consulta de forma asíncrona todas las tareas de una lista específica en ClickUp.

    Realiza una paginación automática para obtener tanto tareas abiertas como cerradas.

    Args:
        client: Cliente asíncrono httpx ya inicializado y configurado.
        list_id: Identificador de la lista de ClickUp.

    Returns:
        Una lista de diccionarios representando las tareas en su formato crudo.
    """
    tareas_lista: List[Dict[str, Any]] = []
    page = 0
    
    while True:
        url_tasks = f"{BASE_URL}/list/{list_id}/task"
        params = {"archived": "false", "include_closed": "true", "page": page}
        
        response = await client.get(url_tasks, params=params)
        response.raise_for_status()
        tasks = response.json().get('tasks', [])
        
        if not tasks:
            break
            
        tareas_lista.extend(tasks)
        page += 1
        
    return tareas_lista


async def _procesar_lista_directa(client: httpx.AsyncClient, list_id: str, list_name: str) -> Dict[str, Dict[str, Any]]:
    """Obtiene y procesa todas las tareas de una lista de ClickUp.

    Args:
        client: Cliente asíncrono httpx.
        list_id: Identificador de la lista en ClickUp.
        list_name: Nombre asignado a la materia de esta lista.

    Returns:
        Un diccionario de tareas procesadas indexadas por su ID de tarea.
    """
    tareas_crudas = await _obtener_tareas_de_lista_async(client, list_id)
    resultado: Dict[str, Dict[str, Any]] = {}
    for task in tareas_crudas:
        task_id, tarea_procesada = _procesar_tarea(task, list_name)
        if task_id and tarea_procesada:
            resultado[task_id] = tarea_procesada
            
    return resultado


async def obtener_tareas_api_async() -> Dict[str, Dict[str, Any]]:
    """Consulta de manera concurrente y asíncrona todas las tareas de las materias configuradas.

    Returns:
        Un diccionario global de todas las tareas obtenidas de todas las materias,
        donde la llave es el ID de la tarea y el valor es el diccionario procesado.
    """
    headers = _obtener_headers()
    tareas: Dict[str, Dict[str, Any]] = {}

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        try:
            mapa_listas = await obtener_mapa_listas_async(client)
            if not mapa_listas:
                print("No hay listas de ClickUp disponibles para procesar tareas.")
                return {}

            resultados = await asyncio.gather(
                *[_procesar_lista_directa(client, list_id, list_name) for list_id, list_name in mapa_listas.items()]
            )

            for tareas_lista in resultados:
                tareas.update(tareas_lista)

        except httpx.HTTPError as req_err:
            print(f"Error de red o de API: {req_err}")
        except Exception as e:
            print(f"Error inesperado al procesar los datos: {e}")

    return tareas


def obtener_tareas_api() -> Dict[str, Dict[str, Any]]:
    """Wrapper para obtener las tareas de ClickUp de forma sincrónica.

    Returns:
        El diccionario global de tareas procesadas indexadas por su ID.
    """
    return asyncio.run(obtener_tareas_api_async())