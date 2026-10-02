#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstdint>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

py::array_t<double> biot_savart(
    py::array_t<double, py::array::c_style | py::array::forcecast> points,
    py::array_t<std::int64_t, py::array::c_style | py::array::forcecast> component_offsets,
    double gamma,
    double core_radius)
{
    auto P = points.unchecked<2>();
    auto O = component_offsets.unchecked<1>();
    if (P.shape(1) != 3) throw std::runtime_error("points must have shape (N,3)");
    const py::ssize_t n = P.shape(0);
    py::array_t<double> out({py::ssize_t(n), py::ssize_t(3)});
    auto V = out.mutable_unchecked<2>();
    const double a2 = core_radius * core_radius;
    const double pref = gamma / (4.0 * 3.141592653589793238462643383279502884);

    #pragma omp parallel for if(n > 64)
    for (py::ssize_t i = 0; i < n; ++i) {
        double vx = 0.0, vy = 0.0, vz = 0.0;
        for (py::ssize_t c = 0; c + 1 < O.shape(0); ++c) {
            const std::int64_t lo = O(c), hi = O(c + 1);
            if (hi - lo < 3) continue;
            for (std::int64_t j = lo; j < hi; ++j) {
                const std::int64_t k = (j + 1 < hi) ? (j + 1) : lo;
                const double dlx = P(k,0) - P(j,0);
                const double dly = P(k,1) - P(j,1);
                const double dlz = P(k,2) - P(j,2);
                const double mx = 0.5 * (P(k,0) + P(j,0));
                const double my = 0.5 * (P(k,1) + P(j,1));
                const double mz = 0.5 * (P(k,2) + P(j,2));
                const double rx = P(i,0) - mx;
                const double ry = P(i,1) - my;
                const double rz = P(i,2) - mz;
                const double den = std::pow(rx*rx + ry*ry + rz*rz + a2, 1.5);
                if (den <= 0.0) continue;
                vx += (dly*rz - dlz*ry) / den;
                vy += (dlz*rx - dlx*rz) / den;
                vz += (dlx*ry - dly*rx) / den;
            }
        }
        V(i,0) = pref * vx;
        V(i,1) = pref * vy;
        V(i,2) = pref * vz;
    }
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "C++17 regularized filament Biot-Savart kernel for SST blind falsifier";
    m.def("biot_savart", &biot_savart,
          py::arg("points"), py::arg("component_offsets"),
          py::arg("gamma") = 1.0, py::arg("core_radius") = 0.05);
}
