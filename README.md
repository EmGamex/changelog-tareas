# Automatizador de Tareas y Changelog de ClickUp

Sistema de automatización en Python diseñado para consultar de forma asíncrona las tareas académicas registradas en ClickUp, detectar diferencias respecto al estado del día anterior, generar un reporte en formato Markdown listo para el portapapeles y renderizar una tabla visual en alta resolución en formato JPEG.

---

## Tabla de Contenidos

El sistema de documentación sigue la estructura del marco de trabajo **Diátaxis**:

- **Tutoriales (Aprendizaje paso a paso)**
  - [Primeros pasos e instalación rápida](docs/tutorials/primeros-pasos.md): Guía paso a paso para configurar el entorno y ejecutar la primera sincronización.

- **Guías Prácticas (Resolución de problemas específicos)**
  - [Cómo agregar nuevas materias o listas](docs/how-to/como-agregar-nuevas-materias.md): Pasos para mapear nuevos identificadores de lista y definir estilos visuales.
  - [Cómo personalizar reglas y etiquetas](docs/how-to/como-personalizar-reglas-y-etiquetas.md): Instrucciones para excluir etiquetas, configurar estados de finalización y personalizar estilos.
  - [Cómo automatizar la ejecución diaria](docs/how-to/como-automatizar-ejecucion-diaria.md): Configuración de ejecución programada en Windows con el Programador de Tareas.
  - [Cómo ejecutar y agregar pruebas unitarias](docs/how-to/como-ejecutar-y-agregar-pruebas.md): Guía para correr la suite de pruebas automatizadas y añadir nuevos casos.
  - [Resolución de problemas frecuentes](docs/how-to/resolucion-de-problemas.md): Diagnóstico y soluciones para errores de red, token, portapapeles y fuentes.

- **Referencia Técnica (Información detallada de arquitectura y API)**
  - [Arquitectura y referencia de módulos](docs/reference/arquitectura-y-modulos.md): Detalle técnico de funciones, parámetros, tipos y estructura de datos JSON.

- **Explicación (Conceptos y diseño del sistema)**
  - [Flujo y procesamiento de tareas](docs/explanation/flujo-y-procesamiento-de-tareas.md): Pipeline completo de extracción, normalización, instanciación, auditoría y renderizado visual.
  - [Ciclo de vida de snapshots y detección de diferencias](docs/explanation/ciclo-de-vida-snapshots-y-diferencias.md): Explicación del mecanismo de persistencia, rotación de estado, lógica de fines de semana y reglas de negocio.

---

## Requisitos Previos

- Python 3.10 o superior.
- Token de API personal de ClickUp.
- Dependencias de Python especificadas en `requirements.txt` (`httpx`, `pillow`, `pyperclip`, `python-dotenv`).

---

## Inicio Rápido

1. Clonar o abrir el directorio del proyecto en el entorno local.
2. Instalar las dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
3. Crear un archivo `.env` en la raíz del proyecto (puedes basarte en `.env.example`):
   ```env
   CLICKUP_API_TOKEN=tu_token_de_clickup_aqui
   AUTOR_NOMBRE=Juan
   ```
   > **Notas de configuración:**
   > - `AUTOR_NOMBRE`: Opcional. Si no se define, se usará un formato genérico seguro.
   > - `CLICKUP_LISTAS_MATERIAS`: Opcional. En la primera ejecución, el sistema **autodescubrirá automáticamente** todas las listas de tu cuenta de ClickUp y las guardará en `.env` para optimizar ejecuciones futuras.
4. Ejecutar el script principal:
   ```bash
   python main.py
   ```
5. El changelog generado se copiará automáticamente al portapapeles del sistema y la tabla gráfica se guardará en `Tareas_ClickUp.jpg`.

---

## Pruebas Unitarias

Para ejecutar la suite de pruebas unitarias automatizadas con descubrimiento automático:

```bash
python -m unittest discover -s tests
```

Para instrucciones detalladas sobre la instalación paso a paso, consulte el [Tutorial de Primeros Pasos](docs/tutorials/primeros-pasos.md).
