#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
namespace py=pybind11;
py::dict metrics(py::array_t<double,py::array::c_style|py::array::forcecast> a){
 auto b=a.request(); if(b.ndim!=2||b.shape[1]!=3||b.shape[0]<4) throw std::runtime_error("Nx3 array required");
 auto *x=(double*)b.ptr; const py::ssize_t n=b.shape[0];
 double cx=0,cy=0,cz=0; for(py::ssize_t i=0;i<n;i++){cx+=x[3*i];cy+=x[3*i+1];cz+=x[3*i+2];} cx/=n;cy/=n;cz/=n;
 double rg2=0,L=0,sum=0,sum2=0;
 for(py::ssize_t i=0;i<n;i++){double dx=x[3*i]-cx,dy=x[3*i+1]-cy,dz=x[3*i+2]-cz;rg2+=dx*dx+dy*dy+dz*dz; py::ssize_t j=(i+1)%n; double ex=x[3*j]-x[3*i],ey=x[3*j+1]-x[3*i+1],ez=x[3*j+2]-x[3*i+2]; double e=std::sqrt(ex*ex+ey*ey+ez*ez);L+=e;sum+=e;sum2+=e*e;}
 double mean=sum/n,var=std::max(0.0,sum2/n-mean*mean),cv=mean>0?std::sqrt(var)/mean:INFINITY;
 py::dict d; d["length"]=L; d["rg"]=std::sqrt(rg2/n); d["edge_cv"]=cv; return d;
}
PYBIND11_MODULE(kpmetrics_native,m){m.def("metrics",&metrics);}
