"""Script de benchmark para comparar el rendimiento entre el motor Python y el motor C++ nativo.

Genera 1.200 tareas sintéticas con una distribución realista de estados,
etiquetas, cambios de nombre, modificaciones de fecha y tareas archivadas.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

from modulos.changelog import (
    generar_texto_changelog_python,
    generar_texto_changelog_nativo,
    MOTOR_NATIVO_DISPONIBLE,
)
from modulos.tarea import Tarea


def generar_dataset_1200_tareas(
    hoy: datetime
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Genera un snapshot sintético de ayer y hoy con 1.200 tareas con casos mixtos.

    Args:
        hoy: Fecha de referencia para el cálculo de estados y fechas relativas.

    Returns:
        Tupla con diccionarios (tareas_ayer, tareas_hoy).
    """
    random.seed(42)
    materias = ["Cálculo III", "Física II", "Estructuras de Datos", "Circuitos", "Filosofía", "Inglés V"]
    tags_pool = ["", "urgente", "digital", "examen", "laboratorio", "personal", "proyecto"]
    statuses = ["to do", "in progress", "complete", "closed", "hecha", "entregada"]

    tareas_ayer: Dict[str, Dict[str, Any]] = {}
    tareas_hoy: Dict[str, Dict[str, Any]] = {}

    for i in range(1, 1201):
        task_id = str(i)
        materia = random.choice(materias)
        tag = random.choice(tags_pool)
        status = "to do" if random.random() > 0.3 else random.choice(statuses)

        # Fecha de vencimiento entre 5 días atrás y 15 días adelante
        dias_offset = random.randint(-5, 15)
        due_dt = hoy + timedelta(days=dias_offset, hours=random.randint(8, 20), minutes=0)
        due_str = due_dt.strftime("%d/%m/%Y %H:%M")

        created_dt = hoy - timedelta(days=random.randint(0, 10))
        created_str = created_dt.strftime("%d/%m/%Y %H:%M")

        t_data = {
            "name": f"Tarea de estudio #{i}",
            "materia": materia,
            "status": status,
            "tags": tag,
            "due_date": due_str,
            "content": f"Descripción de la tarea académica número {i}",
            "date_created": created_str,
        }

        # Distribución de cambios para el snapshot de hoy:
        # 1. Tareas archivadas (5%): estaban ayer pero hoy ya no
        if i <= 60:
            tareas_ayer[task_id] = t_data
            continue

        # 2. Tareas nuevas creadas hoy (10%): no estaban ayer, creadas hoy
        if 61 <= i <= 180:
            t_nueva = dict(t_data)
            t_nueva["date_created"] = hoy.strftime("%d/%m/%Y 09:00")
            tareas_hoy[task_id] = t_nueva
            continue

        # 3. Tareas modificadas (20%): cambio de nombre, fecha o estado
        if 181 <= i <= 420:
            tareas_ayer[task_id] = dict(t_data)
            t_mod = dict(t_data)
            tipo_cambio = i % 4
            if tipo_cambio == 0:
                t_mod["name"] = f"Tarea de estudio #{i} (ACTUALIZADA)"
            elif tipo_cambio == 1:
                t_mod["due_date"] = (due_dt + timedelta(days=2)).strftime("%d/%m/%Y %H:%M")
            elif tipo_cambio == 2:
                t_mod["tags"] = "urgente, digital" if not tag else ""
            else:
                t_mod["status"] = "complete"
            tareas_hoy[task_id] = t_mod
            continue

        # 4. Tareas sin cambios (65%)
        tareas_ayer[task_id] = dict(t_data)
        tareas_hoy[task_id] = dict(t_data)

    return tareas_ayer, tareas_hoy


def ejecutar_benchmark(iteraciones: int = 100) -> None:
    """Ejecuta la medición comparativa de rendimiento entre Python y C++."""
    print("================================================================")
    print(f"BENCHMARK: Motor de Changelog (Python vs C++ Nativo)")
    print(f"Dataset: 1.200 tareas sintéticas | Iteraciones: {iteraciones}")
    print("================================================================\n")

    if not MOTOR_NATIVO_DISPONIBLE:
        print("[ERROR] El módulo nativo C++ no está disponible.")
        return

    hoy = datetime(2026, 8, 22, 10, 0)
    ayer_dict, hoy_dict = generar_dataset_1200_tareas(hoy)

    print(f"• Tareas en snapshot de ayer: {len(ayer_dict)}")
    print(f"• Tareas en snapshot de hoy:  {len(hoy_dict)}\n")

    # 1. Verificación de paridad
    print("1. Verificando paridad exacta de salida...")
    out_py = generar_texto_changelog_python(ayer_dict, hoy_dict, fecha_referencia=hoy)
    out_cpp = generar_texto_changelog_nativo(ayer_dict, hoy_dict, fecha_referencia=hoy)

    if out_py == out_cpp:
        print("   [OK] La salida Markdown es 100% IDÉNTICA entre Python y C++.\n")
    else:
        print("   [ADVERTENCIA] Hay discrepancias en la salida. Revisar implementación.\n")

    # 2. Benchmark Python
    print(f"2. Ejecutando motor Python puro ({iteraciones} iteraciones)...")
    inicio_py = time.perf_counter()
    for _ in range(iteraciones):
        _ = generar_texto_changelog_python(ayer_dict, hoy_dict, fecha_referencia=hoy)
    tiempo_py_total = time.perf_counter() - inicio_py
    tiempo_py_promedio = (tiempo_py_total / iteraciones) * 1000  # en milisegundos

    # 3. Benchmark C++
    print(f"3. Ejecutando motor C++ nativo ({iteraciones} iteraciones)...")
    inicio_cpp = time.perf_counter()
    for _ in range(iteraciones):
        _ = generar_texto_changelog_nativo(ayer_dict, hoy_dict, fecha_referencia=hoy)
    tiempo_cpp_total = time.perf_counter() - inicio_cpp
    tiempo_cpp_promedio = (tiempo_cpp_total / iteraciones) * 1000  # en milisegundos

    speedup = tiempo_py_promedio / tiempo_cpp_promedio if tiempo_cpp_promedio > 0 else 0

    print("\n================================================================")
    print("RESULTADOS DEL BENCHMARK:")
    print("================================================================")
    print(f"• Python Puro:  {tiempo_py_promedio:6.3f} ms por ejecución ({tiempo_py_total:6.3f} s total)")
    print(f"• C++ Nativo:   {tiempo_cpp_promedio:6.3f} ms por ejecución ({tiempo_cpp_total:6.3f} s total)")
    print(f"• Aceleración:  {speedup:6.1f}x más rápido con C++ nativo")
    print(f"• Tareas/seg:   Python = {1200 / (tiempo_py_promedio / 1000):,.0f} tareas/s | C++ = {1200 / (tiempo_cpp_promedio / 1000):,.0f} tareas/s")
    print("================================================================\n")


if __name__ == "__main__":
    ejecutar_benchmark(iteraciones=100)
