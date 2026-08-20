#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(_sycl_import_probe, m)
{
    m.def("hello", []() {
        return "ok";
    });
}