#pragma once

#include "tarea.hpp"
#include <unordered_map>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>

namespace changelog {

inline std::vector<std::string> buscar_tareas_archivadas(
    const std::unordered_map<std::string, TareaCpp>& tareas_ayer,
    const std::vector<std::string>& orden_ayer,
    const std::unordered_map<std::string, TareaCpp>& tareas_hoy
) {
    std::vector<std::string> completadas;
    for (const auto& task_id : orden_ayer) {
        auto it_ayer = tareas_ayer.find(task_id);
        if (it_ayer == tareas_ayer.end()) continue;
        const auto& t_ayer = it_ayer->second;

        if (t_ayer.tiene_etiqueta_ignorada()) {
            continue;
        }
        if (tareas_hoy.find(task_id) == tareas_hoy.end()) {
            std::string st = to_lower(trim(t_ayer.status));
            bool is_completed = false;
            for (const auto& ec : ESTADOS_COMPLETADOS) {
                if (st == ec) {
                    is_completed = true;
                    break;
                }
            }
            if (!is_completed) {
                completadas.push_back("• *" + t_ayer.name + "* (" + t_ayer.materia + ") se completó (archivada/cerrada).");
            }
        }
    }
    return completadas;
}

inline std::string construir_texto_final(
    const std::string& dia_semana,
    const std::string& fecha_encabezado,
    const std::vector<std::string>& completadas,
    const std::vector<std::string>& nuevas,
    const std::vector<std::string>& actualizaciones
) {
    std::vector<std::string> output;
    output.push_back("`Changelog - " + dia_semana + " (" + fecha_encabezado + ")`");
    bool hubo_cambios = false;

    struct Seccion {
        std::string titulo;
        const std::vector<std::string>& items;
    };

    std::vector<Seccion> secciones = {
        {"> Tareas completadas", completadas},
        {"> Nuevas tareas añadidas", nuevas},
        {"> Actualizaciones y correcciones", actualizaciones}
    };

    for (const auto& sec : secciones) {
        if (!sec.items.empty()) {
            output.push_back("\n" + sec.titulo);
            for (const auto& item : sec.items) {
                output.push_back(item);
            }
            hubo_cambios = true;
        }
    }

    if (!hubo_cambios) {
        output.push_back("\n• Sin novedades ni cambios en las tareas respecto al día anterior. Que milagro.");
    }

    std::ostringstream result;
    for (size_t i = 0; i < output.size(); ++i) {
        if (i > 0) {
            result << "\n";
        }
        result << output[i];
    }
    return result.str();
}

inline std::string generar_texto_changelog_core(
    const std::unordered_map<std::string, TareaCpp>& tareas_ayer,
    const std::vector<std::string>& orden_ayer,
    const std::unordered_map<std::string, TareaCpp>& tareas_hoy,
    const std::vector<std::string>& orden_hoy,
    const Date& hoy_date
) {
    int wd = weekday_from_date(hoy_date);
    std::string dia_semana = DIAS_SEMANA_ESPANOL[wd];

    std::ostringstream oss_fecha;
    oss_fecha << std::setfill('0') << std::setw(2) << hoy_date.day << "/"
              << std::setfill('0') << std::setw(2) << hoy_date.month << "/"
              << hoy_date.year;
    std::string fecha_encabezado = oss_fecha.str();

    std::vector<std::string> completadas = buscar_tareas_archivadas(tareas_ayer, orden_ayer, tareas_hoy);
    std::vector<std::string> nuevas;
    std::vector<std::string> actualizaciones;

    for (const auto& task_id : orden_hoy) {
        auto it_hoy = tareas_hoy.find(task_id);
        if (it_hoy == tareas_hoy.end()) continue;
        const auto& t_hoy = it_hoy->second;

        if (t_hoy.tiene_etiqueta_ignorada()) {
            continue;
        }

        const TareaCpp* t_ayer_ptr = nullptr;
        auto it_ayer = tareas_ayer.find(task_id);
        if (it_ayer != tareas_ayer.end()) {
            t_ayer_ptr = &it_ayer->second;
        }

        bool auto_completed = t_hoy.completada_por_inactividad(hoy_date);
        std::string st_hoy = to_lower(trim(t_hoy.status));
        bool status_in_completed = false;
        for (const auto& ec : ESTADOS_COMPLETADOS) {
            if (st_hoy == ec) {
                status_in_completed = true;
                break;
            }
        }
        bool esta_cerrada = status_in_completed || auto_completed;
        bool es_nueva = t_hoy.es_nueva(hoy_date);

        if (esta_cerrada) {
            if (auto_completed) {
                completadas.push_back("• *" + t_hoy.name + "* (" + t_hoy.materia + ") se completó por inactividad.");
            } else if (es_nueva) {
                nuevas.push_back("• *" + t_hoy.name + "* (" + t_hoy.materia + ") se creó y completó el día de hoy.");
            } else {
                bool ayer_estaba_cerrada = false;
                if (t_ayer_ptr) {
                    std::string st_ayer = to_lower(trim(t_ayer_ptr->status));
                    for (const auto& ec : ESTADOS_COMPLETADOS) {
                        if (st_ayer == ec) {
                            ayer_estaba_cerrada = true;
                            break;
                        }
                    }
                }
                if (!t_ayer_ptr || !ayer_estaba_cerrada) {
                    completadas.push_back("• *" + t_hoy.name + "* (" + t_hoy.materia + ") se completó de la lista.");
                }
            }
            continue;
        }

        if (es_nueva) {
            std::string tag_part = t_hoy.tags.empty() ? "" : " con etiqueta *" + t_hoy.tags + "*";
            std::string fecha_visual = t_hoy.fecha_visual(hoy_date);
            std::string fecha_part = t_hoy.due_date.empty() ? " (sin fecha límite)" : " y fecha límite para el *" + fecha_visual + "*";
            nuevas.push_back("• *" + t_hoy.name + "* (" + t_hoy.materia + ") se agregó a la lista" + tag_part + fecha_part + ".");
            continue;
        }

        if (t_ayer_ptr) {
            auto cambios = auditar_cambios(*t_ayer_ptr, t_hoy, hoy_date);
            if (!cambios.empty()) {
                std::ostringstream oss_det;
                for (size_t i = 0; i < cambios.size(); ++i) {
                    if (i > 0) oss_det << ", ";
                    oss_det << cambios[i];
                }
                actualizaciones.push_back("• *" + t_hoy.name + "* (" + t_hoy.materia + "): " + oss_det.str() + ".");
            }
        }
    }

    return construir_texto_final(dia_semana, fecha_encabezado, completadas, nuevas, actualizaciones);
}

} // namespace changelog
