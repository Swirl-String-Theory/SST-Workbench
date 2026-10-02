#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
py::array_t<double> softened_velocity(py::array_t<double,py::array::c_style|py::array::forcecast> targets,
                                      py::array_t<double,py::array::c_style|py::array::forcecast> mids,
                                      py::array_t<double,py::array::c_style|py::array::forcecast> dls,
                                      double gamma,double core){
 auto T=targets.unchecked<2>(), M=mids.unchecked<2>(), D=dls.unchecked<2>();
 if(T.shape(1)!=3||M.shape(1)!=3||D.shape(1)!=3||M.shape(0)!=D.shape(0)) throw std::runtime_error("shape");
 py::array_t<double> out({T.shape(0),3}); auto O=out.mutable_unchecked<2>();
 const double fac=gamma/(4.0*M_PI), a2=core*core;
 #pragma omp parallel for if(T.shape(0)>32)
 for(py::ssize_t i=0;i<T.shape(0);++i){double vx=0,vy=0,vz=0;
   for(py::ssize_t j=0;j<M.shape(0);++j){
    double x=T(i,0)-M(j,0), y=T(i,1)-M(j,1), z=T(i,2)-M(j,2);
    double den=std::pow(x*x+y*y+z*z+a2,1.5);
    double dx=D(j,0),dy=D(j,1),dz=D(j,2);
    vx+=(dy*z-dz*y)/den; vy+=(dz*x-dx*z)/den; vz+=(dx*y-dy*x)/den;
   }
   O(i,0)=fac*vx;O(i,1)=fac*vy;O(i,2)=fac*vz;
 }
 return out;
}
PYBIND11_MODULE(_sst_falsifier_native,m){m.def("softened_velocity",&softened_velocity);}
