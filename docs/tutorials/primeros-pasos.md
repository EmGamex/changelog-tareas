# Tutorial: Primeros Pasos e Instalación Rápida

Este tutorial guía a un usuario desde la preparación del entorno hasta la primera ejecución exitosa de la sincronización de tareas.

---

## Objetivo

Al completar este tutorial, dispondrá de:
1. El entorno virtual de Python configurado con todas las dependencias.
2. La clave de autenticación de ClickUp configurada en el archivo `.env`.
3. Una ejecución exitosa que genere el changelog en el portapapeles y la imagen visual de tareas.

---

## Requisitos Previos

- Python 3.10 o superior instalado en el sistema.
- Acceso a una cuenta de ClickUp con un Token de API generado.
  - Para obtener su token en ClickUp: Perfil -> Apps -> API Token -> Generate.

---

## Paso 1: Configurar el Entorno Virtual

Abra una terminal en la raíz del proyecto y active el entorno virtual o cree uno nuevo:

```bash
python -m venv env
```

Activación en Windows (PowerShell):
```powershell
.\env\Scripts\Activate.ps1
```

Activación en Windows (CMD):
```cmd
.\env\Scripts\activate.bat
```

Instale las dependencias requeridas desde `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## Paso 2: Configurar las Variables de Entorno

En la raíz del proyecto, cree un archivo nombrado `.env` (puede guiarse en `.env.example`) y configure sus variables:

```env
CLICKUP_API_TOKEN=pk_12345678_EJEMPLO_DE_TOKEN
AUTOR_NOMBRE=Juan
```

> **Nota:** `AUTOR_NOMBRE` es opcional. Si no se especifica, el sistema generará el pie de página con un mensaje seguro por defecto sin fallar.

---

## Paso 3: Realizar la Primera Ejecución

Con el entorno virtual activo, ejecute el punto de entrada principal:

```bash
python main.py
```

### Salida esperada en consola:

```text
Obteniendo tareas de ClickUp...
Generando imagen y changelog...
[IMAGEN] ¡Tabla HD en JPEG generada con éxito en 'Tareas_ClickUp.jpg'!

¡Copiado al portapapeles con éxito!

========================================
Output listo:
========================================

`Changelog - Lunes (22/08/2026)`
> Nuevas tareas añadidas
• *Tarea de Ejemplo* (Matemáticas) se agregó a la lista y fecha límite para el *Hoy a las 18:00*.

`Mensaje automatizado por [Nombre] en 1.85 segundos`
```

---

## Paso 4: Validar los Resultados

1. **Portapapeles:** Pegue el contenido (`Ctrl + V`) en cualquier editor o aplicación de mensajería para confirmar el texto Markdown formateado.
2. **Imagen Generada:** Verifique que en la raíz del proyecto exista el archivo `Tareas_ClickUp.jpg` con la tabla renderizada en alta resolución.
3. **Persistencia Inicial:** Compruebe que se haya creado el archivo `clickup_snapshot_hoy.json` con los datos capturados.

---

## Siguientes Pasos

- Para añadir o modificar las materias configuradas, consulte [Cómo agregar nuevas materias o listas](../how-to/como-agregar-nuevas-materias.md).
- Para automatizar la ejecución de lunes a viernes, consulte [Cómo automatizar la ejecución diaria](../how-to/como-automatizar-ejecucion-diaria.md).
- Para comprender cómo se comparan los estados día tras día, lea [Ciclo de vida de snapshots y detección de diferencias](../explanation/ciclo-de-vida-snapshots-y-diferencias.md).
