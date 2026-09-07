#pragma once

#include <string>
#include <vector>
#include <unordered_set>
#include <optional>
#include <sstream>
#include <algorithm>
#include <iomanip>
#include <cctype>

namespace changelog {

struct Date {
    int year{0};
    int month{0};
    int day{0};

    bool operator==(const Date& other) const {
        return year == other.year && month == other.month && day == other.day;
    }
    bool operator!=(const Date& other) const { return !(*this == other); }
    bool operator<(const Date& other) const {
        if (year != other.year) return year < other.year;
        if (month != other.month) return month < other.month;
        return day < other.day;
    }
    bool operator<=(const Date& other) const {
        return (*this < other) || (*this == other);
    }
    bool operator>(const Date& other) const {
        return other < *this;
    }

    bool is_valid() const {
        return year > 0 && month >= 1 && month <= 12 && day >= 1 && day <= 31;
    }
};

inline int days_from_civil(int y, unsigned m, unsigned d) noexcept {
    y -= m <= 2;
    const int era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yoe = static_cast<unsigned>(y - era * 400);
    const unsigned doy = (153 * (m > 2 ? m - 3 : m + 9) + 2) / 5 + d - 1;
    const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + static_cast<int>(doe) - 719468;
}

// Retorna día de la semana en formato Python weekday (0 = Lunes, ..., 6 = Domingo)
inline int weekday_from_date(const Date& d) {
    int days = days_from_civil(d.year, d.month, d.day);
    // 1970-01-01 fue Jueves (weekday = 3)
    int wd = (days + 3) % 7;
    if (wd < 0) wd += 7;
    return wd;
}

inline int diff_in_days(const Date& a, const Date& b) {
    return days_from_civil(a.year, a.month, a.day) - days_from_civil(b.year, b.month, b.day);
}

inline std::string trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return "";
    size_t last = str.find_last_not_of(" \t\r\n");
    return str.substr(first, (last - first + 1));
}

inline std::string to_lower(std::string str) {
    std::transform(str.begin(), str.end(), str.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return str;
}

inline std::optional<Date> parse_date_dmy(const std::string& raw) {
    std::string s = trim(raw);
    if (s.empty()) return std::nullopt;

    // Buscar primer espacio o fin
    size_t space_pos = s.find(' ');
    std::string date_part = (space_pos != std::string::npos) ? s.substr(0, space_pos) : s;

    // Formato DD/MM/YYYY
    std::stringstream ss(date_part);
    std::string d_str, m_str, y_str;
    if (std::getline(ss, d_str, '/') && std::getline(ss, m_str, '/') && std::getline(ss, y_str)) {
        try {
            int d = std::stoi(d_str);
            int m = std::stoi(m_str);
            int y = std::stoi(y_str);
            Date dt{y, m, d};
            if (dt.is_valid()) return dt;
        } catch (...) {
            return std::nullopt;
        }
    }
    return std::nullopt;
}

const std::vector<std::string> ESTADOS_COMPLETADOS = {"closed", "complete", "entregada", "hecha"};
const std::vector<std::string> ETIQUETAS_IGNORADAS = {"personal"};
const std::vector<std::string> DIAS_SEMANA_ESPANOL = {
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
};

struct TareaCpp {
    std::string id;
    std::string name;
    std::string materia;
    std::string status;
    std::string tags;
    std::string due_date;
    std::string content;
    std::string date_created;

    std::unordered_set<std::string> conjunto_etiquetas() const {
        if (tags.empty()) return {};
        std::unordered_set<std::string> result;
        std::stringstream ss(tags);
        std::string item;
        while (std::getline(ss, item, ',')) {
            std::string cleaned = to_lower(trim(item));
            if (!cleaned.empty()) {
                result.insert(cleaned);
            }
        }
        return result;
    }

    bool tiene_etiqueta_ignorada() const {
        if (tags.empty()) return false;
        auto conjunto = conjunto_etiquetas();
        for (const auto& ign : ETIQUETAS_IGNORADAS) {
            if (conjunto.find(ign) != conjunto.end()) {
                return true;
            }
        }
        return false;
    }

    std::optional<Date> due_date_obj() const {
        return parse_date_dmy(due_date);
    }

    bool esta_completada(const Date& hoy_date) const {
        std::string st = to_lower(trim(status));
        for (const auto& ec : ESTADOS_COMPLETADOS) {
            if (st == ec) return true;
        }
        auto due = due_date_obj();
        if (due.has_value() && *due < hoy_date) {
            return true;
        }
        return false;
    }

    bool completada_por_inactividad(const Date& hoy_date) const {
        std::string st = to_lower(trim(status));
        for (const auto& ec : ESTADOS_COMPLETADOS) {
            if (st == ec) return false;
        }
        auto due = due_date_obj();
        return due.has_value() && *due < hoy_date;
    }

    bool es_nueva(const Date& hoy_date) const {
        if (date_created.empty()) return false;
        auto dc = parse_date_dmy(date_created);
        return dc.has_value() && *dc == hoy_date;
    }

    std::string fecha_visual(const Date& hoy_date) const {
        std::string raw = trim(due_date);
        if (raw.empty()) return "No asignada";

        size_t space_pos = raw.find(' ');
        std::string fecha_str = (space_pos != std::string::npos) ? raw.substr(0, space_pos) : raw;
        std::string hora_str = (space_pos != std::string::npos) ? trim(raw.substr(space_pos + 1)) : "00:00";
        if (hora_str.empty()) hora_str = "00:00";

        auto fecha_obj = parse_date_dmy(fecha_str);
        if (!fecha_obj.has_value()) {
            return raw;
        }

        int diff = diff_in_days(*fecha_obj, hoy_date);
        std::string dia_texto;

        if (diff == 0) {
            dia_texto = "Hoy";
        } else if (diff == 1) {
            dia_texto = "Mañana";
        } else if (diff >= 0 && diff <= 7) {
            int wd = weekday_from_date(*fecha_obj);
            dia_texto = DIAS_SEMANA_ESPANOL[wd];
        } else {
            std::ostringstream oss;
            oss << std::setfill('0') << std::setw(2) << fecha_obj->day << "/"
                << std::setfill('0') << std::setw(2) << fecha_obj->month << "/"
                << fecha_obj->year;
            dia_texto = oss.str();
        }

        if (hora_str != "00:00") {
            return dia_texto + " a las " + hora_str;
        }
        return dia_texto;
    }
};

inline std::optional<std::string> _auditar_nombre(const TareaCpp& t_ayer, const TareaCpp& t_hoy) {
    std::string name_ayer = t_ayer.name.empty() ? "Sin nombre" : t_ayer.name;
    std::string name_hoy = t_hoy.name.empty() ? "Sin nombre" : t_hoy.name;
    if (name_ayer != name_hoy) {
        return "se cambió el nombre de '" + name_ayer + "' a '" + name_hoy + "'";
    }
    return std::nullopt;
}

inline std::optional<std::string> _auditar_fecha(const TareaCpp& t_ayer, const TareaCpp& t_hoy, const Date& hoy_date) {
    std::string due_ayer = trim(t_ayer.due_date);
    std::string due_hoy = trim(t_hoy.due_date);

    size_t space_a = due_ayer.find(' ');
    std::string fecha_ayer_corta = (space_a != std::string::npos) ? due_ayer.substr(0, space_a) : due_ayer;

    size_t space_h = due_hoy.find(' ');
    std::string fecha_hoy_corta = (space_h != std::string::npos) ? due_hoy.substr(0, space_h) : due_hoy;

    if (fecha_ayer_corta != fecha_hoy_corta) {
        std::string prev_due = t_ayer.fecha_visual(hoy_date);
        std::string new_due = t_hoy.fecha_visual(hoy_date);
        return "se cambió la fecha del *" + prev_due + "* al *" + new_due + "*";
    }
    return std::nullopt;
}

inline std::optional<std::string> _auditar_etiquetas(const TareaCpp& t_ayer, const TareaCpp& t_hoy) {
    auto tags_ayer_set = t_ayer.conjunto_etiquetas();
    auto tags_hoy_set = t_hoy.conjunto_etiquetas();

    if (tags_ayer_set != tags_hoy_set) {
        std::string tags_ayer_str = t_ayer.tags;
        std::string tags_hoy_str = t_hoy.tags;
        if (tags_ayer_set.empty() && !tags_hoy_set.empty()) {
            return "se le agregaron las etiquetas *[" + tags_hoy_str + "]*";
        } else if (!tags_ayer_set.empty() && tags_hoy_set.empty()) {
            return "se le quitaron las etiquetas";
        } else {
            return "cambió sus etiquetas de *[" + tags_ayer_str + "]* a *[" + tags_hoy_str + "]*";
        }
    }
    return std::nullopt;
}

inline std::vector<std::string> auditar_cambios(const TareaCpp& t_ayer, const TareaCpp& t_hoy, const Date& hoy_date) {
    std::vector<std::string> cambios;
    auto nom = _auditar_nombre(t_ayer, t_hoy);
    if (nom.has_value()) cambios.push_back(*nom);

    auto fec = _auditar_fecha(t_ayer, t_hoy, hoy_date);
    if (fec.has_value()) cambios.push_back(*fec);

    auto eti = _auditar_etiquetas(t_ayer, t_hoy);
    if (eti.has_value()) cambios.push_back(*eti);

    return cambios;
}

} // namespace changelog
