# Guía Práctica: Cómo Personalizar Reglas y Etiquetas

Esta guía muestra cómo ajustar las reglas de negocio para ignorar ciertas etiquetas, configurar estados de tarea y personalizar el diseño visual de las etiquetas en la tabla generada.

---

## 1. Excluir Tareas por Etiquetas

Por regla de negocio, cualquier tarea que contenga una etiqueta configurada como ignorada será excluida automáticamente tanto del changelog como de la imagen renderizada.

### Ubicación centralizada:

En [modulos/tarea.py](../../modulos/tarea.py):

```python
ETIQUETAS_IGNORADAS: List[str] = ["personal", "borrador"]
```

Gracias a que los módulos [modulos/changelog.py](../../modulos/changelog.py) y [generador_imagen.py](../../generador_imagen.py) consumen el método `tarea.tiene_etiqueta_ignorada()`, cualquier etiqueta añadida a esta lista se excluirá de forma uniforme en todo el sistema sin necesidad de modificar múltiples archivos.

---

## 2. Configurar Estados de Tareas Completadas

El sistema reconoce una lista canónica de estados para clasificar una tarea como completada o entregada.

### Ubicación centralizada:

En [modulos/tarea.py](../../modulos/tarea.py):

```python
ESTADOS_COMPLETADOS: List[str] = ["closed", "complete", "entregada", "hecha", "finalizada"]
```

Si su flujo de trabajo en ClickUp utiliza un estado personalizado (por ejemplo, `aprobada`, `terminada` o `archivada`), agréguelo a `ESTADOS_COMPLETADOS` en minúsculas. El método `tarea.esta_completada()` aplicará esta regla automáticamente en la auditoría del changelog y en el filtrado de la tabla de imagen.

---

## 3. Asignar Colores a Nuevas Etiquetas en la Imagen

Las etiquetas activas se dibujan como píldoras redondeadas en la columna derecha de `Tareas_ClickUp.jpg`.

Para definir colores personalizados para una nueva etiqueta, edite `ESTILOS_ETIQUETAS` en [generador_imagen.py](../../generador_imagen.py):

```python
ESTILOS_ETIQUETAS: Dict[str, Dict[str, str]] = {
    "fisico": {"bg": "#2a3644", "text": "#ffffff"},
    "digital": {"bg": "#dc2626", "text": "#ffffff"},
    "opcional": {"bg": "#064e3b", "text": "#34d399"},
    "urgente": {"bg": "#b91c1c", "text": "#fef2f2"},  # Nueva etiqueta personalizada
}
```

Si una tarea tiene una etiqueta que no está registrada en `ESTILOS_ETIQUETAS`, se utilizará el estilo predeterminado `ESTILO_DEFECTO_TAG` (fondo gris `#3f3f46` y texto blanco).

---

## Documentación Relacionada

- [Cómo agregar nuevas materias o listas](como-agregar-nuevas-materias.md)
- [Cómo ejecutar y agregar pruebas unitarias](como-ejecutar-y-agregar-pruebas.md)
- [Ciclo de vida de snapshots y diferencias](../explanation/ciclo-de-vida-snapshots-y-diferencias.md)
- [Volver al inicio del proyecto](../../README.md)
