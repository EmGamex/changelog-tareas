"""Configuración de compilación para la extensión nativa en C++ (pybind11)."""

import sys
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

extra_args = []
if sys.platform == "win32":
    extra_args = ["/utf-8"]

ext_modules = [
    Pybind11Extension(
        "modulos._changelog_nativo",
        ["src/bindings.cpp"],
        cxx_std=17,
        extra_compile_args=extra_args,
    ),
]

setup(
    name="automatizador_changelog_cpp",
    version="1.0.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
