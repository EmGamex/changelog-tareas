# Directrices del Proyecto - Automatizador de Tareas Changelog

## 1. Reglas de Negocio y Clasificación de Tareas
- **Etiquetas Ignoradas**: Nunca incluir en reportes ni en el changelog tareas que contengan la etiqueta `personal`.
- **Estados de Finalización**: Los estados que representan una tarea completada son: `closed`, `complete`, `entregada`, `hecha`.
- **Tareas Vencidas**: Si una tarea tiene fecha de vencimiento (`due_date`) anterior a la fecha de hoy, se clasifica como completada por inactividad.

## 2. Formato del Changelog y Textos Generados
- **Idioma**: Todo el contenido visible para el usuario (changelog, mensajes, fechas) debe estar en **Español**.
- **Fechas Relativas**:
  - Si es el mismo día: `Hoy` (o `Hoy a las HH:MM`).
  - Si es el día siguiente: `Mañana` (o `Mañana a las HH:MM`).
  - Dentro de la semana: Nombre del día (`Lunes`, `Martes`, etc.).
  - Más de una semana: `DD/MM/YYYY`.
- **Estructura Markdown**:
  - Título: `` `Changelog - {Día} ({DD/MM/YYYY})` ``
  - Bloques de sección con blockquote (`>`):
    - `> Tareas completadas`
    - `> Nuevas tareas añadidas`
    - `> Actualizaciones y correcciones`
  - Si no existen cambios: `• Sin novedades ni cambios en las tareas respecto al día anterior. Que milagro.`

## 3. Convenciones de Código Python
- Tipado explícito con el módulo `typing` en todas las firmas de función.
- Docstrings en español detallando propósito, parámetros (`Args:`) y valor de retorno (`Returns:`).
- Funciones auxiliares o privadas de módulo deben llevar prefijo `_`.

## 4. Consulta de Documentación del Proyecto
- **Documentación Diátaxis**: Siempre que sea necesario entender la arquitectura, realizar modificaciones, agregar materias, ajustar reglas de negocio o entender el ciclo de vida de snapshots, consultar la documentación en `README.md` y el directorio `docs/` (`docs/tutorials/`, `docs/how-to/`, `docs/reference/`, `docs/explanation/`).
