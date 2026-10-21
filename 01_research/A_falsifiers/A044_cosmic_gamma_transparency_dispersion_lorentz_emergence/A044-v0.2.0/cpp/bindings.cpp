#include <pybind11/pybind11.h>
#include <cmath>
#include <stdexcept>
namespace py = pybind11;

static double dispersion_epsilon(double E_GeV, double E_star_GeV, int n) {
    if (!(E_GeV > 0.0) || !(E_star_GeV > 0.0) || (n != 1 && n != 2))
        throw std::invalid_argument("Require E>0, E_star>0 and n in {1,2}");
    return std::pow(E_GeV/E_star_GeV, n);
}
static double group_velocity_fraction_exact(double E_GeV, double E_star_GeV, int n) {
    const double x=dispersion_epsilon(E_GeV,E_star_GeV,n);
    return std::sqrt(1.0+x)/(1.0+(1.0+0.5*n)*x);
}
static double poisson_at_least_one(double lambda) {
    if (lambda < 0.0) throw std::invalid_argument("lambda must be non-negative");
    return -std::expm1(-lambda);
}
PYBIND11_MODULE(_native,m) {
    m.doc()="A044 v0.2.0 native kernels";
    m.def("dispersion_epsilon",&dispersion_epsilon);
    m.def("group_velocity_fraction_exact",&group_velocity_fraction_exact);
    m.def("poisson_at_least_one",&poisson_at_least_one);
}
