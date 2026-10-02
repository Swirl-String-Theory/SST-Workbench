// sst_chi_phase.cpp
// Self-contained pybind11 kernel for SST internal torsional phase verification.
//
// Research Track target:
//   I_chi = rho_f * int_A r_perp^2 dA
//   K_chi = rho_f * v_swirl^2 * int_A r_perp^2 dA
//   c_chi = sqrt(K_chi / I_chi) -> v_swirl
//
// This kernel deliberately tests the local internal phase sector only. It does
// not claim to derive electromagnetism, SU(2), SU(3), or the SST mass spectrum.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;

static void require_positive(double x, const char* name) {
    if (!(x > 0.0) || !std::isfinite(x)) {
        throw std::runtime_error(std::string(name) + " must be positive and finite.");
    }
}

double transverse_moment_circular_analytic(double a_core) {
    require_positive(a_core, "a_core");
    return 0.5 * PI * std::pow(a_core, 4);
}

// Midpoint quadrature of int_A r_perp^2 dA over a circular tube cross-section:
// int_0^a int_0^{2pi} r^2 * r dr dtheta.
double transverse_moment_circular_quadrature(double a_core, int n_r, int n_theta) {
    require_positive(a_core, "a_core");
    if (n_r <= 0 || n_theta <= 0) {
        throw std::runtime_error("n_r and n_theta must be positive.");
    }

    const double dr = a_core / static_cast<double>(n_r);
    const double dtheta = 2.0 * PI / static_cast<double>(n_theta);
    double moment = 0.0;

    for (int ir = 0; ir < n_r; ++ir) {
        const double r = (static_cast<double>(ir) + 0.5) * dr;
        const double shell = r * r * r * dr * dtheta;
        for (int it = 0; it < n_theta; ++it) {
            moment += shell;
        }
    }
    return moment;
}

py::dict compute_chi_constants(
    double rho_f,
    double v_swirl,
    double a_core,
    int n_r,
    int n_theta
) {
    require_positive(rho_f, "rho_f");
    require_positive(v_swirl, "v_swirl");
    require_positive(a_core, "a_core");

    const double J_analytic = transverse_moment_circular_analytic(a_core);
    const double J_numeric = transverse_moment_circular_quadrature(a_core, n_r, n_theta);

    const double I_analytic = rho_f * J_analytic;
    const double K_analytic = rho_f * v_swirl * v_swirl * J_analytic;
    const double c_analytic = std::sqrt(K_analytic / I_analytic);

    const double I_numeric = rho_f * J_numeric;
    const double K_numeric = rho_f * v_swirl * v_swirl * J_numeric;
    const double c_numeric = std::sqrt(K_numeric / I_numeric);

    py::dict out;
    out["a_core"] = a_core;
    out["J_analytic"] = J_analytic;
    out["J_numeric"] = J_numeric;
    out["J_rel_error"] = (J_numeric - J_analytic) / J_analytic;
    out["I_chi_analytic"] = I_analytic;
    out["K_chi_analytic"] = K_analytic;
    out["c_chi_analytic"] = c_analytic;
    out["c_chi_over_v_analytic"] = c_analytic / v_swirl;
    out["I_chi_numeric"] = I_numeric;
    out["K_chi_numeric"] = K_numeric;
    out["c_chi_numeric"] = c_numeric;
    out["c_chi_over_v_numeric"] = c_numeric / v_swirl;
    return out;
}

// Continuous gapless internal phase frequencies on a closed domain L_chi.
// omega_n = 2*pi*v_swirl*|n|/L_chi.
std::vector<double> continuous_phase_spectrum(
    double v_swirl,
    double L_chi,
    int n_max,
    double omega_gap
) {
    require_positive(v_swirl, "v_swirl");
    require_positive(L_chi, "L_chi");
    if (n_max <= 0) {
        throw std::runtime_error("n_max must be positive.");
    }
    if (omega_gap < 0.0 || !std::isfinite(omega_gap)) {
        throw std::runtime_error("omega_gap must be non-negative and finite.");
    }

    std::vector<double> out;
    out.reserve(static_cast<size_t>(n_max));
    for (int n = 1; n <= n_max; ++n) {
        const double k = 2.0 * PI * static_cast<double>(n) / L_chi;
        out.push_back(std::sqrt(omega_gap * omega_gap + v_swirl * v_swirl * k * k));
    }
    return out;
}

// Finite-difference spectrum for the periodic wave equation on a ring.
// Central second derivative eigenvalue: k_eff = 2/ds * sin(pi*n/N).
std::vector<double> discrete_phase_spectrum(
    double v_swirl,
    double L_chi,
    int n_grid,
    int n_max,
    double omega_gap
) {
    require_positive(v_swirl, "v_swirl");
    require_positive(L_chi, "L_chi");
    if (n_grid < 8) {
        throw std::runtime_error("n_grid must be at least 8.");
    }
    if (n_max <= 0 || n_max >= n_grid / 2) {
        throw std::runtime_error("n_max must be in [1, n_grid/2).");
    }
    if (omega_gap < 0.0 || !std::isfinite(omega_gap)) {
        throw std::runtime_error("omega_gap must be non-negative and finite.");
    }

    const double ds = L_chi / static_cast<double>(n_grid);
    std::vector<double> out;
    out.reserve(static_cast<size_t>(n_max));
    for (int n = 1; n <= n_max; ++n) {
        const double k_eff = (2.0 / ds) * std::sin(PI * static_cast<double>(n) / static_cast<double>(n_grid));
        out.push_back(std::sqrt(omega_gap * omega_gap + v_swirl * v_swirl * k_eff * k_eff));
    }
    return out;
}

PYBIND11_MODULE(sst_chi_phase, m) {
    m.doc() = "SST internal torsional phase verification kernel";
    m.def("transverse_moment_circular_analytic", &transverse_moment_circular_analytic,
          "Analytic int_A r_perp^2 dA for a circular cross-section.");
    m.def("transverse_moment_circular_quadrature", &transverse_moment_circular_quadrature,
          "Midpoint quadrature int_A r_perp^2 dA for a circular cross-section.");
    m.def("compute_chi_constants", &compute_chi_constants,
          "Compute I_chi, K_chi, c_chi and numerical quadrature diagnostics.");
    m.def("continuous_phase_spectrum", &continuous_phase_spectrum,
          "Continuous internal phase spectrum on a closed domain.");
    m.def("discrete_phase_spectrum", &discrete_phase_spectrum,
          "Finite-difference internal phase spectrum on a periodic ring.");
}
