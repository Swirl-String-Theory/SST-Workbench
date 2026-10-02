#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <stdexcept>

namespace py = pybind11;
using index_t = py::ssize_t;

py::tuple decompose_gradient(
    py::array_t<double, py::array::c_style | py::array::forcecast> grad
) {
    auto g = grad.unchecked<3>();
    if (g.shape(1) != 3 || g.shape(2) != 3) {
        throw std::runtime_error("grad must have shape (N,3,3)");
    }
    const index_t N = g.shape(0);

    py::array_t<double> strain(
        py::array::ShapeContainer{N, index_t{3}, index_t{3}}
    );
    py::array_t<double> omega(
        py::array::ShapeContainer{N, index_t{3}}
    );
    py::array_t<double> div(
        py::array::ShapeContainer{N}
    );

    auto S = strain.mutable_unchecked<3>();
    auto W = omega.mutable_unchecked<2>();
    auto D = div.mutable_unchecked<1>();

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (index_t n = 0; n < N; ++n) {
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 3; ++j) {
                S(n, i, j) = 0.5 * (g(n, i, j) + g(n, j, i));
            }
        }
        W(n, 0) = g(n, 2, 1) - g(n, 1, 2);
        W(n, 1) = g(n, 0, 2) - g(n, 2, 0);
        W(n, 2) = g(n, 1, 0) - g(n, 0, 1);
        D(n) = g(n, 0, 0) + g(n, 1, 1) + g(n, 2, 2);
    }
    return py::make_tuple(strain, omega, div);
}

py::array_t<double> invariants(
    py::array_t<double, py::array::c_style | py::array::forcecast> u,
    py::array_t<double, py::array::c_style | py::array::forcecast> omega,
    py::array_t<double, py::array::c_style | py::array::forcecast> strain
) {
    auto U = u.unchecked<2>();
    auto W = omega.unchecked<2>();
    auto S = strain.unchecked<3>();

    if (U.shape(1) != 3 || W.shape(1) != 3 ||
        S.shape(1) != 3 || S.shape(2) != 3 ||
        U.shape(0) != W.shape(0) || U.shape(0) != S.shape(0)) {
        throw std::runtime_error("shape mismatch");
    }

    const index_t N = U.shape(0);
    py::array_t<double> out(
        py::array::ShapeContainer{N, index_t{4}}
    );
    auto O = out.mutable_unchecked<2>();

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (index_t n = 0; n < N; ++n) {
        double u2 = 0.0;
        double w2 = 0.0;
        double s2 = 0.0;
        double h = 0.0;

        for (int i = 0; i < 3; ++i) {
            u2 += U(n, i) * U(n, i);
            w2 += W(n, i) * W(n, i);
            h += U(n, i) * W(n, i);
            for (int j = 0; j < 3; ++j) {
                s2 += S(n, i, j) * S(n, i, j);
            }
        }
        O(n, 0) = u2;
        O(n, 1) = w2;
        O(n, 2) = s2;
        O(n, 3) = h;
    }
    return out;
}

PYBIND11_MODULE(triadic_native, m) {
    m.doc() = "C++17/OpenMP pointwise kernels for A046 v0.2.0";
    m.def("decompose_gradient", &decompose_gradient);
    m.def("invariants", &invariants);
}
