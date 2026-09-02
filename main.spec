# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de compilación de PyInstaller para el Automatizador de Tareas Changelog.

Optimizado para generar un ejecutable liviano (.exe) en un solo archivo (onefile),
excluyendo módulos pesados e innecesarios (como Tkinter, unittest, sqlite3, etc.)
e incluyendo todos los paquetes requeridos por el proyecto.
"""

block_cipher = None

# Recolección explícita de dependencias clave
hiddenimports = [
    # Módulos del proyecto
    "modulos",
    "modulos.api_clickup",
    "modulos.changelog",
    "modulos.configuracion",
    "modulos.memoria",
    "modulos.tarea",
    "generador_imagen",
    # Dependencias de terceros
    "httpx",
    "httpcore",
    "h11",
    "anyio",
    "anyio._backends._asyncio",
    "sniffio",
    "pyperclip",
    "dotenv",
    # Pillow (módulos esenciales y plugins de imagen)
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "PIL.JpegImagePlugin",
    "PIL.PngImagePlugin",
    "certifi",
]

# Exclusiones para reducir al máximo el peso del ejecutable
excludes = [
    "tkinter",
    "_tkinter",
    "tcl",
    "tk",
    "unittest",
    "pytest",
    "pydoc",
    "doctest",
    "sqlite3",
    "_sqlite3",
    "turtle",
    "curses",
    "xmlrpc",
    "multiprocessing",
    "lib2to3",
    "distutils",
    "setuptools",
    "pip",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
]

datas = []

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="changelog-tareas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
