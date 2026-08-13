#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

static inline std::array<double,3> sub3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}
static inline std::array<double,3> add3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[0]+b[0], a[1]+b[1], a[2]+b[2]};
}
static inline std::array<double,3> mul3(const std::array<double,3>& a, double s) {
    return {a[0]*s, a[1]*s, a[2]*s};
}
static inline double dot3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
}
static inline std::array<double,3> cross3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]};
}
static inline double norm2(const std::array<double,3>& a) { return dot3(a,a); }

double filament_energy(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                       double rho, double gamma, double core_radius) {
    auto p = points.unchecked<2>();
    if (p.shape(1) != 3 || p.shape(0) < 3) throw std::runtime_error("points must have shape (N,3), N>=3");
    const ssize_t n = p.shape(0);
    const double a2 = core_radius*core_radius;
    double sum = 0.0;
    for (ssize_t i=0; i<n; ++i) {
        ssize_t ip = (i+1)%n;
        std::array<double,3> xi{p(i,0),p(i,1),p(i,2)};
        std::array<double,3> xip{p(ip,0),p(ip,1),p(ip,2)};
        auto dli = sub3(xip,xi);
        auto mi = mul3(add3(xi,xip),0.5);
        for (ssize_t j=0; j<n; ++j) {
            ssize_t jp = (j+1)%n;
            std::array<double,3> xj{p(j,0),p(j,1),p(j,2)};
            std::array<double,3> xjp{p(jp,0),p(jp,1),p(jp,2)};
            auto dlj = sub3(xjp,xj);
            auto mj = mul3(add3(xj,xjp),0.5);
            auto r = sub3(mi,mj);
            const double denom = std::sqrt(norm2(r)+a2);
            sum += dot3(dli,dlj)/denom;
        }
    }
    return rho*gamma*gamma*sum/(8.0*PI);
}

py::array_t<double> biot_savart_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> points,
    double gamma, double core_radius,
    py::array_t<double, py::array::c_style | py::array::forcecast> background) {
    auto p = points.unchecked<2>();
    auto bg = background.unchecked<1>();
    if (p.shape(1) != 3 || p.shape(0) < 3) throw std::runtime_error("points must have shape (N,3), N>=3");
    if (bg.shape(0) != 3) throw std::runtime_error("background must have shape (3,)");
    const ssize_t n = p.shape(0);
    const double a2 = core_radius*core_radius;
    py::array_t<double> out({n, (ssize_t)3});
    auto v = out.mutable_unchecked<2>();
    const double pref = gamma/(4.0*PI);
    for (ssize_t i=0; i<n; ++i) {
        std::array<double,3> xi{p(i,0),p(i,1),p(i,2)};
        std::array<double,3> vi{bg(0),bg(1),bg(2)};
        for (ssize_t j=0; j<n; ++j) {
            ssize_t jp = (j+1)%n;
            std::array<double,3> xj{p(j,0),p(j,1),p(j,2)};
            std::array<double,3> xjp{p(jp,0),p(jp,1),p(jp,2)};
            auto dl = sub3(xjp,xj);
            auto mid = mul3(add3(xj,xjp),0.5);
            auto r = sub3(xi,mid);
            const double den = std::pow(norm2(r)+a2,1.5);
            auto c = cross3(dl,r);
            vi[0] += pref*c[0]/den;
            vi[1] += pref*c[1]/den;
            vi[2] += pref*c[2]/den;
        }
        v(i,0)=vi[0]; v(i,1)=vi[1]; v(i,2)=vi[2];
    }
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "SST preferred-frame / binary falsifier C++ kernels";
    m.def("filament_energy", &filament_energy,
          py::arg("points"), py::arg("rho"), py::arg("gamma"), py::arg("core_radius"));
    m.def("biot_savart_velocity", &biot_savart_velocity,
          py::arg("points"), py::arg("gamma"), py::arg("core_radius"), py::arg("background"));
}
