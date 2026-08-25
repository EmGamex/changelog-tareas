# Guía Práctica: Resolución de Problemas Frecuentes

Esta guía ofrece soluciones directas a los errores e incidencias operativas más comunes al ejecutar el sistema de automatización.

---

## 1. Error de Autenticación con ClickUp (`401 Unauthorized` o Datos Vacíos)

### Síntoma:
La consola muestra `Error de red o de API: 401 Unauthorized` o el mensaje `No se encontraron datos en ClickUp para procesar.`

### Causa:
- La variable `CLICKUP_API_TOKEN` no está definida en el archivo `.env`.
- El token de API expiró, contiene espacios accidentales o carece del prefijo correcto (e.g. `pk_...`).

### Solución:
1. Abra o cree el archivo `.env` en la raíz del proyecto.
2. Asegúrese de que el formato sea exacto:
   ```env
   CLICKUP_API_TOKEN=pk_12345678_TU_TOKEN_AQUI
   ```
3. Genere un nuevo token desde ClickUp en caso de duda: **Perfil -> Settings -> Apps -> API Token -> Generate**.

---

## 2. Error al Copiar al Portapapeles (`PyperclipException`)

### Síntoma:
La consola muestra:
```text
No se pudo copiar al portapapeles: Pyperclip could not find a copy/paste mechanism for your system.
```

### Causa:
- En entornos Windows sin sesión de usuario activa (por ejemplo, tareas programadas ejecutadas como servicio de sistema `SYSTEM`), `pyperclip` no puede acceder al portapapeles gráfico.
- En distribuciones Linux, falta la utilidad `xclip` o `xsel`.

### Solución:
- **En Windows Task Scheduler:** Configure la tarea programada con la opción **"Ejecutar solo cuando el usuario haya iniciado sesión"** (Run only when user is logged on).
- **En Linux/WSL:** Instale el gestor de portapapeles:
  ```bash
  sudo apt-get install xclip
  ```
- **Nota:** Si la copia al portapapeles falla, el script no se interrumpe: el texto del changelog se imprimirá igualmente en la consola y se guardará el snapshot.

---

## 3. Advertencia de Fuentes Tipográficas (`IOError: cannot open resource`)

### Síntoma:
Al generar la imagen no se encuentra la fuente `arial.ttf`.

### Causa:
El sistema operativo (común en Linux o Docker) no tiene instalada la fuente TrueType `arial.ttf` en las rutas del sistema.

### Solución:
El módulo [generador_imagen.py](../../generador_imagen.py) cuenta con un mecanismo de respaldo automático:
```python
except IOError:
    default = ImageFont.load_default()
    return default, default, default
```
Si desea utilizar fuentes TrueType en Linux/macOS, instale el paquete de fuentes Microsoft Core:
```bash
sudo apt-get install ttf-mscorefonts-installer
```

---

## 4. Historial o Snapshot Corrupto (`clickup_snapshot_ayer.json`)

### Síntoma:
La consola muestra: `Advertencia: No se pudo leer el historial base (JSONDecodeError).`

### Causa:
El archivo JSON se interrumpió durante una escritura previa o contiene caracteres inválidos.

### Solución:
1. Elimine o limpie los archivos de snapshot en la raíz del proyecto:
   - `clickup_snapshot_ayer.json`
   - `clickup_snapshot_hoy.json`
2. Vuelva a ejecutar el script:
   ```bash
   python main.py
   ```
3. La primera ejecución recreará automáticamente un snapshot limpio de partida.

---

## 5. Tiempos de Espera o Errores de Red (`httpx.TimeoutException`)

### Síntoma:
Peticiones interrumpidas por límite de tiempo al consultar múltiples materias concurrentemente.

### Causa:
Inestabilidad temporal en la conexión de red o degradación del servicio de ClickUp.

### Solución:
El cliente asíncrono tiene un timeout configurado de `10.0` segundos por petición. Si su conexión presenta latencia alta, puede ajustar el timeout en [modulos/api_clickup.py](../../modulos/api_clickup.py):
```python
async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
```

---

## Documentación Relacionada

- [Primeros pasos](../tutorials/primeros-pasos.md)
- [Cómo automatizar la ejecución diaria](como-automatizar-ejecucion-diaria.md)
- [Cómo ejecutar y agregar pruebas unitarias](como-ejecutar-y-agregar-pruebas.md)
- [Volver al inicio del proyecto](../../README.md)
