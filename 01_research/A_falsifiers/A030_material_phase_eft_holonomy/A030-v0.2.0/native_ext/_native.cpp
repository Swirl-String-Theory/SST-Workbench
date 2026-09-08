#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>

namespace py = pybind11;

py::array_t<double> biot_savart_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> x,
    double gamma_star,
    double core_radius_star
) {
    auto b = x.request();
    if (b.ndim != 2 || b.shape[1] != 3) {
        throw std::runtime_error("x must be Nx3");
    }

    // Py_ssize_t is provided by Python.h and is portable on MSVC.
    // Use Python's signed size type for ABI portability.
    const Py_ssize_t n = static_cast<Py_ssize_t>(b.shape[0]);
    py::array_t<double> out({n, static_cast<Py_ssize_t>(3)});
    auto bo = out.request();

    const double* p = static_cast<const double*>(b.ptr);
    double* v = static_cast<double*>(bo.ptr);
    constexpr double PI = 3.141592653589793238462643383279502884;
    const double coeff = gamma_star / (4.0 * PI);
    const double a2 = core_radius_star * core_radius_star;

    {
        py::gil_scoped_release release;
#ifdef _OPENMP
#pragma omp parallel for
#endif
        for (Py_ssize_t i = 0; i < n; ++i) {
            double vx = 0.0, vy = 0.0, vz = 0.0;
            const double xi = p[3*i];
            const double yi = p[3*i + 1];
            const double zi = p[3*i + 2];

            for (Py_ssize_t j = 0; j < n; ++j) {
                const Py_ssize_t j2 = (j + 1) % n;
                const double dlx = p[3*j2]     - p[3*j];
                const double dly = p[3*j2 + 1] - p[3*j + 1];
                const double dlz = p[3*j2 + 2] - p[3*j + 2];

                const double mx = 0.5 * (p[3*j2]     + p[3*j]);
                const double my = 0.5 * (p[3*j2 + 1] + p[3*j + 1]);
                const double mz = 0.5 * (p[3*j2 + 2] + p[3*j + 2]);

                const double rx = xi - mx;
                const double ry = yi - my;
                const double rz = zi - mz;
                const double d2 = rx*rx + ry*ry + rz*rz + a2;
                const double den = std::pow(d2, 1.5);

                vx += (dly*rz - dlz*ry) / den;
                vy += (dlz*rx - dlx*rz) / den;
                vz += (dlx*ry - dly*rx) / den;
            }

            v[3*i]     = coeff * vx;
            v[3*i + 1] = coeff * vy;
            v[3*i + 2] = coeff * vz;
        }
    }
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Native regularized Biot-Savart kernel for SST Material/Phase EFT Falsifier";
    m.def(
        "biot_savart_velocity",
        &biot_savart_velocity,
        py::arg("x"),
        py::arg("gamma_star"),
        py::arg("core_radius_star")
    );
}
