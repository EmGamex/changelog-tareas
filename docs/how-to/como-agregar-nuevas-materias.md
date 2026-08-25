# Guía Práctica: Cómo Agregar Nuevas Materias o Listas

Esta guía explica cómo registrar nuevas listas de ClickUp en el sistema y definir su identidad visual en la tabla gráfica generada.

---

## Contexto

El sistema cuenta con un mecanismo de **autodescubrimiento automático** que detecta todas las listas de tu cuenta de ClickUp y las persiste en la variable `CLICKUP_LISTAS_MATERIAS` dentro de tu archivo `.env`.

Tienes dos métodos sencillos para agregar nuevas materias:

---

## Método 1: Autodescubrimiento Automático (Recomendado)

Si creas una o más listas nuevas en ClickUp, no necesitas buscar los IDs manualmente:

1. Abre tu archivo `.env`.
2. Elimina la línea que contiene `CLICKUP_LISTAS_MATERIAS` (o vacía su valor).
3. Ejecuta el script:
   ```bash
   python main.py
   ```
4. El sistema consultará la API de ClickUp, detectará todas las listas actuales (incluyendo las nuevas) y reescribirá la variable `CLICKUP_LISTAS_MATERIAS` actualizada en tu `.env`.

---

## Método 2: Agregar o Editar Manualmente en `.env`

Si prefieres registrar una lista específica o cambiar el nombre con el que se mostrará:

1. **Obtener el ID de la Lista:**
   Abre la lista en ClickUp y copia el número final de la URL en la barra del navegador:
   ```text
   https://app.clickup.com/123456789000/v/li/123456789999
   ```
   En este caso, el ID es `123456789999`.

2. **Editar `.env`:**
   Abre el archivo `.env` y añade la nueva clave/valor dentro del JSON de `CLICKUP_LISTAS_MATERIAS`:
   ```env
   CLICKUP_LISTAS_MATERIAS={"123456789012": "Matemáticas", "123456789999": "Química General"}
   ```

---

## Configurar el Estilo Visual en el Generador de Imagen

Para que la nueva materia tenga su propio color en la tabla JPEG:

1. Abre [generador_imagen.py](../../generador_imagen.py).
2. Añade el nombre de la materia (en minúsculas) al diccionario `ESTILOS_MATERIAS`:
   ```python
   ESTILOS_MATERIAS: Dict[str, Dict[str, str]] = {
       "matemáticas": {"bg": "#ffb300", "text": "#111111"},
       # ... materias existentes ...
       "química general": {"bg": "#009688", "text": "#ffffff"}
   }
   ```
   > **Nota:** Si una materia no tiene estilo definido en este diccionario, el sistema utilizará automáticamente `ESTILO_MATERIA_DEFECTO` (gris oscuro elegante).

---

## Validar la Configuración

Ejecuta el script principal:

```bash
python main.py
```

Comprueba que las tareas de la nueva lista se incluyan en el reporte Markdown y aparezcan con la píldora de color correspondiente en `Tareas_ClickUp.jpg`.

---

## Documentación Relacionada

- [Cómo personalizar reglas y etiquetas](como-personalizar-reglas-y-etiquetas.md)
- [Referencia de módulos](../reference/arquitectura-y-modulos.md)
- [Volver al inicio del proyecto](../../README.md)
