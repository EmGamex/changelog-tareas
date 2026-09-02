# Guía Práctica: Cómo Ejecutar y Agregar Pruebas Unitarias

Esta guía explica cómo ejecutar la suite de pruebas unitarias automatizadas del proyecto y cómo agregar nuevas pruebas para validar reglas de negocio, formateo y transformaciones de datos.

---

## 1. Ejecución de la Suite de Pruebas

El proyecto utiliza el módulo nativo [unittest](https://docs.python.org/3/library/unittest.html) de Python, por lo que no requiere librerías de prueba externas.

### Comando de descubrimiento automático:

Abra una terminal en la raíz del proyecto con el entorno virtual activo:

```bash
python -m unittest discover -s tests
```

### Ejecutar un archivo de pruebas específico:

```bash
python -m unittest tests/test_tarea.py
```

### Ejecutar una prueba individual con detalle (`verbose`):

```bash
python -m unittest -v tests.test_tarea.TestModuloTarea.test_formateo_fechas_relativas
```

---

## 2. Estructura de la Suite de Pruebas

El archivo de pruebas principal se ubica en [tests/test_tarea.py](../../tests/test_tarea.py) y agrupa las pruebas en la clase `TestModuloTarea`:

| Método de Prueba | Qué Valida |
| :--- | :--- |
| `test_etiquetas_ignoradas` | Tareas con etiqueta `personal` se ignoran correctamente. |
| `test_estados_completados_canonicos` | Normalización de estados `closed`, `complete`, `entregada`, `hecha`. |
| `test_autocompletado_por_inactividad_fecha_vencida` | Detección de tareas vencidas (`due_date < hoy`) como completadas. |
| `test_formateo_fechas_relativas` | Formateo en español (`Hoy a las HH:MM`, `Mañana`, día de la semana). |
| `test_serializacion_y_deserializacion_diccionario` | Conversión bidireccional entre `Tarea` y diccionarios JSON. |
| `test_auditoria_de_cambios` | Detección de modificaciones en título, fecha límite y etiquetas. |
| `test_generador_changelog_integracion` | Ensamblado del markdown final del changelog con secciones `>`. |
| `test_generador_changelog_sin_cambios` | Mensaje estándar de cierre cuando no existen cambios respecto a ayer. |
| `test_generador_changelog_autocompletado_inactividad_sin_mutacion` | Autocompletado de tareas vencidas sin mutar el objeto en memoria. |
| `test_preparar_datos_imagen` | Filtrado de tareas cerradas/ignoradas y orden cronológico para JPEG. |

---

## 3. Cómo Agregar Nuevos Casos de Prueba

Para agregar una prueba que verifique una nueva regla o comportamiento, siga el patrón `unittest`:

### Ejemplo: Probar una nueva regla de fecha o etiqueta

Abra [tests/test_tarea.py](../../tests/test_tarea.py) y añada un nuevo método dentro de la clase `TestModuloTarea`:

```python
def test_nueva_regla_personalizada(self):
    """Verifica que las tareas sin fecha límite muestren 'No asignada'."""
    tarea = Tarea(
        id="99",
        name="Lectura voluntaria",
        materia="Filosofía",
        due_date="",
    )
    self.assertEqual(tarea.fecha_visual(), "No asignada")
    self.assertFalse(tarea.esta_completada())
```

### Buenas Prácticas al Escribir Pruebas:
1. **Sin dependencias de red:** Las pruebas unitarias no deben invocar la API de ClickUp real ni depender de variables de entorno como `CLICKUP_API_TOKEN`.
2. **Fechas deterministas:** Al probar cálculos de fechas relativas o vencimientos, proporcione explícitamente el parámetro `hoy_date` (por ejemplo, `hoy_date=date(2026, 8, 22)`) o `fecha_referencia` en `generar_texto_changelog`.
3. **Docstrings claros:** Cada método de prueba debe incluir un docstring explicativo en español.

---

## Documentación Relacionada

- [Referencia técnica de arquitectura y módulos](../reference/arquitectura-y-modulos.md)
- [Cómo personalizar reglas y etiquetas](como-personalizar-reglas-y-etiquetas.md)
- [Resolución de problemas frecuentes](resolucion-de-problemas.md)
- [Volver al inicio del proyecto](../../README.md)
