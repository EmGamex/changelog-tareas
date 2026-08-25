"""Motor gráfico basado en Pillow para la composición de la tabla visual de tareas.

Procesa las tareas activas, calcula dinámicamente las dimensiones requeridas
y dibuja una tabla en formato JPEG con columnas de materia, tarea, fecha y etiquetas.
"""

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date
import textwrap
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from modulos.tarea import Tarea

ESTILOS_MATERIAS: Dict[str, Dict[str, str]] = {
    "matemáticas": {"bg": "#ffb300", "text": "#111111"},
    "filosofía": {"bg": "#8e24aa", "text": "#ffffff"},
    "ingles": {"bg": "#ec407a", "text": "#ffffff"},
    "física fundamental": {"bg": "#00acc1", "text": "#111111"},
    "lengua y literatura": {"bg": "#fb8c00", "text": "#111111"},
    "tejido social": {"bg": "#1e88e5", "text": "#ffffff"},
    "extracurricular": {"bg": "#43a047", "text": "#ffffff"},
    "expresión artistica": {"bg": "#3949ab", "text": "#ffffff"},
    "laboratorio i": {"bg": "#00897b", "text": "#ffffff"},
    "contabilidad": {"bg": "#78909c", "text": "#111111"},
    "técnicas de investigacion": {"bg": "#f4511e", "text": "#ffffff"},
    "computacion": {"bg": "#5e35b1", "text": "#ffffff"},
    "educación física": {"bg": "#e53935", "text": "#ffffff"},
}

ESTILO_MATERIA_DEFECTO: Dict[str, str] = {"bg": "#3f3f46", "text": "#ffffff"}

ESTILOS_ETIQUETAS: Dict[str, Dict[str, str]] = {
    "fisico": {"bg": "#2a3644", "text": "#ffffff"},
    "digital": {"bg": "#dc2626", "text": "#ffffff"},
    "opcional": {"bg": "#064e3b", "text": "#34d399"},
    "falta info.": {"bg": "#2e1065", "text": "#c084fc"},
    "falta info": {"bg": "#2e1065", "text": "#c084fc"},
}

ESTILO_DEFECTO_TAG: Dict[str, str] = {"bg": "#3f3f46", "text": "#ffffff"}


def _calcular_alturas_y_texto(desc_original: str, tags_original: str = "") -> Tuple[List[str], int]:
    """Aplica textwrap a la descripción de la tarea y calcula la altura vertical requerida
    teniendo en cuenta tanto las líneas de descripción como las filas de etiquetas.

    Args:
        desc_original: La descripción completa de la tarea.
        tags_original: Las etiquetas en formato string separadas por comas.

    Returns:
        Una tupla conteniendo:
            - Una lista de strings (líneas ajustadas por textwrap).
            - Un entero con la altura en píxeles que ocupará la fila correspondiente.
    """
    desc_lineas = textwrap.wrap(desc_original, width=55) if desc_original else []
    alto_desc = max(90, 54 + (len(desc_lineas) * 28) + 20) if desc_lineas else 90

    tags = [t.strip() for t in tags_original.split(",") if t.strip()] if tags_original else []
    if tags:
        filas_tags = max(1, (len(tags) + 2) // 3)
        alto_tags = 18 + (filas_tags * 58) + 14
        alto_esta_fila = max(alto_desc, alto_tags)
    else:
        alto_esta_fila = alto_desc

    return desc_lineas, alto_esta_fila


def preparar_datos_tareas(
    tareas: Mapping[str, Union[Tarea, Mapping[str, Any]]],
    hoy_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Filtra las tareas completadas o ignoradas y estructura los datos para el renderizado.

    Las tareas activas se ordenan cronológicamente según su fecha límite.

    Args:
        tareas: Mapeo de tareas indexado por ID de tarea.
        hoy_date: Fecha de referencia para evaluar vigencia y fechas relativas.

    Returns:
        Una lista de diccionarios de tareas con datos de formato añadidos y ordenados.
    """
    hoy_date = hoy_date or datetime.now().date()
    tareas_procesadas = []

    for task_id, item in (tareas or {}).items():
        tarea = item if isinstance(item, Tarea) else Tarea.desde_diccionario(task_id, dict(item))

        if tarea.esta_completada(hoy_date):
            continue

        if tarea.tiene_etiqueta_ignorada():
            continue

        fecha_visual = tarea.fecha_visual(hoy_date)
        fecha_sort = tarea.fecha_ordenamiento()
        desc_lineas, alto_esta_fila = _calcular_alturas_y_texto(tarea.content, tarea.tags)

        info_dict = tarea.a_diccionario()
        info_dict.update({
            "id": task_id,
            "fecha_sort": fecha_sort,
            "fecha_visual": fecha_visual,
            "desc_lineas": desc_lineas,
            "alto_fila_dinamico": alto_esta_fila,
        })
        tareas_procesadas.append(info_dict)

    tareas_procesadas.sort(key=lambda x: x["fecha_sort"])
    return tareas_procesadas


# 3. LÓGICA DE DIBUJO Y RENDERIZADO (UI)

def _cargar_fuentes() -> Tuple[Any, Any, Any]:
    """Carga y retorna las fuentes TTF para renderizar texto.

    Returns:
        Una tupla con tres objetos de fuente Pillow (fuente_titulo, fuente_texto, fuente_desc).
        Si falla la carga de fuentes locales, se retorna la fuente por defecto.
    """
    try:
        return (
            ImageFont.truetype("arial.ttf", 40),  # titulo
            ImageFont.truetype("arial.ttf", 30),  # texto
            ImageFont.truetype("arial.ttf", 22),  # desc
        )
    except IOError:
        default = ImageFont.load_default()
        return default, default, default


def _obtener_ancho_texto(dibujo: Any, texto: str, fuente: Any) -> float:
    """Helper para medir el ancho del texto compatible entre versiones de Pillow.

    Args:
        dibujo: Objeto ImageDraw de Pillow para realizar mediciones auxiliares si es necesario.
        texto: Cadena de texto a medir.
        fuente: Objeto de tipo fuente de Pillow.

    Returns:
        El ancho calculado para el texto en píxeles.
    """
    try:
        return fuente.getlength(texto)
    except AttributeError:
        return dibujo.textbbox((0, 0), texto, font=fuente)[2]


def _dibujar_encabezado(
    dibujo: Any,
    ancho_imagen: int,
    margen_superior: int,
    columnas: Dict[str, Tuple[int, int]],
    fuente_titulo: Any
) -> None:
    """Dibuja la barra superior del encabezado con los títulos de las columnas.

    Args:
        dibujo: Objeto de dibujo sobre el cual pintar.
        ancho_imagen: El ancho total de la imagen.
        margen_superior: El alto vertical reservado para el encabezado.
        columnas: Diccionario que define los rangos de coordenadas de cada columna.
        fuente_titulo: Objeto de fuente Pillow para los títulos.
    """
    dibujo.rectangle([(0, 0), (ancho_imagen, margen_superior - 20)], fill="#2a2a35")
    for titulo, (x_inicio, _) in columnas.items():
        dibujo.text((x_inicio, 30), titulo, font=fuente_titulo, fill="#ffffff")


def _dibujar_pildora_materia(dibujo: Any, info: Dict[str, Any], y_actual: int, fuente_texto: Any) -> None:
    """Dibuja la píldora de color de la materia con un icono circular representativo.

    Args:
        dibujo: Objeto de dibujo sobre el cual pintar.
        info: Diccionario con la información de la tarea.
        y_actual: Coordenada Y actual de la fila.
        fuente_texto: Objeto de fuente Pillow para el texto de la materia.
    """
    materia = info["materia"]
    estilo_m = ESTILOS_MATERIAS.get(materia.lower().strip(), ESTILO_MATERIA_DEFECTO)
    ancho_txt = _obtener_ancho_texto(dibujo, materia, fuente_texto)

    m_x1, m_y1 = 40, y_actual + 18
    m_x2 = min(480, m_x1 + 44 + ancho_txt + 16)
    m_y2 = y_actual + 72

    dibujo.rounded_rectangle([(m_x1, m_y1), (m_x2, m_y2)], radius=27, fill=estilo_m["bg"])
    cx, cy = m_x1 + 30, m_y1 + 27
    dibujo.ellipse([(cx - 14, cy - 14), (cx + 14, cy + 14)], outline=estilo_m["text"], width=4)
    dibujo.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=estilo_m["text"])
    dibujo.text((m_x1 + 56, y_actual + 26), materia, font=fuente_texto, fill=estilo_m["text"])


def _dibujar_tarea_y_descripcion(
    dibujo: Any,
    info: Dict[str, Any],
    y_actual: int,
    fuente_texto: Any,
    fuente_desc: Any
) -> None:
    """Dibuja el nombre de la tarea y renderiza sus líneas de descripción.

    Args:
        dibujo: Objeto de dibujo sobre el cual pintar.
        info: Diccionario con la información de la tarea.
        y_actual: Coordenada Y actual de la fila.
        fuente_texto: Fuente para el título de la tarea.
        fuente_desc: Fuente para el cuerpo de la descripción de la tarea.
    """
    y_titulo = y_actual + 18 if info["desc_lineas"] else y_actual + 26
    dibujo.text((500, y_titulo), info["name"][:40], font=fuente_texto, fill="#ffffff")

    y_linea = y_actual + 58
    for linea in info["desc_lineas"]:
        dibujo.text((500, y_linea), linea, font=fuente_desc, fill="#a1a1aa")
        y_linea += 28


def _dibujar_pildoras_etiquetas(
    dibujo: Any,
    info: Dict[str, Any],
    y_actual: int,
    fuente_texto: Any,
    x_inicio: int = 1460,
    x_limite: int = 1960
) -> None:
    """Itera sobre las etiquetas de la tarea y las dibuja como píldoras redondeadas.
    Permite el salto de línea si hay más etiquetas de las que caben en el ancho disponible.

    Si no hay etiquetas, renderiza un texto indicador de "Ninguna".

    Args:
        dibujo: Objeto de dibujo sobre el cual pintar.
        info: Diccionario con la información de la tarea.
        y_actual: Coordenada Y actual de la fila.
        fuente_texto: Objeto de fuente Pillow para el texto de la etiqueta.
        x_inicio: Coordenada X inicial de la columna de etiquetas.
        x_limite: Coordenada X máxima antes de forzar salto de línea.
    """
    if not info["tags"]:
        dibujo.text((x_inicio, y_actual + 26), "Ninguna", font=fuente_texto, fill="#55555c")
        return

    x_pildora = x_inicio
    y_pildora = y_actual + 18
    tags = [t.strip() for t in info["tags"].split(",") if t.strip()]

    for tag in tags:
        estilo_t = ESTILOS_ETIQUETAS.get(tag.lower(), ESTILO_DEFECTO_TAG)
        ancho_texto_t = _obtener_ancho_texto(dibujo, tag, fuente_texto)
        ancho_pildora = ancho_texto_t + 32

        if x_pildora + ancho_pildora > x_limite and x_pildora > x_inicio:
            x_pildora = x_inicio
            y_pildora += 58

        pildora_x2 = x_pildora + ancho_pildora
        dibujo.rounded_rectangle([(x_pildora, y_pildora), (pildora_x2, y_pildora + 54)], radius=27, fill=estilo_t["bg"])
        dibujo.text((x_pildora + 16, y_pildora + 8), tag, font=fuente_texto, fill=estilo_t["text"])
        x_pildora = pildora_x2 + 12


def exportar_tabla_imagen(
    tareas: Mapping[str, Union[Tarea, Mapping[str, Any]]],
    archivo_salida: str = "Tareas_ClickUp.jpg"
) -> None:
    """Orquesta el dibujado completo de la tabla y la exporta a un archivo JPG.

    Calcula de manera dinámica la altura total de la imagen según la cantidad de tareas
    y sus descripciones.

    Args:
        tareas: Mapeo de tareas obtenidas desde ClickUp o instancias de Tarea.
        archivo_salida: Nombre o ruta de archivo donde guardar la imagen resultante.
    """
    if not tareas:
        print("[IMAGEN] No hay tareas para procesar.")
        return

    tareas_procesadas = preparar_datos_tareas(tareas)

    if not tareas_procesadas:
        print("[IMAGEN] No hay tareas activas para mostrar en la imagen.")
        return

    ancho_imagen = 2000
    margen_superior = 120
    alto_tareas_total = sum(t["alto_fila_dinamico"] for t in tareas_procesadas)
    alto_imagen = margen_superior + alto_tareas_total + 40

    columnas = {
        "Materia": (40, 460),
        "Tarea": (500, 1130),
        "Fecha Límite": (1160, 1430),
        "Etiquetas": (1460, 1960),
    }

    # Crear imagen RGB
    imagen = Image.new("RGB", (ancho_imagen, alto_imagen), "#1e1e24")
    dibujo = ImageDraw.Draw(imagen)
    fuente_titulo, fuente_texto, fuente_desc = _cargar_fuentes()

    _dibujar_encabezado(dibujo, ancho_imagen, margen_superior, columnas, fuente_titulo)

    # Dibuja Filas
    y_actual = margen_superior
    for idx, info in enumerate(tareas_procesadas):
        alto_fila = info["alto_fila_dinamico"]

        # Fondo y franjas intermitentes
        fondo_fila = "#25252d" if idx % 2 == 0 else "#1e1e24"
        dibujo.rectangle([(0, y_actual), (ancho_imagen, y_actual + alto_fila)], fill=fondo_fila)

        # Contenido de cada columna
        _dibujar_pildora_materia(dibujo, info, y_actual, fuente_texto)
        _dibujar_tarea_y_descripcion(dibujo, info, y_actual, fuente_texto, fuente_desc)
        dibujo.text((1160, y_actual + 26), info["fecha_visual"], font=fuente_texto, fill="#ffffff")  # Fecha
        _dibujar_pildoras_etiquetas(dibujo, info, y_actual, fuente_texto, x_inicio=1460, x_limite=1960)

        # Línea separadora
        dibujo.line([(0, y_actual + alto_fila), (ancho_imagen, y_actual + alto_fila)], fill="#2d2d37", width=2)
        y_actual += alto_fila

    imagen.convert("RGB").save(archivo_salida, format="JPEG", quality=85, optimize=False)
    print(f"[IMAGEN] ¡Tabla HD en JPEG generada con éxito en '{archivo_salida}'!")