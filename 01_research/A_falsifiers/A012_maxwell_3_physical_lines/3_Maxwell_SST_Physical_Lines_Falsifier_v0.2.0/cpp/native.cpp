#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstddef>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

py::array_t<double> biot_savart_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> samples,
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_a,
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_b,
    double gamma,
    double core_radius,
    int threads = 0
) {
    auto s = samples.unchecked<2>();
    auto a = seg_a.unchecked<2>();
    auto b = seg_b.unchecked<2>();
    if (s.shape(1) != 3 || a.shape(1) != 3 || b.shape(1) != 3 || a.shape(0) != b.shape(0)) {
        throw std::runtime_error("samples, seg_a, seg_b must have shapes (N,3), (M,3), (M,3)");
    }
    const py::ssize_t n = s.shape(0);
    const py::ssize_t m = a.shape(0);
    py::array_t<double> out({n, py::ssize_t(3)});
    auto o = out.mutable_unchecked<2>();
    const double eps2 = core_radius * core_radius;
    const double pref = gamma / (4.0 * M_PI);
#ifdef _OPENMP
    if (threads > 0) omp_set_num_threads(threads);
#pragma omp parallel for schedule(static)
#endif
    for (py::ssize_t i = 0; i < n; ++i) {
        double vx = 0.0, vy = 0.0, vz = 0.0;
        const double sx = s(i,0), sy = s(i,1), sz = s(i,2);
        for (py::ssize_t j = 0; j < m; ++j) {
            const double dlx = b(j,0) - a(j,0);
            const double dly = b(j,1) - a(j,1);
            const double dlz = b(j,2) - a(j,2);
            const double mx = 0.5 * (a(j,0) + b(j,0));
            const double my = 0.5 * (a(j,1) + b(j,1));
            const double mz = 0.5 * (a(j,2) + b(j,2));
            const double rx = sx - mx;
            const double ry = sy - my;
            const double rz = sz - mz;
            const double r2 = rx*rx + ry*ry + rz*rz + eps2;
            const double inv = 1.0 / (r2 * std::sqrt(r2));
            // dℓ × r
            const double cx = dly*rz - dlz*ry;
            const double cy = dlz*rx - dlx*rz;
            const double cz = dlx*ry - dly*rx;
            vx += cx * inv;
            vy += cy * inv;
            vz += cz * inv;
        }
        o(i,0) = pref * vx;
        o(i,1) = pref * vy;
        o(i,2) = pref * vz;
    }
    return out;
}

py::dict build_info() {
    py::dict d;
#ifdef _OPENMP
    d["openmp"] = true;
    d["openmp_max_threads"] = omp_get_max_threads();
#else
    d["openmp"] = false;
    d["openmp_max_threads"] = 1;
#endif
    d["kernel"] = "regularized_midpoint_biot_savart";
    d["cpp_standard"] = "c++17";
    return d;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "SST Maxwell-3 fast regularized Biot-Savart kernel";
    m.def("biot_savart_velocity", &biot_savart_velocity,
          py::arg("samples"), py::arg("seg_a"), py::arg("seg_b"),
          py::arg("gamma"), py::arg("core_radius"), py::arg("threads") = 0,
          "Evaluate regularized midpoint-segment Biot-Savart velocity.");
    m.def("build_info", &build_info);
}
