#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <cmath>
#include <cstddef>
#include <stdexcept>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using index_t = std::ptrdiff_t;

// NOTE (v0.1.1): do not use POSIX ssize_t here.  MSVC does not define it.
// std::ptrdiff_t is a standard signed integral type and is accepted by MSVC
// OpenMP canonical for-loops while safely representing pybind11 array indices.

double curve_length(
    py::array_t<double, py::array::c_style | py::array::forcecast> a) {
    auto b = a.unchecked<2>();
    if (b.shape(1) != 3 || b.shape(0) < 2) {
        throw std::runtime_error("Nx3 required");
    }

    const index_t n = static_cast<index_t>(b.shape(0));
    double s = 0.0;

#pragma omp parallel for reduction(+ : s) if (n > 2000)
    for (index_t i = 0; i < n; ++i) {
        const index_t j = (i + 1) % n;
        const double dx = b(j, 0) - b(i, 0);
        const double dy = b(j, 1) - b(i, 1);
        const double dz = b(j, 2) - b(i, 2);
        s += std::sqrt(dx * dx + dy * dy + dz * dz);
    }
    return s;
}

double gauss_linking(
    py::array_t<double, py::array::c_style | py::array::forcecast> aa,
    py::array_t<double, py::array::c_style | py::array::forcecast> bb) {
    auto a = aa.unchecked<2>();
    auto b = bb.unchecked<2>();
    if (a.shape(1) != 3 || b.shape(1) != 3 || a.shape(0) < 2 || b.shape(0) < 2) {
        throw std::runtime_error("Nx3 arrays with at least two points required");
    }

    const index_t na = static_cast<index_t>(a.shape(0));
    const index_t nb = static_cast<index_t>(b.shape(0));
    double sum = 0.0;

#pragma omp parallel for reduction(+ : sum) schedule(static) if (na > 0 && nb > 100000 / na)
    for (index_t i = 0; i < na; ++i) {
        const index_t i2 = (i + 1) % na;
        const double dax = a(i2, 0) - a(i, 0);
        const double day = a(i2, 1) - a(i, 1);
        const double daz = a(i2, 2) - a(i, 2);
        const double maxa = 0.5 * (a(i2, 0) + a(i, 0));
        const double maya = 0.5 * (a(i2, 1) + a(i, 1));
        const double maza = 0.5 * (a(i2, 2) + a(i, 2));

        for (index_t j = 0; j < nb; ++j) {
            const index_t j2 = (j + 1) % nb;
            const double dbx = b(j2, 0) - b(j, 0);
            const double dby = b(j2, 1) - b(j, 1);
            const double dbz = b(j2, 2) - b(j, 2);

            const double rx = maxa - 0.5 * (b(j2, 0) + b(j, 0));
            const double ry = maya - 0.5 * (b(j2, 1) + b(j, 1));
            const double rz = maza - 0.5 * (b(j2, 2) + b(j, 2));

            const double cx = day * dbz - daz * dby;
            const double cy = daz * dbx - dax * dbz;
            const double cz = dax * dby - day * dbx;
            const double r2 = rx * rx + ry * ry + rz * rz;
            if (r2 < 1e-30) {
                continue;
            }
            sum += (rx * cx + ry * cy + rz * cz) / (r2 * std::sqrt(r2));
        }
    }

    constexpr double pi = 3.141592653589793238462643383279502884;
    return sum / (4.0 * pi);
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "SST7 C++17 native kernels";
    m.def("curve_length", &curve_length);
    m.def("gauss_linking", &gauss_linking);
#ifdef _OPENMP
    m.attr("openmp") = true;
#else
    m.attr("openmp") = false;
#endif
}
