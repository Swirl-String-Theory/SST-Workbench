#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "kernels.hpp"
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
using sstknot::V3;
static std::vector<V3> read_pts(py::array_t<double,py::array::c_style|py::array::forcecast> a){
    auto b=a.request();if(b.ndim!=2||b.shape[1]!=3)throw std::runtime_error("points must be Nx3");
    const double* p=(const double*)b.ptr;std::vector<V3> out((size_t)b.shape[0]);
    for(ssize_t i=0;i<b.shape[0];++i)out[(size_t)i]={p[3*i],p[3*i+1],p[3*i+2]};return out;
}
static double py_min(py::array_t<double,py::array::c_style|py::array::forcecast> a,int skip){return sstknot::min_nonlocal_distance(read_pts(a),skip);}
static double py_wr(py::array_t<double,py::array::c_style|py::array::forcecast> a){return sstknot::writhe_midpoint(read_pts(a));}
static double py_lk(py::array_t<double,py::array::c_style|py::array::forcecast> a,py::array_t<double,py::array::c_style|py::array::forcecast> b){return sstknot::linking_midpoint(read_pts(a),read_pts(b));}
PYBIND11_MODULE(_sstknot_native,m){
    m.doc()="Native geometry kernels for SST Knot Geometry Library";
    m.def("min_nonlocal_distance",&py_min,py::arg("points"),py::arg("skip")=8);
    m.def("writhe_midpoint",&py_wr);m.def("linking_midpoint",&py_lk);
#ifdef _OPENMP
    m.attr("openmp_enabled")=true;
#else
    m.attr("openmp_enabled")=false;
#endif
}
