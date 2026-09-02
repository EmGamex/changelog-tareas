# Referencia Técnica: Arquitectura y Módulos

Este documento proporciona la especificación técnica completa de los componentes, funciones, tipos de datos, esquemas de almacenamiento y configuración del proyecto.

---

## Estructura General del Código

```text
automatizador_de_tareas_changelog/
├── main.py                     # Punto de entrada y orquestación asíncrona
├── generador_imagen.py         # Motor gráfico para renderizado de tablas en JPEG
├── requirements.txt            # Dependencias del proyecto
├── .env.example                # Plantilla de variables de entorno
├── modulos/
│   ├── __init__.py             # Inicializador y exportación de la API pública del paquete
│   ├── configuracion.py        # Gestión de variables .env y autodescubrimiento de ClickUp
│   ├── tarea.py                # Modelo de dominio, reglas de negocio y cálculo de fechas
│   ├── api_clickup.py          # Cliente HTTP asíncrono para extracción y parseo de tareas
│   ├── changelog.py            # Motor de auditoría de diferencias y formateo Markdown
│   └── memoria.py              # Gestión de persistencia y rotación de snapshots JSON
├── tests/
│   ├── test_tarea.py           # Pruebas unitarias de dominio, integración y fechas
│   ├── test_api_clickup.py     # Pruebas unitarias de extracción y normalización de tareas
│   └── test_configuracion.py   # Pruebas unitarias de variables de entorno y autodescubrimiento
├── clickup_snapshot_ayer.json  # Snapshot del estado base anterior
└── clickup_snapshot_hoy.json   # Snapshot del estado actual
```

---

## 1. Módulo de Dominio `modulos/tarea.py`

Encapsula la entidad fundamental `Tarea`, centralizando las reglas de negocio, clasificación de estados, exclusión de etiquetas, fechas relativas y auditoría de cambios.

### Constantes:
- `ESTADOS_COMPLETADOS: List[str]`: `["closed", "complete", "entregada", "hecha"]`
- `ETIQUETAS_IGNORADAS: List[str]`: `["personal"]`
- `DIAS_SEMANA_ESPANOL: List[str]`: `["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]`

### Clase `Tarea`:
- **Atributos:**
  - `id: str`: Identificador único de la tarea.
  - `name: str`: Título descriptivo.
  - `materia: str`: Nombre de la materia asignada.
  - `status: str`: Estado actual normalizado.
  - `tags: str`: Cadena de etiquetas separadas por comas.
  - `due_date: str`: Fecha límite en formato texto (`DD/MM/YYYY` o `DD/MM/YYYY HH:MM`).
  - `content: str`: Descripción de la tarea.
  - `date_created: str`: Fecha y hora de creación (`DD/MM/YYYY HH:MM`).

- **Métodos Principales:**
  - `tiene_etiqueta_ignorada() -> bool`: Determina si contiene etiquetas excluidas (ej. `personal`).
  - `conjunto_etiquetas() -> Set[str]`: Retorna un conjunto con las etiquetas en minúsculas y sin espacios.
  - `lista_etiquetas() -> List[str]`: Retorna una lista con las etiquetas limpias conservando el case original.
  - `due_date_obj() -> Optional[date]`: Extrae y parsea la fecha de vencimiento como un objeto `datetime.date`.
  - `esta_completada(hoy_date: Optional[date] = None) -> bool`: Valida si su estado es completado o si está vencida por inactividad (`due_date < hoy`).
  - `completada_por_inactividad(hoy_date: Optional[date] = None) -> bool`: Identifica tareas abiertas cuya fecha límite ya expiró.
  - `es_nueva(hoy_date: Optional[date] = None) -> bool`: Valida si fue creada en la fecha indicada.
  - `fecha_visual(hoy_date: Optional[date] = None) -> str`: Retorna el formato natural en español (`Hoy a las HH:MM`, `Mañana`, etc.).
  - `fecha_ordenamiento() -> date`: Retorna la fecha para ordenamiento cronológico (`date.max` si no tiene fecha).
  - `a_diccionario() -> Dict[str, Any]`: Serialización a formato compatible con snapshots JSON.
  - `desde_diccionario(id_tarea: str, datos: Dict[str, Any]) -> Tarea`: Deserialización desde datos crudos o JSON.

### Funciones de Comparación:
- `auditar_cambios(t_ayer: Tarea, t_hoy: Tarea, hoy_date: date) -> List[str]`: Compara y reporta diferencias en nombre, fecha de vencimiento y etiquetas entre dos estados de una tarea.
- `_auditar_nombre(t_ayer: Tarea, t_hoy: Tarea) -> Optional[str]`: Detecta cambios de título.
- `_auditar_fecha(t_ayer: Tarea, t_hoy: Tarea, hoy_date: date) -> Optional[str]`: Detecta cambios de fecha límite.
- `_auditar_etiquetas(t_ayer: Tarea, t_hoy: Tarea) -> Optional[str]`: Detecta altas, bajas o modificaciones de etiquetas.

---

## 2. Módulo `main.py`

Punto de entrada del sistema. Coordina la carga de memoria, la consulta asíncrona de ClickUp, la ejecución concurrente del renderizado de imagen y la copia final al portapapeles.

### Variables de Entorno:
- `AUTOR_NOMBRE` (o `CHANGELOG_AUTOR`): Nombre que firmará el pie de mensaje del changelog. Opcional (si no se define o está vacío, se utiliza un formato seguro por defecto).

### Funciones Principales:
- `_obtener_pie_mensaje(tiempo_calculo: float, autor: Optional[str] = None) -> str`:
  - Construye la línea final del changelog con el tiempo de ejecución y el autor configurado en `AUTOR_NOMBRE` (o `CHANGELOG_AUTOR`).
  - Si el autor no está configurado, es `None`, está vacío o contiene solo espacios en blanco, retorna un pie genérico seguro: `` `Mensaje automatizado en {tiempo_calculo:.2f} segundos` ``.
- `ejecutar_async() -> None`:
  - Carga el estado base mediante `cargar_tareas_ayer()`.
  - Obtiene las tareas actuales concurrentemente vía `obtener_tareas_api_async()`.
  - Dispara en un hilo secundario `asyncio.to_thread` la función `exportar_tabla_imagen` para evitar bloquear el bucle de eventos.
  - Genera el texto del changelog con `generar_texto_changelog`.
  - Concatena el pie de página mediante `_obtener_pie_mensaje(tiempo_calculo)`.
  - Copia el texto resultante al portapapeles del sistema utilizando `pyperclip.copy`.
  - Guarda el snapshot actual mediante `guardar_tareas_hoy`.
- `ejecutar() -> None`:
  - Envoltorio síncrono que ejecuta `asyncio.run(ejecutar_async())`.

---

## 3. Módulo `modulos/configuracion.py`

Centraliza la carga y gestión de variables de entorno, la persistencia en `.env` mediante `dotenv.set_key` y el autodescubrimiento jerárquico de listas en ClickUp.

### Variables de Entorno Administradas:
- `CLICKUP_API_TOKEN`: Token de autenticación personal para la API de ClickUp.
- `AUTOR_NOMBRE` (o `CHANGELOG_AUTOR`): Nombre para la firma del changelog.
- `CLICKUP_LISTAS_MATERIAS`: Mapeo JSON `{ "list_id": "Nombre Materia" }`.

### Constantes:
- `API_TOKEN: Optional[str]`: Token de ClickUp cargado al iniciar.
- `BASE_URL: str`: `"https://api.clickup.com/api/v2"`

### Funciones:
- `obtener_token_api() -> Optional[str]`: Retorna el token de autenticación configurado.
- `obtener_nombre_autor() -> str`: Retorna el nombre del autor limpio o cadena vacía.
- `guardar_listas_en_env(listas: Dict[str, str], ruta_env: Optional[str] = None) -> None`:
  - Escribe `CLICKUP_LISTAS_MATERIAS` en `.env` mediante `dotenv.set_key` preservando las demás configuraciones y comentarios.
- `autodescubrir_listas_clickup_async(client: httpx.AsyncClient) -> Dict[str, str]`:
  - Recorre la jerarquía de Workspaces (`/team`), Espacios (`/space`), Listas (`/list`) y Carpetas (`/folder`) para autodetectar materias.
- `obtener_mapa_listas_async(client: httpx.AsyncClient) -> Dict[str, str]`:
  - Resuelve las listas desde `.env` o ejecuta el autodescubrimiento si la variable no existe.

---

## 4. Módulo `modulos/api_clickup.py`

Cliente HTTP asíncrono enfocado exclusivamente en la consulta concurrente, paginación y normalización de tareas de ClickUp.

### Funciones:
- `obtener_tareas_api_async() -> Dict[str, Dict[str, Any]]`:
  - Abre un cliente `httpx.AsyncClient` con timeout de 10.0 segundos.
  - Obtiene el mapa de listas con `obtener_mapa_listas_async` y ejecuta consultas paralelas con `asyncio.gather`.
- `obtener_tareas_api() -> Dict[str, Dict[str, Any]]`:
  - Envoltorio síncrono que invoca `obtener_tareas_api_async` con `asyncio.run`.
- `_obtener_tareas_de_lista_async(client: httpx.AsyncClient, list_id: str) -> List[Dict[str, Any]]`:
  - Maneja la paginación automática mediante parámetros `page`, `archived=false` e `include_closed=true`.
- `_procesar_lista_directa(client: httpx.AsyncClient, list_id: str, list_name: str) -> Dict[str, Dict[str, Any]]`:
  - Obtiene y procesa las tareas de una lista específica retornando un diccionario indexado por ID.
- `_procesar_tarea(task: Dict[str, Any], list_name: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]`:
  - Normaliza la estructura cruda de ClickUp a un diccionario estandarizado.
- `_formatear_fecha_limite(due_raw: Any) -> str`: Convierte timestamps en milisegundos a fecha legible omitiendo horas por defecto (12:00 AM / 04:00 AM).
- `_formatear_fecha_creacion(created_raw: Any) -> str`: Convierte el timestamp de creación a `DD/MM/YYYY HH:MM`.
- `_obtener_headers() -> Dict[str, str]`: Genera cabeceras `Authorization` y `Content-Type`.

---

## 4. Módulo `modulos/changelog.py`

Implementa la lógica de negocio para comparar los estados de ayer y hoy y producir el changelog en Markdown basándose en la entidad `Tarea`.

### Alias de Tipos:
- `TareaEntrada = Union[Tarea, Mapping[str, Any]]`: Representa una tarea como instancia u objeto diccionario.
- `MapaTareas = Mapping[str, TareaEntrada]`: Mapeo indexado por identificador de tarea.

### Funciones:
- `generar_texto_changelog(tareas_ayer: Optional[MapaTareas], tareas_hoy: Optional[MapaTareas], fecha_referencia: Optional[datetime] = None) -> str`:
  - Función orquestadora del changelog. Evalúa tareas archivadas, nuevas, autocompletadas por inactividad y actualizaciones. Admite el parámetro `fecha_referencia` para pruebas deterministas.
- `construir_texto_final(dia_semana: str, fecha_encabezado: str, completadas: List[str], nuevas: List[str], actualizaciones: List[str]) -> str`:
  - Ensambla las secciones formateadas en Markdown con bloques de sección (`>`).
- `tiene_etiqueta_ignorada(tarea: Optional[TareaEntrada]) -> bool`: Helper público para evaluar etiquetas excluidas.
- `obtener_fecha_visual(raw_date: Any, hoy_date: date) -> str`: Transforma fechas crudas a fechas naturales.
- `es_tarea_nueva(t_hoy: TareaEntrada, hoy_date: date) -> bool`: Helper para verificar creación en el día.
- `_buscar_tareas_archivadas(tareas_ayer: Dict[str, Tarea], tareas_hoy: Dict[str, Tarea]) -> List[str]`: Detecta tareas que desaparecieron del snapshot actual.
- `_clasificar_evento_tarea(t_hoy: Tarea, t_ayer: Optional[Tarea], hoy_date: date) -> Tuple[Optional[str], Optional[str]]`: Evalúa una tarea individual clasificándola en completada, nueva o actualizada sin generar efectos secundarios en sus atributos.
- `_generar_texto_tarea_nueva(t_hoy: Tarea, hoy_date: date) -> str`: Genera el fragmento Markdown para altas de tareas.

---

## 5. Módulo `modulos/memoria.py`

Controla la persistencia local de los estados en formato JSON.

### Constantes:
- `ARCHIVO_AYER: str = "clickup_snapshot_ayer.json"`
- `ARCHIVO_HOY: str = "clickup_snapshot_hoy.json"`

### Funciones:
- `cargar_tareas_ayer() -> Dict[str, Any]`:
  - Verifica la fecha de última modificación de `clickup_snapshot_hoy.json`. Si pertenece a un día anterior (y no es fin de semana), rota el archivo a `clickup_snapshot_ayer.json`.
- `guardar_tareas_hoy(tareas: Dict[str, Any]) -> None`:
  - Persiste el estado actual en `clickup_snapshot_hoy.json`. Si es fin de semana, no altera los archivos.

---

## 6. Módulo `generador_imagen.py`

Motor gráfico basado en Pillow (`PIL`) para la composición visual de la tabla de tareas.

### Constantes de Estilo:
- `ESTILOS_MATERIAS: Dict[str, Dict[str, str]]`: Paletas de color `{bg, text}` por materia.
- `ESTILO_MATERIA_DEFECTO: Dict[str, str]`: Paleta fallback `{bg: "#3f3f46", text: "#ffffff"}`.
- `ESTILOS_ETIQUETAS: Dict[str, Dict[str, str]]`: Paletas de color para etiquetas (`fisico`, `digital`, `opcional`, `falta info.`).
- `ESTILO_DEFECTO_TAG: Dict[str, str]`: Paleta fallback para etiquetas no registradas.

### Funciones Principales:
- `exportar_tabla_imagen(tareas: Mapping[str, Union[Tarea, Mapping[str, Any]]], archivo_salida: str = "Tareas_ClickUp.jpg") -> None`:
  - Orquesta el renderizado completo, inicializa el canvas de 2000px de ancho y guarda el archivo JPEG con calidad 85%.
- `preparar_datos_tareas(tareas: Mapping[str, Union[Tarea, Mapping[str, Any]]]) -> List[Dict[str, Any]]`:
  - Filtra tareas cerradas o ignoradas, calcula saltos de línea con `textwrap` y ordena las tareas cronológicamente según su fecha límite.
- `_calcular_alturas_y_texto(desc_original: str, tags_original: str = "") -> Tuple[List[str], int]`:
  - Calcula la altura dinámica de cada fila en función de la longitud del texto y la cantidad de filas de etiquetas.
- `_cargar_fuentes() -> Tuple[Any, Any, Any]`:
  - Carga las fuentes tipográficas `arial.ttf` en tamaños 40, 30 y 22 px, o `ImageFont.load_default()` como respaldo.
- `_obtener_ancho_texto(dibujo: Any, texto: str, fuente: Any) -> float`:
  - Mide el ancho en píxeles de un texto asegurando compatibilidad entre versiones de Pillow.
- `_dibujar_encabezado(...) -> None`: Dibuja la barra de títulos superior (`Materia`, `Tarea`, `Fecha Límite`, `Etiquetas`).
- `_dibujar_pildora_materia(...) -> None`: Dibuja la cápsula coloreada de materia e icono circular.
- `_dibujar_tarea_y_descripcion(...) -> None`: Dibuja el título de la tarea y las líneas envueltas de descripción.
- `_dibujar_pildoras_etiquetas(...) -> None`: Dibuja las cápsulas de etiquetas con soporte para múltiples líneas.

---

## 7. Paquete `modulos/__init__.py`

Exporta los símbolos esenciales para la API pública interna:
```python
__all__ = [
    "Tarea",
    "ESTADOS_COMPLETADOS",
    "ETIQUETAS_IGNORADAS",
    "auditar_cambios",
    "cargar_tareas_ayer",
    "guardar_tareas_hoy",
    "obtener_tareas_api_async",
    "obtener_tareas_api",
    "generar_texto_changelog",
]
```

---

## 8. Esquema de Datos del Snapshot JSON

Cada tarea procesada en el diccionario se indexa por su `task_id` con el siguiente esquema retrocompatible:

```json
{
  "901709123456": {
    "name": "Entrega de Proyecto Final",
    "materia": "Laboratorio I",
    "status": "complete",
    "tags": "digital, grupal",
    "due_date": "24/08/2026 18:00",
    "content": "Descripción detallada de la tarea y criterios de evaluación.",
    "date_created": "20/08/2026 10:15"
  }
}
```

---

## 9. Suites de Pruebas Unitarias (`tests/`)

Las pruebas están basadas en el framework estándar `unittest` de Python:

### `tests/test_tarea.py`:
- Filtrado de etiquetas ignoradas (`test_etiquetas_ignoradas`).
- Clasificación de estados completados (`test_estados_completados_canonicos`).
- Autocompletado por inactividad y vencimiento (`test_autocompletado_por_inactividad_fecha_vencida`).
- Formateo de fechas relativas en español (`test_formateo_fechas_relativas`).
- Serialización y deserialización bidireccional (`test_serializacion_y_deserializacion_diccionario`).
- Auditoría granular de cambios en nombre, fecha y tags (`test_auditoria_de_cambios`).
- Generación integral de texto del changelog (`test_generador_changelog_integracion`).
- Preparación y ordenamiento cronológico para el motor gráfico (`test_preparar_datos_imagen`).
- Pie de página con autor configurado (`test_pie_mensaje_con_autor_configurado`).
- Pie de página seguro ante autor nulo o vacío (`test_pie_mensaje_sin_autor_o_vacio`).

### `tests/test_configuracion.py`:
- Lectura de autor limpio desde entorno (`test_obtener_nombre_autor`).
- Carga directa desde variable `CLICKUP_LISTAS_MATERIAS` en JSON (`test_obtener_mapa_listas_desde_env_valido`).
- Autodescubrimiento y persistencia en `.env` cuando la variable está ausente (`test_obtener_mapa_listas_ejecuta_autodescubrimiento_si_no_existe_env`).
- Retorno de diccionario vacío seguro ante fallo de descubrimiento (`test_obtener_mapa_listas_retorna_vacio_si_falla_autodescubrimiento`).
- Recorrido jerárquico simulado de ClickUp (`/team` -> `/space` -> `/list` / `/folder`) (`test_autodescubrir_listas_clickup_async_exitoso`).
- Persistencia en `.env` mediante `dotenv.set_key` (`test_guardar_listas_en_env`).

### `tests/test_api_clickup.py`:
- Generación de encabezados HTTP con autorización (`test_obtener_headers`).
- Formateo de fechas límite y de creación desde timestamps (`test_formatear_fecha_limite_y_creacion`).
- Normalización y extracción de campos de tareas (`test_procesar_tarea_extraccion_campos`).
- Descarte limpio de tareas sin ID válido (`test_procesar_tarea_sin_id_retorna_none`).
- Paginación automática asíncrona (`test_obtener_tareas_de_lista_async_paginacion`).
- Consulta asíncrona concurrente con `asyncio.gather` (`test_obtener_tareas_api_async_concurrencia`).
- Manejo seguro cuando no existen listas configuradas (`test_obtener_tareas_api_async_sin_listas`).

Comando de ejecución:
```bash
python -m unittest discover -s tests
```

---

## Documentación Relacionada

- [Primeros pasos](../tutorials/primeros-pasos.md)
- [Cómo ejecutar y agregar pruebas unitarias](../how-to/como-ejecutar-y-agregar-pruebas.md)
- [Resolución de problemas frecuentes](../how-to/resolucion-de-problemas.md)
- [Flujo y procesamiento de tareas](../explanation/flujo-y-procesamiento-de-tareas.md)
- [Ciclo de vida de snapshots](../explanation/ciclo-de-vida-snapshots-y-diferencias.md)
- [Volver al inicio del proyecto](../../README.md)
