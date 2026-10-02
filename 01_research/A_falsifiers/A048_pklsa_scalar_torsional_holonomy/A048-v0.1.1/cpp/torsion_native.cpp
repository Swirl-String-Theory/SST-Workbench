#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
namespace py=pybind11;

py::array_t<double> kelvin_omega(py::array_t<double,py::array::c_style|py::array::forcecast> k,double beta){
    auto x=k.unchecked<1>(); py::array_t<double> out(x.shape(0)); auto y=out.mutable_unchecked<1>();
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for(py::ssize_t i=0;i<x.shape(0);++i) y(i)=beta*x(i)*x(i);
    return out;
}
py::array_t<double> torsion_omega(py::array_t<double,py::array::c_style|py::array::forcecast> k,double c,double gap){
    auto x=k.unchecked<1>(); py::array_t<double> out(x.shape(0)); auto y=out.mutable_unchecked<1>();
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for(py::ssize_t i=0;i<x.shape(0);++i) y(i)=std::sqrt((c*x(i))*(c*x(i))+gap*gap);
    return out;
}
double loglog_slope(py::array_t<double,py::array::c_style|py::array::forcecast> k,py::array_t<double,py::array::c_style|py::array::forcecast> w){
    auto x=k.unchecked<1>(); auto y=w.unchecked<1>(); if(x.shape(0)!=y.shape(0)||x.shape(0)<2) throw std::runtime_error("shape mismatch");
    double sx=0,sy=0,sxx=0,sxy=0; auto n=x.shape(0);
    for(py::ssize_t i=0;i<n;++i){ if(x(i)<=0||y(i)<=0) throw std::runtime_error("positive inputs required"); double a=std::log(x(i)),b=std::log(y(i)); sx+=a;sy+=b;sxx+=a*a;sxy+=a*b; }
    return (n*sxy-sx*sy)/(n*sxx-sx*sx);
}
PYBIND11_MODULE(torsion_native,m){m.def("kelvin_omega",&kelvin_omega);m.def("torsion_omega",&torsion_omega);m.def("loglog_slope",&loglog_slope);}
