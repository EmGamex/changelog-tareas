#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "motor_changelog.hpp"

namespace py = pybind11;

namespace {

changelog::TareaCpp extraer_tarea(const std::string& id, const py::handle& obj) {
    changelog::TareaCpp t;
    t.id = id;
    if (py::isinstance<py::dict>(obj)) {
        py::dict d = py::reinterpret_borrow<py::dict>(obj);
        if (d.contains("name")) t.name = py::str(d["name"]);
        if (d.contains("materia")) t.materia = py::str(d["materia"]);
        if (d.contains("status")) t.status = py::str(d["status"]);
        if (d.contains("tags")) t.tags = py::str(d["tags"]);
        if (d.contains("due_date")) t.due_date = py::str(d["due_date"]);
        if (d.contains("content")) t.content = py::str(d["content"]);
        if (d.contains("date_created")) t.date_created = py::str(d["date_created"]);
    } else {
        if (py::hasattr(obj, "name")) t.name = py::str(obj.attr("name"));
        if (py::hasattr(obj, "materia")) t.materia = py::str(obj.attr("materia"));
        if (py::hasattr(obj, "status")) t.status = py::str(obj.attr("status"));
        if (py::hasattr(obj, "tags")) t.tags = py::str(obj.attr("tags"));
        if (py::hasattr(obj, "due_date")) t.due_date = py::str(obj.attr("due_date"));
        if (py::hasattr(obj, "content")) t.content = py::str(obj.attr("content"));
        if (py::hasattr(obj, "date_created")) t.date_created = py::str(obj.attr("date_created"));
    }
    if (t.name.empty()) t.name = "Sin nombre";
    if (t.materia.empty()) t.materia = "Sin materia";
    return t;
}

void convertir_mapa(
    const py::dict& py_mapa,
    std::unordered_map<std::string, changelog::TareaCpp>& out_map,
    std::vector<std::string>& out_order
) {
    out_order.reserve(py_mapa.size());
    out_map.reserve(py_mapa.size());
    for (auto item : py_mapa) {
        std::string id = py::str(item.first);
        out_order.push_back(id);
        out_map.emplace(id, extraer_tarea(id, item.second));
    }
}

std::string generar_changelog_binding(
    const py::dict& tareas_ayer,
    const py::dict& tareas_hoy,
    int year,
    int month,
    int day
) {
    changelog::Date fecha_ref{year, month, day};
    std::unordered_map<std::string, changelog::TareaCpp> mapa_ayer;
    std::vector<std::string> orden_ayer;
    convertir_mapa(tareas_ayer, mapa_ayer, orden_ayer);

    std::unordered_map<std::string, changelog::TareaCpp> mapa_hoy;
    std::vector<std::string> orden_hoy;
    convertir_mapa(tareas_hoy, mapa_hoy, orden_hoy);

    return changelog::generar_texto_changelog_core(mapa_ayer, orden_ayer, mapa_hoy, orden_hoy, fecha_ref);
}

} // namespace

PYBIND11_MODULE(_changelog_nativo, m) {
    m.doc() = "Motor nativo en C++ para comparacion de tareas y generacion de changelog.";
    m.def(
        "generar_texto_changelog_cpp",
        &generar_changelog_binding,
        py::arg("tareas_ayer"),
        py::arg("tareas_hoy"),
        py::arg("year"),
        py::arg("month"),
        py::arg("day"),
        "Genera el texto Markdown del changelog a partir de dos diccionarios y una fecha de referencia."
    );
}
