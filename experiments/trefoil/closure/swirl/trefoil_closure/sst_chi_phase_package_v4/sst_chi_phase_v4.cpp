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

static std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

static double get_param(const std::map<std::string, double>& params, const std::string& name, double fallback) {
    auto it = params.find(name);
    return (it == params.end()) ? fallback : it->second;
}

static double raw_profile(const std::string& profile_in, double x, const std::map<std::string, double>& params = {}) {
    std::string p = lower_copy(profile_in);
    x = std::max(0.0, std::min(1.0, x));

    if (p == "uniform" || p == "uniform_boundary" || p == "constant_shell") return 1.0;
    if (p == "solid_body" || p == "solid-body" || p == "solid") return x;
    if (p == "irrotational_reg" || p == "regularized_1_over_r" || p == "vortex_1_over_r") {
        double eps = std::max(get_param(params, "eps", 0.05), 1e-12);
        return 1.0 / std::sqrt(x*x + eps*eps);
    }
    if (p == "gaussian_core" || p == "gaussian") {
        double sigma = std::max(get_param(params, "sigma", 0.35), 1e-12);
        return std::exp(-0.5 * (x/sigma) * (x/sigma));
    }
    if (p == "rankine_matched" || p == "rankine") {
        double core = std::min(std::max(get_param(params, "core", 0.35), 1e-12), 1.0);
        if (x <= core) return x / core;
        return core / std::max(x, 1e-12);
    }
    throw std::runtime_error("unknown profile: " + profile_in);
}

static double profile_derivative(const std::string& profile_in, double x, const std::map<std::string, double>& params = {}) {
    std::string p = lower_copy(profile_in);
    x = std::max(0.0, std::min(1.0, x));

    if (p == "uniform" || p == "uniform_boundary" || p == "constant_shell") return 0.0;
    if (p == "solid_body" || p == "solid-body" || p == "solid") return 1.0;
    if (p == "irrotational_reg" || p == "regularized_1_over_r" || p == "vortex_1_over_r") {
        double eps = std::max(get_param(params, "eps", 0.05), 1e-12);
        return -x / std::pow(x*x + eps*eps, 1.5);
    }
    if (p == "gaussian_core" || p == "gaussian") {
        double sigma = std::max(get_param(params, "sigma", 0.35), 1e-12);
        return raw_profile(profile_in, x, params) * (-(x / (sigma*sigma)));
    }
    if (p == "rankine_matched" || p == "rankine") {
        double core = std::min(std::max(get_param(params, "core", 0.35), 1e-12), 1.0);
        if (x < core) return 1.0 / core;
        return -core / std::max(x*x, 1e-24);
    }
    throw std::runtime_error("unknown profile: " + profile_in);
}

static py::dict raw_info(const std::string& profile, const std::map<std::string, double>& params = {}, int n_radial = 200000) {
    int n = std::max(128, n_radial);
    double dx = 1.0 / static_cast<double>(n);
    double J = 0.0, K = 0.0, E = 0.0, max_abs = 0.0;
    for (int i = 0; i < n; ++i) {
        double x = (static_cast<double>(i) + 0.5) * dx;
        double f = raw_profile(profile, x, params);
        double f2 = f*f;
        J += x*x*x * dx;
        K += f2 * x*x*x * dx;
        E += f2 * x * dx;
        max_abs = std::max(max_abs, std::abs(f));
    }
    double boundary = raw_profile(profile, 1.0, params);
    double center = raw_profile(profile, 0.0, params);
    double dboundary = profile_derivative(profile, 1.0, params);
    py::dict d;
    d["J_radial"] = J;
    d["K_radial_raw"] = K;
    d["E_radial_raw"] = E;
    d["raw_boundary"] = boundary;
    d["raw_center"] = center;
    d["raw_max_abs"] = max_abs;
    d["raw_r2_rms"] = std::sqrt(K / J);
    d["raw_energy_rms"] = std::sqrt(2.0 * E);
    d["raw_boundary_derivative"] = dboundary;
    return d;
}

static double normalization_scale(const std::string& profile, const std::string& normalization_in, const std::map<std::string, double>& params = {}, int n_radial = 200000) {
    std::string norm = lower_copy(normalization_in);
    py::dict info = raw_info(profile, params, n_radial);
    double denom = 1.0;
    if (norm == "boundary" || norm == "edge") denom = info["raw_boundary"].cast<double>();
    else if (norm == "max" || norm == "peak") denom = info["raw_max_abs"].cast<double>();
    else if (norm == "rms_r2" || norm == "r2_rms" || norm == "weighted_rms") denom = info["raw_r2_rms"].cast<double>();
    else if (norm == "none" || norm == "raw") denom = 1.0;
    else throw std::runtime_error("unknown normalization: " + normalization_in);
    if (std::abs(denom) < 1e-300) throw std::runtime_error("normalization denominator too small");
    return 1.0 / denom;
}

static py::dict profile_metrics(
    const std::string& profile,
    double a_core,
    double rho_f,
    double v_ref,
    const std::string& normalization = "boundary",
    const std::map<std::string, double>& params = {},
    int n_radial = 200000
) {
    if (a_core <= 0.0 || rho_f <= 0.0 || v_ref <= 0.0) throw std::runtime_error("a_core, rho_f and v_ref must be positive");
    py::dict info = raw_info(profile, params, n_radial);
    double scale = normalization_scale(profile, normalization, params, n_radial);
    double J_rad = info["J_radial"].cast<double>();
    double K_rad = info["K_radial_raw"].cast<double>();
    double E_rad = info["E_radial_raw"].cast<double>();

    double J = 2.0 * PI * std::pow(a_core, 4) * J_rad;
    double Kgeom = 2.0 * PI * std::pow(a_core, 4) * scale*scale * K_rad;
    double Egeom = 2.0 * PI * a_core*a_core * scale*scale * E_rad;
    double I = rho_f * J;
    double K_chi = rho_f * v_ref*v_ref * Kgeom;
    double c = std::sqrt(K_chi / I);
    double energy_per_length = 0.5 * rho_f * v_ref*v_ref * Egeom;

    double boundary_over_v = scale * info["raw_boundary"].cast<double>();
    double center_over_v = scale * info["raw_center"].cast<double>();
    double max_over_v = scale * info["raw_max_abs"].cast<double>();
    double boundary_slope_scaled = scale * info["raw_boundary_derivative"].cast<double>();
    double boundary_log_slope = (std::abs(boundary_over_v) > 1e-300) ? boundary_slope_scaled / boundary_over_v : std::numeric_limits<double>::quiet_NaN();
    double gamma_boundary = 2.0 * PI * a_core * v_ref * boundary_over_v;
    double gamma_ref = 2.0 * PI * a_core * v_ref;
    double J_analytic = 0.5 * PI * std::pow(a_core, 4);

    int axis_regular = (std::abs(center_over_v) < 1e-3) ? 1 : 0;
    int boundary_matches = (std::abs(boundary_over_v - 1.0) < 1e-6) ? 1 : 0;
    int exterior_slope_matches = (std::abs(boundary_log_slope + 1.0) < 5e-2) ? 1 : 0;
    int finite_energy = (std::isfinite(energy_per_length) && std::abs(energy_per_length) < 1e100) ? 1 : 0;
    int r2_rms_matches_ref = (std::abs(c / v_ref - 1.0) < 1e-6) ? 1 : 0;
    std::string norm_low = lower_copy(normalization);
    int calibration_mode = (norm_low == "rms_r2" || norm_low == "r2_rms" || norm_low == "weighted_rms") ? 1 : 0;
    int score = axis_regular + boundary_matches + exterior_slope_matches + finite_energy;

    py::dict d;
    d["profile"] = profile;
    d["normalization"] = normalization;
    d["a_core"] = a_core;
    d["rho_f"] = rho_f;
    d["v_ref"] = v_ref;
    d["scale"] = scale;
    d["I_chi"] = I;
    d["K_chi"] = K_chi;
    d["c_chi"] = c;
    d["c_over_v_ref"] = c / v_ref;
    d["J_numeric"] = J;
    d["J_analytic_disk"] = J_analytic;
    d["J_rel_error"] = J / J_analytic - 1.0;
    d["Kgeom"] = Kgeom;
    d["Kgeom_over_J"] = Kgeom / J;
    d["Egeom"] = Egeom;
    d["energy_per_length"] = energy_per_length;
    d["gamma_boundary"] = gamma_boundary;
    d["gamma_ref"] = gamma_ref;
    d["gamma_boundary_over_ref"] = gamma_boundary / gamma_ref;
    d["boundary_over_v"] = boundary_over_v;
    d["center_over_v"] = center_over_v;
    d["max_over_v"] = max_over_v;
    d["boundary_log_slope"] = boundary_log_slope;
    d["axis_regular"] = axis_regular;
    d["boundary_matches"] = boundary_matches;
    d["exterior_slope_matches"] = exterior_slope_matches;
    d["finite_energy"] = finite_energy;
    d["r2_rms_matches_ref"] = r2_rms_matches_ref;
    d["calibration_mode"] = calibration_mode;
    d["admissibility_score"] = score;
    d["n_radial"] = n_radial;
    return d;
}

static py::list default_four_profiles() {
    py::list rows;
    rows.append(py::make_tuple("uniform", "boundary", std::map<std::string,double>{}, "uniform boundary"));
    rows.append(py::make_tuple("solid_body", "boundary", std::map<std::string,double>{}, "solid-body boundary"));
    rows.append(py::make_tuple("irrotational_reg", "boundary", std::map<std::string,double>{{"eps",0.05}}, "regularized 1/r boundary, eps=0.05"));
    rows.append(py::make_tuple("gaussian_core", "max", std::map<std::string,double>{{"sigma",0.35}}, "Gaussian core max, sigma=0.35"));
    return rows;
}

static py::list extended_profiles() {
    py::list rows = default_four_profiles();
    rows.append(py::make_tuple("rankine_matched", "boundary", std::map<std::string,double>{{"core",0.35}}, "Rankine matched boundary, core=0.35"));
    rows.append(py::make_tuple("solid_body", "rms_r2", std::map<std::string,double>{}, "solid-body r2-RMS calibration (forces c/v=1)"));
    return rows;
}

static py::list horn_loop_frequency_ratios(double c_over_v, int n_max = 32, int n_grid = 4096) {
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

static py::list spectrum_convergence(double c_over_v = 1.0, int n_max = 32, const std::vector<int>& grids = {128,256,512,1024,2048,4096,8192}) {
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

PYBIND11_MODULE(sst_chi_phase_v4, m) {
    m.doc() = "SST chi-phase v4: four-profile core admissibility selector";
    m.def("raw_profile", &raw_profile, py::arg("profile"), py::arg("x"), py::arg("params") = std::map<std::string,double>{});
    m.def("profile_derivative", &profile_derivative, py::arg("profile"), py::arg("x"), py::arg("params") = std::map<std::string,double>{});
    m.def("raw_info", &raw_info, py::arg("profile"), py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("normalization_scale", &normalization_scale, py::arg("profile"), py::arg("normalization"), py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("profile_metrics", &profile_metrics,
          py::arg("profile"), py::arg("a_core"), py::arg("rho_f"), py::arg("v_ref"),
          py::arg("normalization") = "boundary", py::arg("params") = std::map<std::string,double>{}, py::arg("n_radial") = 200000);
    m.def("default_four_profiles", &default_four_profiles);
    m.def("extended_profiles", &extended_profiles);
    m.def("horn_loop_frequency_ratios", &horn_loop_frequency_ratios, py::arg("c_over_v"), py::arg("n_max") = 32, py::arg("n_grid") = 4096);
    m.def("spectrum_convergence", &spectrum_convergence, py::arg("c_over_v") = 1.0, py::arg("n_max") = 32, py::arg("grids") = std::vector<int>{128,256,512,1024,2048,4096,8192});
}
