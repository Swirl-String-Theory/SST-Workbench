#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <string>
#include <map>
#include <vector>
#include <stdexcept>
#include <algorithm>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;

static double get_param(const std::map<std::string, double>& params, const std::string& name, double fallback) {
    auto it = params.find(name);
    if (it == params.end()) return fallback;
    return it->second;
}

static std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

static double raw_profile(const std::string& profile_in, double x, const std::map<std::string, double>& params) {
    std::string p = lower_copy(profile_in);
    x = std::max(0.0, std::min(1.0, x));

    if (p == "uniform" || p == "constant" || p == "shell") return 1.0;
    if (p == "solid" || p == "solid_body" || p == "solid-body" || p == "rankine_inside") return x;
    if (p == "quadratic" || p == "quadratic_core" || p == "parabolic_edge") return x * (2.0 - x);

    if (p == "irrotational" || p == "irrotational_reg" || p == "vortex_1_over_r") {
        double eps = std::max(get_param(params, "eps", 0.05), 1e-9);
        return 1.0 / std::max(x, eps);
    }

    if (p == "rankine" || p == "rankine_vortex") {
        double core = std::min(std::max(get_param(params, "core", 0.35), 1e-9), 1.0);
        if (x <= core) return x / core;
        return core / std::max(x, 1e-12);
    }

    if (p == "lamb_oseen" || p == "oseen") {
        double sigma = std::max(get_param(params, "sigma", 0.35), 1e-9);
        if (x < 1e-9) return 0.0;
        return (1.0 - std::exp(-std::pow(x / sigma, 2.0))) / x;
    }

    if (p == "gaussian_core" || p == "gaussian") {
        double sigma = std::max(get_param(params, "sigma", 0.35), 1e-9);
        return std::exp(-0.5 * std::pow(x / sigma, 2.0));
    }

    if (p == "gaussian_shell" || p == "shell_gaussian") {
        double r0 = std::min(std::max(get_param(params, "r0", 0.75), 0.0), 1.0);
        double sigma = std::max(get_param(params, "sigma", 0.12), 1e-9);
        return std::exp(-0.5 * std::pow((x - r0) / sigma, 2.0));
    }

    throw std::runtime_error("unknown profile: " + profile_in);
}

static py::dict integrate_profile_raw(const std::string& profile,
                                      const std::map<std::string, double>& params,
                                      int n_radial) {
    int n = std::max(64, n_radial);
    double dx = 1.0 / static_cast<double>(n);
    double j = 0.0;
    double k_raw = 0.0;
    double max_abs = 0.0;
    for (int i = 0; i < n; ++i) {
        double x = (static_cast<double>(i) + 0.5) * dx;
        double f = raw_profile(profile, x, params);
        double weight = x * x * x;
        j += weight * dx;
        k_raw += f * f * weight * dx;
        max_abs = std::max(max_abs, std::abs(f));
    }
    double f_boundary = raw_profile(profile, 1.0, params);
    py::dict d;
    d["j_dimless_radial"] = j;
    d["k_dimless_raw_radial"] = k_raw;
    d["raw_rms_r2"] = std::sqrt(k_raw / j);
    d["raw_boundary"] = f_boundary;
    d["raw_max_abs"] = max_abs;
    return d;
}

static double normalization_scale(const std::string& profile,
                                  const std::string& normalization_in,
                                  const std::map<std::string, double>& params,
                                  int n_radial) {
    std::string normalization = lower_copy(normalization_in);
    py::dict info = integrate_profile_raw(profile, params, n_radial);
    double denom = 1.0;
    if (normalization == "boundary" || normalization == "edge") {
        denom = info["raw_boundary"].cast<double>();
    } else if (normalization == "max" || normalization == "peak") {
        denom = info["raw_max_abs"].cast<double>();
    } else if (normalization == "rms_r2" || normalization == "r2_rms" || normalization == "weighted_rms") {
        // Calibration mode: this forces c/v_ref=1 and is therefore not a physics test.
        denom = info["raw_rms_r2"].cast<double>();
    } else if (normalization == "none" || normalization == "raw") {
        denom = 1.0;
    } else {
        throw std::runtime_error("unknown normalization: " + normalization_in);
    }
    if (std::abs(denom) < 1e-300) {
        throw std::runtime_error("normalization denominator too small for " + profile + "/" + normalization_in);
    }
    return 1.0 / denom;
}

static py::dict profile_metrics(const std::string& profile,
                                double a_core,
                                double rho_f,
                                double v_ref,
                                const std::string& normalization,
                                const std::map<std::string, double>& params,
                                int n_radial) {
    if (a_core <= 0.0 || rho_f <= 0.0 || v_ref <= 0.0) {
        throw std::runtime_error("a_core, rho_f and v_ref must be positive");
    }

    py::dict raw = integrate_profile_raw(profile, params, n_radial);
    double scale = normalization_scale(profile, normalization, params, n_radial);
    double j_radial = raw["j_dimless_radial"].cast<double>();
    double k_radial = raw["k_dimless_raw_radial"].cast<double>();

    double a4 = std::pow(a_core, 4.0);
    double J = 2.0 * PI * a4 * j_radial;
    double Kgeom = 2.0 * PI * a4 * scale * scale * k_radial;
    double I = rho_f * J;
    double K = rho_f * v_ref * v_ref * Kgeom;
    double c = std::sqrt(K / I);
    double J_analytic = 0.5 * PI * a4;

    py::dict d;
    d["profile"] = profile;
    d["normalization"] = normalization;
    d["a_core"] = a_core;
    d["rho_f"] = rho_f;
    d["v_ref"] = v_ref;
    d["I_chi"] = I;
    d["K_chi"] = K;
    d["J_numeric"] = J;
    d["J_analytic_disk"] = J_analytic;
    d["J_rel_error"] = J / J_analytic - 1.0;
    d["Kgeom_over_J"] = Kgeom / J;
    d["c_chi"] = c;
    d["c_over_v_ref"] = c / v_ref;
    d["scale"] = scale;
    d["raw_boundary"] = raw["raw_boundary"].cast<double>();
    d["raw_max_abs"] = raw["raw_max_abs"].cast<double>();
    d["raw_rms_r2"] = raw["raw_rms_r2"].cast<double>();
    d["n_radial"] = n_radial;
    return d;
}

static py::list horn_loop_frequency_ratios(double c_over_v, int n_max, int n_grid) {
    py::list rows;
    for (int n = 1; n <= n_max; ++n) {
        double x = PI * static_cast<double>(n) / static_cast<double>(n_grid);
        double fd = std::sin(x) / x;
        py::dict d;
        d["n"] = n;
        d["continuous_ratio"] = c_over_v;
        d["fd_ratio"] = c_over_v * fd;
        d["fd_relative_error_vs_cont"] = fd - 1.0;
        rows.append(d);
    }
    return rows;
}

static py::list spectrum_convergence(double c_over_v, int n_max, const std::vector<int>& grids) {
    py::list rows;
    for (int N : grids) {
        double max_err = 0.0;
        for (int n = 1; n <= n_max; ++n) {
            double x = PI * static_cast<double>(n) / static_cast<double>(N);
            double fd = std::sin(x) / x;
            max_err = std::max(max_err, std::abs(fd - 1.0));
        }
        double x_max = PI * static_cast<double>(n_max) / static_cast<double>(N);
        double pred = std::abs(std::sin(x_max) / x_max - 1.0);
        py::dict d;
        d["N"] = N;
        d["max_rel_error"] = max_err;
        d["prediction"] = pred;
        d["c_over_v"] = c_over_v;
        rows.append(d);
    }
    return rows;
}

PYBIND11_MODULE(sst_chi_phase_v3, m) {
    m.doc() = "SST chi-phase v3: non-tautological profile-derived torsional stiffness extractor";
    m.def("raw_profile", &raw_profile, py::arg("profile"), py::arg("x"), py::arg("params") = std::map<std::string,double>{});
    m.def("integrate_profile_raw", &integrate_profile_raw, py::arg("profile"), py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("normalization_scale", &normalization_scale, py::arg("profile"), py::arg("normalization"), py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("profile_metrics", &profile_metrics,
          py::arg("profile"), py::arg("a_core"), py::arg("rho_f"), py::arg("v_ref"),
          py::arg("normalization") = "boundary", py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("horn_loop_frequency_ratios", &horn_loop_frequency_ratios, py::arg("c_over_v"), py::arg("n_max") = 16, py::arg("n_grid") = 4096);
    m.def("spectrum_convergence", &spectrum_convergence, py::arg("c_over_v") = 1.0, py::arg("n_max") = 32, py::arg("grids") = std::vector<int>{128,256,512,1024,2048,4096,8192});
}
