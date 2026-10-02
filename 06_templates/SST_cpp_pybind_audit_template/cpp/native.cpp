#include <pybind11/pybind11.h>

namespace py = pybind11;

double add(double a, double b) { return a + b; }

PYBIND11_MODULE(_native, m) {
    m.doc() = "Minimal pybind11 extension (replace with your kernel).";
    m.def("add", &add, "Example: a + b");
}
