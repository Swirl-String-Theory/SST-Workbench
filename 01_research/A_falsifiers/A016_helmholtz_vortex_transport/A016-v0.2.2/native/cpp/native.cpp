#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
namespace {
constexpr double PI = 3.141592653589793238462643383279502884;
std::string backend_name() {
#ifdef _OPENMP
    return "openmp";
#else
    return "serial";
#endif
}
}

py::array_t<double> biot_savart(
    py::array_t<double, py::array::c_style | py::array::forcecast> points,
    py::array_t<double, py::array::c_style | py::array::forcecast> queries,
    double gamma,
    double core) {

    if (!(std::isfinite(gamma) && std::isfinite(core)) || core <= 0.0)
        throw std::runtime_error("gamma/core invalid; core must be >0");

    auto bp = points.request();
    auto bq = queries.request();
    if (bp.ndim != 2 || bp.shape[1] != 3 || bq.ndim != 2 || bq.shape[1] != 3)
        throw std::runtime_error("points/queries must be Nx3");

    const py::ssize_t n = bp.shape[0];
    const py::ssize_t m = bq.shape[0];
    if (n < 3) throw std::runtime_error("need >=3 closed filament points");

    const double* p = static_cast<const double*>(bp.ptr);
    const double* q = static_cast<const double*>(bq.ptr);
    py::array_t<double> out({m, py::ssize_t(3)});
    auto bo = out.request();
    double* v = static_cast<double*>(bo.ptr);

    const double scale = gamma / (4.0 * PI);
    const double a2 = core * core;

    {
        py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if(m > 64)
#endif
        for (long long j = 0; j < static_cast<long long>(m); ++j) {
            double vx = 0.0, vy = 0.0, vz = 0.0;
            const double* x = q + 3 * j;
            for (py::ssize_t s = 0; s < n; ++s) {
                const py::ssize_t t = (s + 1) % n;
                const double* a = p + 3 * s;
                const double* b = p + 3 * t;
                const double dlx = b[0] - a[0];
                const double dly = b[1] - a[1];
                const double dlz = b[2] - a[2];
                const double mx = 0.5 * (a[0] + b[0]);
                const double my = 0.5 * (a[1] + b[1]);
                const double mz = 0.5 * (a[2] + b[2]);
                const double rx = x[0] - mx;
                const double ry = x[1] - my;
                const double rz = x[2] - mz;
                const double D = rx * rx + ry * ry + rz * rz + a2;
                const double inv3 = 1.0 / (D * std::sqrt(D));
                vx += scale * (dly * rz - dlz * ry) * inv3;
                vy += scale * (dlz * rx - dlx * rz) * inv3;
                vz += scale * (dlx * ry - dly * rx) * inv3;
            }
            v[3 * j] = vx;
            v[3 * j + 1] = vy;
            v[3 * j + 2] = vz;
        }
    }
    return out;
}

py::dict backend_info() {
    py::dict d;
    d["backend"] = backend_name();
    d["precision"] = "float64";
#ifdef _OPENMP
    d["openmp_compiled"] = true;
    d["openmp_max_threads"] = omp_get_max_threads();
#else
    d["openmp_compiled"] = false;
    d["openmp_max_threads"] = 1;
#endif
    return d;
}

PYBIND11_MODULE(_sst_native, m) {
    m.doc() = "A016 v0.2.2 instance-local C++17/OpenMP Biot-Savart certification kernel";
    m.def("biot_savart", &biot_savart,
          py::arg("points"), py::arg("queries"), py::arg("gamma") = 1.0, py::arg("core") = 0.04);
    m.def("backend_info", &backend_info);
}
