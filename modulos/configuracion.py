"""Módulo de gestión de configuración, variables de entorno y descubrimiento de ClickUp.

Centraliza la lectura y persistencia en el archivo `.env`, la validación de estructuras
y el autodescubrimiento jerárquico de listas y materias desde la API de ClickUp.
"""

import os
import json
import dotenv
import httpx
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

API_TOKEN: Optional[str] = os.getenv("CLICKUP_API_TOKEN")

BASE_URL: str = "https://api.clickup.com/api/v2"


def obtener_token_api() -> Optional[str]:
    """Retorna el token de autenticación configurado para la API de ClickUp.

    Returns:
        El token de API como string, o None si no está definido.
    """
    return os.getenv("CLICKUP_API_TOKEN") or API_TOKEN


def obtener_nombre_autor() -> str:
    """Retorna el nombre configurado para firmar el changelog.

    Returns:
        El nombre del autor limpio, o una cadena vacía si no está configurado.
    """
    nombre = os.getenv("AUTOR_NOMBRE") or os.getenv("CHANGELOG_AUTOR") or ""
    return nombre.strip()


def guardar_listas_en_env(listas: Dict[str, str], ruta_env: Optional[str] = None) -> None:
    """Guarda el mapeo de listas en el archivo .env de forma segura y estructurada.

    Args:
        listas: Diccionario que mapea ID de lista a nombre legible de materia.
        ruta_env: Ruta opcional al archivo .env (si es None, busca el archivo más cercano).
    """
    json_listas = json.dumps(listas, ensure_ascii=False)
    os.environ["CLICKUP_LISTAS_MATERIAS"] = json_listas

    archivo_env = ruta_env or dotenv.find_dotenv()
    if not archivo_env:
        archivo_env = ".env"

    try:
        dotenv.set_key(archivo_env, "CLICKUP_LISTAS_MATERIAS", json_listas)
    except Exception as e:
        print(f"Advertencia: No se pudo escribir CLICKUP_LISTAS_MATERIAS en {archivo_env}: {e}")


async def autodescubrir_listas_clickup_async(client: httpx.AsyncClient) -> Dict[str, str]:
    """Descubre automáticamente todas las listas accesibles en la cuenta de ClickUp.

    Explora la jerarquía completa de Workspaces (/team), Espacios (/space), Listas
    sin carpeta (/list) y Carpetas con sub-listas (/folder).

    Args:
        client: Cliente asíncrono httpx configurado con cabeceras de autorización.

    Returns:
        Diccionario con identificadores de lista como claves y sus nombres como valores.
    """
    mapa_listas: Dict[str, str] = {}
    try:
        resp_teams = await client.get(f"{BASE_URL}/team")
        resp_teams.raise_for_status()
        teams = resp_teams.json().get("teams", [])

        for team in teams:
            team_id = team.get("id")
            if not team_id:
                continue

            resp_spaces = await client.get(f"{BASE_URL}/team/{team_id}/space", params={"archived": "false"})
            if resp_spaces.status_code != 200:
                continue
            spaces = resp_spaces.json().get("spaces", [])

            for space in spaces:
                space_id = space.get("id")
                if not space_id:
                    continue

                # 1. Listas directas sin carpeta
                resp_lists = await client.get(f"{BASE_URL}/space/{space_id}/list", params={"archived": "false"})
                if resp_lists.status_code == 200:
                    for item_list in resp_lists.json().get("lists", []):
                        lid = str(item_list.get("id", ""))
                        lname = item_list.get("name", "").strip()
                        if lid and lname:
                            mapa_listas[lid] = lname

                # 2. Listas contenidas dentro de carpetas
                resp_folders = await client.get(f"{BASE_URL}/space/{space_id}/folder", params={"archived": "false"})
                if resp_folders.status_code == 200:
                    for folder in resp_folders.json().get("folders", []):
                        for item_list in folder.get("lists", []):
                            lid = str(item_list.get("id", ""))
                            lname = item_list.get("name", "").strip()
                            if lid and lname:
                                mapa_listas[lid] = lname

    except Exception as e:
        print(f"Aviso durante el autodescubrimiento de listas de ClickUp: {e}")

    return mapa_listas


async def obtener_mapa_listas_async(client: httpx.AsyncClient) -> Dict[str, str]:
    """Resuelve el mapeo de listas a consultar desde variables de entorno o autodescubrimiento.

    Si `CLICKUP_LISTAS_MATERIAS` existe y contiene un JSON válido, lo retorna.
    Si no existe o está vacía, ejecuta el autodescubrimiento por API y lo guarda en `.env`.
    Si no se encuentran listas, retorna un diccionario vacío con una advertencia informativa.

    Args:
        client: Cliente asíncrono httpx.

    Returns:
        Diccionario con el mapeo de ID de lista a nombre de materia.
    """
    env_listas = os.getenv("CLICKUP_LISTAS_MATERIAS")
    if env_listas and env_listas.strip():
        try:
            cargadas = json.loads(env_listas)
            if isinstance(cargadas, dict) and cargadas:
                return {str(k): str(v) for k, v in cargadas.items()}
        except Exception:
            print("Advertencia: El formato de CLICKUP_LISTAS_MATERIAS en .env no es un JSON válido. Reintentando detección...")

    print("Detectando listas de ClickUp automáticamente...")
    listas_descubiertas = await autodescubrir_listas_clickup_async(client)

    if listas_descubiertas:
        print(f"¡Se detectaron {len(listas_descubiertas)} listas en ClickUp y se guardaron en .env!")
        guardar_listas_en_env(listas_descubiertas)
        return listas_descubiertas

    print("Aviso: No se encontraron listas configuradas ni se pudieron autodetectar.")
    print("Verifique su CLICKUP_API_TOKEN o defina CLICKUP_LISTAS_MATERIAS en el archivo .env.")
    return {}
