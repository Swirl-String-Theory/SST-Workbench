\
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

namespace py = pybind11;

static double dispersion_epsilon(double E_GeV, double E_liv_GeV, int n) {
    if (!(E_GeV > 0.0) || !(E_liv_GeV > 0.0) || (n != 1 && n != 2))
        throw std::invalid_argument("Require E>0, E_LIV>0 and n in {1,2}");
    return std::pow(E_GeV / E_liv_GeV, n);
}

static double group_velocity_fraction(double E_GeV, double E_liv_GeV, int n) {
    // Leading-order subluminal result for p^2=E^2[1+(E/E_LIV)^n], c=1.
    const double eps = dispersion_epsilon(E_GeV, E_liv_GeV, n);
    return 1.0 - 0.5 * (n + 1.0) * eps;
}

static py::dict intersect_bounds(const std::vector<double>& lowers,
                                 const std::vector<double>& uppers) {
    double lo = 0.0;
    double hi = std::numeric_limits<double>::infinity();
    if (!lowers.empty()) lo = *std::max_element(lowers.begin(), lowers.end());
    if (!uppers.empty()) hi = *std::min_element(uppers.begin(), uppers.end());
    py::dict out;
    out["lower"] = lo;
    out["upper"] = hi;
    out["nonempty"] = lo < hi;
    if (std::isfinite(hi) && hi > 0.0) out["log10_span"] = (lo > 0.0) ? std::log10(hi/lo) : std::numeric_limits<double>::infinity();
    else out["log10_span"] = std::numeric_limits<double>::infinity();
    return out;
}

static double poisson_at_least_one(double lambda) {
    if (lambda < 0.0) throw std::invalid_argument("lambda must be non-negative");
    return -std::expm1(-lambda);
}

static double k_times_length(double E_eV, double length_m) {
    // k*l = E*l/(hbar*c), with hbar*c in eV*m.
    constexpr double hbar_c_eVm = 1.9732698045930252e-7;
    if (!(E_eV >= 0.0) || !(length_m >= 0.0)) throw std::invalid_argument("non-negative inputs required");
    return E_eV * length_m / hbar_c_eVm;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Native kernels for CGTDLEF blind falsifier";
    m.def("dispersion_epsilon", &dispersion_epsilon);
    m.def("group_velocity_fraction", &group_velocity_fraction);
    m.def("intersect_bounds", &intersect_bounds);
    m.def("poisson_at_least_one", &poisson_at_least_one);
    m.def("k_times_length", &k_times_length);
}
