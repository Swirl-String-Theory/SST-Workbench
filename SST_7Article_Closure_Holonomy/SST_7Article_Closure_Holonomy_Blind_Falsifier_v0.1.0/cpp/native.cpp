#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;

double curve_length(py::array_t<double,py::array::c_style|py::array::forcecast> a){
    auto b=a.unchecked<2>(); if(b.shape(1)!=3||b.shape(0)<2) throw std::runtime_error("Nx3 required");
    const ssize_t n=b.shape(0); double s=0.0;
    #pragma omp parallel for reduction(+:s) if(n>2000)
    for(ssize_t i=0;i<n;i++){
        ssize_t j=(i+1)%n; double dx=b(j,0)-b(i,0),dy=b(j,1)-b(i,1),dz=b(j,2)-b(i,2);
        s+=std::sqrt(dx*dx+dy*dy+dz*dz);
    } return s;
}

double gauss_linking(py::array_t<double,py::array::c_style|py::array::forcecast> aa,
                     py::array_t<double,py::array::c_style|py::array::forcecast> bb){
    auto a=aa.unchecked<2>(); auto b=bb.unchecked<2>();
    if(a.shape(1)!=3||b.shape(1)!=3) throw std::runtime_error("Nx3 required");
    const ssize_t na=a.shape(0), nb=b.shape(0); double sum=0.0;
    #pragma omp parallel for reduction(+:sum) schedule(static) if(na*nb>100000)
    for(ssize_t i=0;i<na;i++){
        ssize_t i2=(i+1)%na;
        double dax=a(i2,0)-a(i,0), day=a(i2,1)-a(i,1), daz=a(i2,2)-a(i,2);
        double maxa=0.5*(a(i2,0)+a(i,0)), maya=0.5*(a(i2,1)+a(i,1)), maza=0.5*(a(i2,2)+a(i,2));
        for(ssize_t j=0;j<nb;j++){
            ssize_t j2=(j+1)%nb;
            double dbx=b(j2,0)-b(j,0), dby=b(j2,1)-b(j,1), dbz=b(j2,2)-b(j,2);
            double rx=maxa-0.5*(b(j2,0)+b(j,0)), ry=maya-0.5*(b(j2,1)+b(j,1)), rz=maza-0.5*(b(j2,2)+b(j,2));
            double cx=day*dbz-daz*dby, cy=daz*dbx-dax*dbz, cz=dax*dby-day*dbx;
            double r2=rx*rx+ry*ry+rz*rz; if(r2<1e-30) continue;
            sum+=(rx*cx+ry*cy+rz*cz)/(r2*std::sqrt(r2));
        }
    }
    constexpr double pi=3.141592653589793238462643383279502884;
    return sum/(4.0*pi);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST7 C++17 native kernels";
    m.def("curve_length",&curve_length);
    m.def("gauss_linking",&gauss_linking);
#ifdef _OPENMP
    m.attr("openmp")=true;
#else
    m.attr("openmp")=false;
#endif
}
