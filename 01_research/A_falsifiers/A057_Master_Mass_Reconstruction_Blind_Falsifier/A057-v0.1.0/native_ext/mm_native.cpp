#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "energy_core.hpp"
namespace py=pybind11;

std::vector<std::vector<double>> py_energy_matrix(py::list comps,double core){
    std::vector<std::vector<a057::Point>> cc;
    for(auto obj:comps){
        auto a=py::array_t<double,py::array::c_style|py::array::forcecast>(obj);
        auto u=a.unchecked<2>();
        if (u.shape(1)!=3 || u.shape(0)<4) throw std::runtime_error("component must be Nx3 with N>=4");
        std::vector<a057::Point> pts(static_cast<std::size_t>(u.shape(0)));
        for(ssize_t i=0;i<u.shape(0);++i) pts[static_cast<std::size_t>(i)]={u(i,0),u(i,1),u(i,2)};
        cc.push_back(std::move(pts));
    }
    return a057::energy_matrix(cc,core);
}
PYBIND11_MODULE(mm_native,m){
    m.doc()="A057 FP64 regularized filament-energy certification kernel";
    m.def("energy_matrix",&py_energy_matrix,py::arg("components"),py::arg("core")=1.0);
}
