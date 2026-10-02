// sst_chi_phase_v2.cpp
// Self-contained pybind11 kernel for SST internal torsional chi-phase verification v2.
//
// Research Track target:
//   I_chi = rho_f * J_A
//   K_chi = rho_f * v_swirl^2 * J_A
//   c_chi = sqrt(K_chi / I_chi) -> v_swirl
//
// v2 extends v1 beyond circular cross-sections:
//   - circle / annulus / ellipse transverse moments
//   - anisotropic moment tensor checks
//   - periodic phase-ring spectral convergence
//
// This kernel deliberately tests the local internal phase sector only. It does
// not claim to derive electromagnetism, SU(2), SU(3), or the SST mass spectrum.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;

static void require_positive(double x, const char* name) {
    if (!(x > 0.0) || !std::isfinite(x)) {
        throw std::runtime_error(std::string(name) + " must be positive and finite.");
    }
}

static void require_nonnegative(double x, const char* name) {
    if (x < 0.0 || !std::isfinite(x)) {
        throw std::runtime_error(std::string(name) + " must be non-negative and finite.");
    }
}

static void require_quadrature(int n_r, int n_theta) {
    if (n_r <= 0 || n_theta <= 0) {
        throw std::runtime_error("n_r and n_theta must be positive.");
    }
}

static py::dict constants_from_moment(double rho_f, double v_swirl, double J) {
    require_positive(rho_f, "rho_f");
    require_positive(v_swirl, "v_swirl");
    require_positive(J, "J");

    const double I = rho_f * J;
    const double K = rho_f * v_swirl * v_swirl * J;
    const double c = std::sqrt(K / I);

    py::dict out;
    out["J"] = J;
    out["I_chi"] = I;
    out["K_chi"] = K;
    out["c_chi"] = c;
    out["c_chi_over_v"] = c / v_swirl;
    return out;
}

// ---------------------------------------------------------------------------
// Analytic transverse moments J = int_A (x^2 + y^2) dA.
// ---------------------------------------------------------------------------

double moment_circle_analytic(double a) {
    require_positive(a, "a");
    return 0.5 * PI * std::pow(a, 4);
}

double moment_annulus_analytic(double a_inner, double a_outer) {
    require_nonnegative(a_inner, "a_inner");
    require_positive(a_outer, "a_outer");
    if (!(a_inner < a_outer)) {
        throw std::runtime_error("a_inner must be smaller than a_outer.");
    }
    return 0.5 * PI * (std::pow(a_outer, 4) - std::pow(a_inner, 4));
}

double moment_ellipse_analytic(double a, double b) {
    require_positive(a, "a");
    require_positive(b, "b");
    // int_ellipse x^2 dA = pi a^3 b / 4 ; int y^2 dA = pi a b^3 / 4.
    return 0.25 * PI * a * b * (a * a + b * b);
}

py::dict ellipse_tensor_analytic(double a, double b) {
    require_positive(a, "a");
    require_positive(b, "b");
    py::dict out;
    out["M_xx"] = 0.25 * PI * std::pow(a, 3) * b; // int x^2 dA
    out["M_yy"] = 0.25 * PI * a * std::pow(b, 3); // int y^2 dA
    out["M_xy"] = 0.0;
    out["J_trace"] = moment_ellipse_analytic(a, b);
    return out;
}

// ---------------------------------------------------------------------------
// Midpoint quadrature in polar / mapped-polar coordinates.
// ---------------------------------------------------------------------------

double moment_circle_quadrature(double a, int n_r, int n_theta) {
    require_positive(a, "a");
    require_quadrature(n_r, n_theta);
    const double dr = a / static_cast<double>(n_r);
    const double dtheta = 2.0 * PI / static_cast<double>(n_theta);
    double moment = 0.0;
    for (int ir = 0; ir < n_r; ++ir) {
        const double r = (static_cast<double>(ir) + 0.5) * dr;
        const double shell = r * r * r * dr * dtheta;
        moment += static_cast<double>(n_theta) * shell;
    }
    return moment;
}

double moment_annulus_quadrature(double a_inner, double a_outer, int n_r, int n_theta) {
    require_nonnegative(a_inner, "a_inner");
    require_positive(a_outer, "a_outer");
    if (!(a_inner < a_outer)) {
        throw std::runtime_error("a_inner must be smaller than a_outer.");
    }
    require_quadrature(n_r, n_theta);
    const double dr = (a_outer - a_inner) / static_cast<double>(n_r);
    const double dtheta = 2.0 * PI / static_cast<double>(n_theta);
    double moment = 0.0;
    for (int ir = 0; ir < n_r; ++ir) {
        const double r = a_inner + (static_cast<double>(ir) + 0.5) * dr;
        const double shell = r * r * r * dr * dtheta;
        moment += static_cast<double>(n_theta) * shell;
    }
    return moment;
}

double moment_ellipse_quadrature(double a, double b, int n_r, int n_theta) {
    require_positive(a, "a");
    require_positive(b, "b");
    require_quadrature(n_r, n_theta);
    const double dr = 1.0 / static_cast<double>(n_r);
    const double dtheta = 2.0 * PI / static_cast<double>(n_theta);
    double moment = 0.0;
    for (int ir = 0; ir < n_r; ++ir) {
        const double r = (static_cast<double>(ir) + 0.5) * dr;
        for (int it = 0; it < n_theta; ++it) {
            const double th = (static_cast<double>(it) + 0.5) * dtheta;
            const double x = a * r * std::cos(th);
            const double y = b * r * std::sin(th);
            const double jac = a * b * r;
            moment += (x * x + y * y) * jac * dr * dtheta;
        }
    }
    return moment;
}

py::dict ellipse_tensor_quadrature(double a, double b, int n_r, int n_theta) {
    require_positive(a, "a");
    require_positive(b, "b");
    require_quadrature(n_r, n_theta);
    const double dr = 1.0 / static_cast<double>(n_r);
    const double dtheta = 2.0 * PI / static_cast<double>(n_theta);
    double mxx = 0.0, myy = 0.0, mxy = 0.0;
    for (int ir = 0; ir < n_r; ++ir) {
        const double r = (static_cast<double>(ir) + 0.5) * dr;
        for (int it = 0; it < n_theta; ++it) {
            const double th = (static_cast<double>(it) + 0.5) * dtheta;
            const double x = a * r * std::cos(th);
            const double y = b * r * std::sin(th);
            const double weight = a * b * r * dr * dtheta;
            mxx += x * x * weight;
            myy += y * y * weight;
            mxy += x * y * weight;
        }
    }
    py::dict out;
    out["M_xx"] = mxx;
    out["M_yy"] = myy;
    out["M_xy"] = mxy;
    out["J_trace"] = mxx + myy;
    return out;
}

py::dict compute_chi_from_shape(
    const std::string& shape,
    double rho_f,
    double v_swirl,
    double p1,
    double p2,
    int n_r,
    int n_theta
) {
    require_positive(rho_f, "rho_f");
    require_positive(v_swirl, "v_swirl");
    double J_analytic = 0.0;
    double J_numeric = 0.0;

    if (shape == "circle") {
        J_analytic = moment_circle_analytic(p1);
        J_numeric = moment_circle_quadrature(p1, n_r, n_theta);
    } else if (shape == "annulus") {
        J_analytic = moment_annulus_analytic(p1, p2);
        J_numeric = moment_annulus_quadrature(p1, p2, n_r, n_theta);
    } else if (shape == "ellipse") {
        J_analytic = moment_ellipse_analytic(p1, p2);
        J_numeric = moment_ellipse_quadrature(p1, p2, n_r, n_theta);
    } else {
        throw std::runtime_error("Unknown shape. Use circle, annulus, or ellipse.");
    }

    const double I_analytic = rho_f * J_analytic;
    const double K_analytic = rho_f * v_swirl * v_swirl * J_analytic;
    const double c_analytic = std::sqrt(K_analytic / I_analytic);

    const double I_numeric = rho_f * J_numeric;
    const double K_numeric = rho_f * v_swirl * v_swirl * J_numeric;
    const double c_numeric = std::sqrt(K_numeric / I_numeric);

    py::dict out;
    out["shape"] = shape;
    out["p1"] = p1;
    out["p2"] = p2;
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

py::dict anisotropic_ellipse_speed_check(double rho_f, double v_swirl, double a, double b) {
    require_positive(rho_f, "rho_f");
    require_positive(v_swirl, "v_swirl");
    py::dict mt = ellipse_tensor_analytic(a, b);
    const double mxx = mt["M_xx"].cast<double>();
    const double myy = mt["M_yy"].cast<double>();

    // Canonical shared-moment/tensor convention: K_axis = rho v^2 M_axis.
    const double c_x_shared = std::sqrt((rho_f * v_swirl * v_swirl * mxx) / (rho_f * mxx));
    const double c_y_shared = std::sqrt((rho_f * v_swirl * v_swirl * myy) / (rho_f * myy));

    // Counterfactual diagnostic: impose one scalar stiffness against anisotropic inertia.
    // This is NOT the canonical SST ansatz; it demonstrates the sort of splitting that
    // would appear if the shared-moment assumption failed.
    const double m_mean = 0.5 * (mxx + myy);
    const double c_x_counter = std::sqrt((rho_f * v_swirl * v_swirl * m_mean) / (rho_f * mxx));
    const double c_y_counter = std::sqrt((rho_f * v_swirl * v_swirl * m_mean) / (rho_f * myy));

    py::dict out;
    out["a"] = a;
    out["b"] = b;
    out["aspect_b_over_a"] = b / a;
    out["M_xx"] = mxx;
    out["M_yy"] = myy;
    out["canonical_cx_over_v"] = c_x_shared / v_swirl;
    out["canonical_cy_over_v"] = c_y_shared / v_swirl;
    out["counterfactual_cx_over_v"] = c_x_counter / v_swirl;
    out["counterfactual_cy_over_v"] = c_y_counter / v_swirl;
    out["counterfactual_split_abs"] = std::abs(c_x_counter - c_y_counter) / v_swirl;
    return out;
}

// ---------------------------------------------------------------------------
// Internal phase spectra.
// ---------------------------------------------------------------------------

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
    require_nonnegative(omega_gap, "omega_gap");

    std::vector<double> out;
    out.reserve(static_cast<size_t>(n_max));
    for (int n = 1; n <= n_max; ++n) {
        const double k = 2.0 * PI * static_cast<double>(n) / L_chi;
        out.push_back(std::sqrt(omega_gap * omega_gap + v_swirl * v_swirl * k * k));
    }
    return out;
}

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
    require_nonnegative(omega_gap, "omega_gap");

    const double ds = L_chi / static_cast<double>(n_grid);
    std::vector<double> out;
    out.reserve(static_cast<size_t>(n_max));
    for (int n = 1; n <= n_max; ++n) {
        const double k_eff = (2.0 / ds) * std::sin(PI * static_cast<double>(n) / static_cast<double>(n_grid));
        out.push_back(std::sqrt(omega_gap * omega_gap + v_swirl * v_swirl * k_eff * k_eff));
    }
    return out;
}

py::dict spectrum_error_summary(double v_swirl, double L_chi, int n_grid, int n_max, double omega_gap) {
    std::vector<double> cont = continuous_phase_spectrum(v_swirl, L_chi, n_max, omega_gap);
    std::vector<double> disc = discrete_phase_spectrum(v_swirl, L_chi, n_grid, n_max, omega_gap);
    double max_abs_rel = 0.0;
    double omega1_ratio = disc[0] / cont[0];
    for (int i = 0; i < n_max; ++i) {
        const double rel = disc[i] / cont[i] - 1.0;
        max_abs_rel = std::max(max_abs_rel, std::abs(rel));
    }
    py::dict out;
    out["n_grid"] = n_grid;
    out["n_max"] = n_max;
    out["omega1_ratio_disc_over_cont"] = omega1_ratio;
    out["max_abs_rel_error"] = max_abs_rel;
    return out;
}

PYBIND11_MODULE(sst_chi_phase_v2, m) {
    m.doc() = "SST internal torsional chi-phase verification kernel v2";
    m.def("constants_from_moment", &constants_from_moment, "Compute I, K, c from a transverse moment J.");
    m.def("moment_circle_analytic", &moment_circle_analytic, "Analytic J for a circular cross-section.");
    m.def("moment_circle_quadrature", &moment_circle_quadrature, "Quadrature J for a circular cross-section.");
    m.def("moment_annulus_analytic", &moment_annulus_analytic, "Analytic J for an annular cross-section.");
    m.def("moment_annulus_quadrature", &moment_annulus_quadrature, "Quadrature J for an annular cross-section.");
    m.def("moment_ellipse_analytic", &moment_ellipse_analytic, "Analytic J for an elliptical cross-section.");
    m.def("moment_ellipse_quadrature", &moment_ellipse_quadrature, "Quadrature J for an elliptical cross-section.");
    m.def("ellipse_tensor_analytic", &ellipse_tensor_analytic, "Analytic second-moment tensor for ellipse.");
    m.def("ellipse_tensor_quadrature", &ellipse_tensor_quadrature, "Quadrature second-moment tensor for ellipse.");
    m.def("compute_chi_from_shape", &compute_chi_from_shape, "Compute chi constants for circle/annulus/ellipse.");
    m.def("anisotropic_ellipse_speed_check", &anisotropic_ellipse_speed_check, "Canonical and counterfactual anisotropic speed checks.");
    m.def("continuous_phase_spectrum", &continuous_phase_spectrum, "Continuous internal phase spectrum on a closed domain.");
    m.def("discrete_phase_spectrum", &discrete_phase_spectrum, "Finite-difference internal phase spectrum on a periodic ring.");
    m.def("spectrum_error_summary", &spectrum_error_summary, "Discrete spectrum convergence summary.");
}
