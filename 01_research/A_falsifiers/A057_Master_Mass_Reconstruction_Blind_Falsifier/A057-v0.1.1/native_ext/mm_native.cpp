#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <stdexcept>
#include "energy_core.hpp"
namespace py = pybind11;

using ArrayF64C = py::array_t<double, py::array::c_style | py::array::forcecast>;

std::vector<std::vector<double>> py_energy_matrix(const py::list& comps, double core) {
    std::vector<std::vector<a057::Point>> cc;
    cc.reserve(static_cast<std::size_t>(py::len(comps)));

    for (py::handle obj : comps) {
        // pybind11 3.x no longer accepts the old direct array_t(handle) construction
        // used by A057-v0.1.0.  ensure() performs the requested force-cast safely.
        ArrayF64C a = ArrayF64C::ensure(obj);
        if (!a) {
            throw py::type_error("component must be convertible to a C-contiguous float64 NumPy array");
        }
        if (a.ndim() != 2 || a.shape(1) != 3 || a.shape(0) < 4) {
            throw py::value_error("component must be Nx3 with N>=4");
        }

        auto u = a.unchecked<2>();
        const py::ssize_t n = u.shape(0);
        std::vector<a057::Point> pts(static_cast<std::size_t>(n));
        for (py::ssize_t i = 0; i < n; ++i) {
            pts[static_cast<std::size_t>(i)] = {u(i,0), u(i,1), u(i,2)};
        }
        cc.push_back(std::move(pts));
    }
    return a057::energy_matrix(cc, core);
}

PYBIND11_MODULE(mm_native, m) {
    m.doc() = "A057 FP64 regularized filament-energy certification kernel";
    m.def("energy_matrix", &py_energy_matrix,
          py::arg("components"), py::arg("core") = 1.0);
}
