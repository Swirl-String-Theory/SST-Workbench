#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
py::dict curve_basic_stats(py::array_t<double,py::array::c_style|py::array::forcecast> a){
 auto x=a.unchecked<2>(); const py::ssize_t n=x.shape(0); double L=0.0;
 #pragma omp parallel for reduction(+:L) if(n>512)
 for(py::ssize_t i=0;i<n;i++){py::ssize_t j=(i+1)%n;double s=0;for(int k=0;k<3;k++){double d=x(j,k)-x(i,k);s+=d*d;}L+=std::sqrt(s);} py::dict d;d["length"]=L;d["n_points"]=n;return d;}
PYBIND11_MODULE(_native,m){m.doc()="SST finite-core helper kernels";m.def("curve_basic_stats",&curve_basic_stats);}
