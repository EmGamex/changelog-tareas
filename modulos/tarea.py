"""Modelo de dominio y reglas de negocio para la gestión de tareas académicas.

Encapsula la entidad `Tarea`, la normalización de estados, exclusión de etiquetas,
cálculo de fechas relativas en español y algoritmos de auditoría de cambios.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple, Set

ESTADOS_COMPLETADOS: List[str] = ["closed", "complete", "entregada", "hecha"]
ETIQUETAS_IGNORADAS: List[str] = ["personal"]


@dataclass
class Tarea:
    """Representa una tarea académica y encapsula sus reglas de dominio y formato.

    Attributes:
        id: Identificador único de la tarea.
        name: Nombre o título de la tarea.
        materia: Nombre de la materia a la que pertenece la tarea.
        status: Estado actual de la tarea (ej. 'to do', 'complete', 'hecha').
        tags: Cadena con las etiquetas separadas por comas.
        due_date: Fecha y hora de vencimiento en formato texto (ej. 'DD/MM/YYYY HH:MM').
        content: Descripción o contenido detallado de la tarea.
        date_created: Fecha y hora de creación en formato texto (ej. 'DD/MM/YYYY HH:MM').
    """

    id: str
    name: str
    materia: str
    status: str = ""
    tags: str = ""
    due_date: str = ""
    content: str = ""
    date_created: str = ""

    def tiene_etiqueta_ignorada(self) -> bool:
        """Verifica si la tarea contiene alguna de las etiquetas ignoradas (ej. 'personal').

        Returns:
            True si contiene etiquetas ignoradas, False en caso contrario.
        """
        if not self.tags:
            return False
        tags_set = self.conjunto_etiquetas()
        return any(ign.lower() in tags_set for ign in ETIQUETAS_IGNORADAS)

    def conjunto_etiquetas(self) -> Set[str]:
        """Obtiene el conjunto de etiquetas normalizadas en minúsculas.

        Returns:
            Conjunto de cadenas con cada etiqueta limpia en minúsculas.
        """
        if not self.tags:
            return set()
        return {t.strip().lower() for t in self.tags.split(",") if t.strip()}

    def lista_etiquetas(self) -> List[str]:
        """Obtiene la lista de etiquetas limpias conservando el espaciado original.

        Returns:
            Lista de cadenas con cada etiqueta.
        """
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def due_date_obj(self) -> Optional[date]:
        """Extrae la fecha de vencimiento como un objeto date.

        Returns:
            Objeto date con la fecha de vencimiento, o None si no tiene fecha válida.
        """
        if not self.due_date or not self.due_date.strip():
            return None
        try:
            fecha_str = self.due_date.strip().split()[0]
            return datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except (ValueError, IndexError):
            return None

    def esta_completada(self, hoy_date: Optional[date] = None) -> bool:
        """Determina si la tarea está en estado completado o si está vencida por inactividad.

        Args:
            hoy_date: Fecha de referencia para evaluar vencimiento. Por defecto usa la fecha de hoy.

        Returns:
            True si el estado es completado o si la fecha de vencimiento ya expiró.
        """
        status_limpio = self.status.lower().strip()
        if status_limpio in ESTADOS_COMPLETADOS:
            return True

        if hoy_date is None:
            hoy_date = datetime.now().date()

        f_due = self.due_date_obj()
        if f_due is not None and f_due < hoy_date:
            return True

        return False

    def completada_por_inactividad(self, hoy_date: Optional[date] = None) -> bool:
        """Verifica si la tarea debe considerarse completada automáticamente por inactividad (vencida).

        Args:
            hoy_date: Fecha actual de referencia.

        Returns:
            True si el estado no es completado pero su fecha de vencimiento es anterior a hoy.
        """
        status_limpio = self.status.lower().strip()
        if status_limpio in ESTADOS_COMPLETADOS:
            return False

        if hoy_date is None:
            hoy_date = datetime.now().date()

        f_due = self.due_date_obj()
        return f_due is not None and f_due < hoy_date

    def es_nueva(self, hoy_date: Optional[date] = None) -> bool:
        """Verifica si la tarea fue creada en la fecha indicada.

        Args:
            hoy_date: Fecha de referencia contra la cual comparar. Por defecto hoy.

        Returns:
            True si la fecha de creación coincide con la fecha de referencia.
        """
        if not self.date_created:
            return False
        if hoy_date is None:
            hoy_date = datetime.now().date()
        try:
            fecha_str = self.date_created.strip().split()[0]
            return datetime.strptime(fecha_str, "%d/%m/%Y").date() == hoy_date
        except (ValueError, IndexError):
            return False

    def fecha_visual(self, hoy_date: Optional[date] = None) -> str:
        """Genera una representación textual legible de la fecha en español (Hoy, Mañana, Lunes, etc.).

        Args:
            hoy_date: Fecha de referencia. Por defecto la fecha actual.

        Returns:
            Cadena de texto con la fecha relativa o 'No asignada'.
        """
        if not self.due_date or not self.due_date.strip():
            return "No asignada"

        if hoy_date is None:
            hoy_date = datetime.now().date()

        try:
            partes = self.due_date.strip().split()
            fecha_str = partes[0]
            hora_str = " ".join(partes[1:]) if len(partes) > 1 else "00:00"

            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            limite_semana = hoy_date + timedelta(days=7)
            dias_espanol = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

            if fecha_obj == hoy_date:
                dia_texto = "Hoy"
            elif fecha_obj == hoy_date + timedelta(days=1):
                dia_texto = "Mañana"
            elif hoy_date <= fecha_obj <= limite_semana:
                dia_texto = dias_espanol[fecha_obj.weekday()]
            else:
                dia_texto = fecha_obj.strftime("%d/%m/%Y")

            if hora_str != "00:00":
                return f"{dia_texto} a las {hora_str}"
            return dia_texto
        except (ValueError, IndexError):
            return self.due_date

    def fecha_ordenamiento(self) -> date:
        """Retorna la fecha para ordenar tareas cronológicamente.

        Returns:
            Objeto date correspondiente a la fecha de vencimiento, o date.max si no tiene.
        """
        f_due = self.due_date_obj()
        return f_due if f_due is not None else date.max

    def a_diccionario(self) -> Dict[str, Any]:
        """Serializa la tarea a un diccionario compatible con el esquema de snapshot JSON.

        Returns:
            Diccionario con las claves y valores estandarizados de la tarea.
        """
        return {
            "name": self.name,
            "materia": self.materia,
            "status": self.status,
            "tags": self.tags,
            "due_date": self.due_date,
            "content": self.content,
            "date_created": self.date_created,
        }

    @classmethod
    def desde_diccionario(cls, id_tarea: str, datos: Dict[str, Any]) -> "Tarea":
        """Instancia un objeto Tarea a partir de un diccionario de datos crudos o deserializados.

        Args:
            id_tarea: Identificador de la tarea.
            datos: Diccionario con los campos de la tarea.

        Returns:
            Nueva instancia de Tarea.
        """
        return cls(
            id=str(id_tarea),
            name=str(datos.get("name", "Sin nombre")).strip(),
            materia=str(datos.get("materia", "Sin materia")).strip(),
            status=str(datos.get("status", "")).lower().strip(),
            tags=str(datos.get("tags", "")).strip(),
            due_date=str(datos.get("due_date", "")).strip(),
            content=str(datos.get("content", "")).strip(),
            date_created=str(datos.get("date_created", "")).strip(),
        )


def _auditar_nombre(t_ayer: Tarea, t_hoy: Tarea) -> Optional[str]:
    """Compara y audita si hubo un cambio en el nombre de la tarea.

    Args:
        t_ayer: Tarea en el estado anterior.
        t_hoy: Tarea en el estado actual.

    Returns:
        Mensaje descriptivo del cambio o None.
    """
    name_ayer = t_ayer.name or "Sin nombre"
    name_hoy = t_hoy.name or "Sin nombre"
    if name_ayer != name_hoy:
        return f"se cambió el nombre de '{name_ayer}' a '{name_hoy}'"
    return None


def _auditar_fecha(t_ayer: Tarea, t_hoy: Tarea, hoy_date: date) -> Optional[str]:
    """Compara y audita si hubo un cambio en la fecha de vencimiento de la tarea.

    Args:
        t_ayer: Tarea en el estado anterior.
        t_hoy: Tarea en el estado actual.
        hoy_date: Fecha actual de referencia.

    Returns:
        Mensaje descriptivo del cambio o None.
    """
    due_ayer = t_ayer.due_date
    due_hoy = t_hoy.due_date
    fecha_ayer_corta = due_ayer.split()[0] if due_ayer else ""
    fecha_hoy_corta = due_hoy.split()[0] if due_hoy else ""

    if fecha_ayer_corta != fecha_hoy_corta:
        prev_due = t_ayer.fecha_visual(hoy_date)
        new_due = t_hoy.fecha_visual(hoy_date)
        return f"se cambió la fecha del *{prev_due}* al *{new_due}*"
    return None


def _auditar_etiquetas(t_ayer: Tarea, t_hoy: Tarea) -> Optional[str]:
    """Compara y audita si hubo un cambio en las etiquetas de la tarea.

    Args:
        t_ayer: Tarea en el estado anterior.
        t_hoy: Tarea en el estado actual.

    Returns:
        Mensaje descriptivo del cambio o None.
    """
    tags_ayer_set = t_ayer.conjunto_etiquetas()
    tags_hoy_set = t_hoy.conjunto_etiquetas()

    if tags_ayer_set != tags_hoy_set:
        tags_ayer_str = t_ayer.tags
        tags_hoy_str = t_hoy.tags
        if not tags_ayer_set and tags_hoy_set:
            return f"se le agregaron las etiquetas *[{tags_hoy_str}]*"
        elif tags_ayer_set and not tags_hoy_set:
            return "se le quitaron las etiquetas"
        else:
            return f"cambió sus etiquetas de *[{tags_ayer_str}]* a *[{tags_hoy_str}]*"
    return None


def auditar_cambios(t_ayer: Tarea, t_hoy: Tarea, hoy_date: date) -> List[str]:
    """Compara los atributos de una tarea entre ayer y hoy.

    Args:
        t_ayer: Instancia de Tarea con el estado previo.
        t_hoy: Instancia de Tarea con el estado actual.
        hoy_date: Fecha actual de referencia.

    Returns:
        Lista de cadenas con las descripciones de los cambios detectados.
    """
    auditores = [
        _auditar_nombre(t_ayer, t_hoy),
        _auditar_fecha(t_ayer, t_hoy, hoy_date),
        _auditar_etiquetas(t_ayer, t_hoy),
    ]
    return [cambio for cambio in auditores if cambio is not None]
