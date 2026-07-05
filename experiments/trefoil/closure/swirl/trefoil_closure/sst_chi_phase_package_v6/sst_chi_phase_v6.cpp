#include <pybind11/pybind11.h>
#include <cmath>
#include <stdexcept>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;

double phi() { return (1.0 + std::sqrt(5.0)) / 2.0; }
double analytic_root() { return (-13.0 + std::sqrt(385.0)) / 4.0; }

double smooth_matched_poly(double x, double a0) {
    const double x2 = x * x;
    return x * (a0 + (3.0 - 2.0 * a0) * x2 + (a0 - 2.0) * x2 * x2);
}

double smooth_matched_poly_prime(double x, double a0) {
    return a0 + 3.0 * (3.0 - 2.0 * a0) * x * x + 5.0 * (a0 - 2.0) * std::pow(x, 4.0);
}

double c2_over_v2_analytic(double a0) {
    return (2.0 * a0 * a0 + 13.0 * a0 + 78.0) / 105.0;
}

double c_over_v_analytic(double a0) {
    return std::sqrt(c2_over_v2_analytic(a0));
}

double root_residual(double a0) {
    return c2_over_v2_analytic(a0) - 1.0;
}

double bisection_root(double lo=0.0, double hi=3.0, double tol=1e-14, int max_iter=200) {
    double flo = root_residual(lo);
    double fhi = root_residual(hi);
    if (flo == 0.0) return lo;
    if (fhi == 0.0) return hi;
    if (flo * fhi > 0.0) throw std::runtime_error("Root not bracketed");
    for (int k=0; k<max_iter; ++k) {
        double mid = 0.5 * (lo + hi);
        double fm = root_residual(mid);
        if (std::abs(fm) < tol || 0.5 * (hi - lo) < tol) return mid;
        if (flo * fm <= 0.0) { hi = mid; fhi = fm; }
        else { lo = mid; flo = fm; }
    }
    return 0.5 * (lo + hi);
}

double c2_over_v2_numeric(double a0, int n=400000) {
    if (n <= 0) throw std::runtime_error("n must be positive");
    const double h = 1.0 / static_cast<double>(n);
    double total = 0.0;
    for (int i=0; i<n; ++i) {
        const double x = (static_cast<double>(i) + 0.5) * h;
        const double f = smooth_matched_poly(x, a0);
        total += f * f * x * x * x;
    }
    return 4.0 * total * h;
}

double grad_energy_analytic(double a0) {
    return (2.0 * a0 * a0 - 7.0 * a0 + 12.0) / 12.0;
}

double curvature_energy_analytic(double a0) {
    return 6.0 * a0 * a0 - 28.0 * a0 + 41.0;
}

double shape_energy_analytic(double a0) {
    return (2.0 * a0 * a0 - 2.0 * a0 + 1.0) / 120.0;
}

PYBIND11_MODULE(sst_chi_phase_v6, m) {
    m.doc() = "SST chi-phase v6 smooth-matched root selector";
    m.def("phi", &phi);
    m.def("analytic_root", &analytic_root);
    m.def("smooth_matched_poly", &smooth_matched_poly);
    m.def("smooth_matched_poly_prime", &smooth_matched_poly_prime);
    m.def("c2_over_v2_analytic", &c2_over_v2_analytic);
    m.def("c_over_v_analytic", &c_over_v_analytic);
    m.def("root_residual", &root_residual);
    m.def("bisection_root", &bisection_root, py::arg("lo")=0.0, py::arg("hi")=3.0, py::arg("tol")=1e-14, py::arg("max_iter")=200);
    m.def("c2_over_v2_numeric", &c2_over_v2_numeric, py::arg("a0"), py::arg("n")=400000);
    m.def("grad_energy_analytic", &grad_energy_analytic);
    m.def("curvature_energy_analytic", &curvature_energy_analytic);
    m.def("shape_energy_analytic", &shape_energy_analytic);
}
