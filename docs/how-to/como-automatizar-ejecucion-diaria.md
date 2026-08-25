# Guía Práctica: Cómo Automatizar la Ejecución Diaria

Esta guía detalla los pasos para programar la ejecución del script de lunes a viernes en Windows utilizando el Programador de Tareas (Task Scheduler).

---

## Requisitos Previos

- Entorno virtual de Python configurado en el subdirectorio `env/` del proyecto.
- Permisos para programar tareas en Windows.

---

## Paso 1: Crear un Script Batch Portable

Cree un archivo ejecutable nombrado `ejecutar_sincronizacion.bat` en la raíz del proyecto. El uso de `%~dp0` asegura que el script resuelva las rutas relativas al directorio donde reside el archivo, haciéndolo completamente portable e independiente de la ubicación absoluta:

```bat
@echo off
cd /d "%~dp0"
call ".\env\Scripts\python.exe" main.py
```

Pruebe el archivo haciendo doble clic sobre él para verificar que complete la sincronización y copie el resultado al portapapeles.

---

## Paso 2: Configurar el Programador de Tareas de Windows

1. Presione `Win + R`, escriba `taskschd.msc` y presione Enter.
2. En el panel derecho, seleccione **Crear tarea básica...**
3. **Nombre:** `Sincronizador ClickUp Changelog`.
4. **Desencadenador:** Seleccione **Semanalmente**.
   - Marque los días de **Lunes a Viernes**.
   - Configure la hora deseada (por ejemplo, `07:00 AM`).
5. **Acción:** Seleccione **Iniciar un programa**.
   - **Programa o script:** `ejecutar_sincronizacion.bat` (o la ruta al archivo batch dentro de su clon local).
   - **Iniciar en (opcional):** Directorio raíz del proyecto.
6. Finalice el asistente haciendo clic en **Finalizar**.

---

## Consideraciones Importantes

- **Fines de Semana:** El sistema detecta automáticamente si el día actual es sábado o domingo y congela el historial sin sobreescribir los archivos JSON de estado.
- **Portapapeles:** Para que `pyperclip` acceda al portapapeles del usuario, la tarea programada debe configurarse con la opción "Ejecutar solo cuando el usuario haya iniciado sesión".

---

## Documentación Relacionada

- [Ciclo de vida de snapshots y detección de diferencias](../explanation/ciclo-de-vida-snapshots-y-diferencias.md)
- [Referencia de módulos](../reference/arquitectura-y-modulos.md)
- [Volver al inicio del proyecto](../../README.md)
