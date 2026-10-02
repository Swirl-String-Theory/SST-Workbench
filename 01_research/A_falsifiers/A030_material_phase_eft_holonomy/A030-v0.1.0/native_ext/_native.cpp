#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
namespace py=pybind11;
py::array_t<double> biot_savart_velocity(py::array_t<double,py::array::c_style|py::array::forcecast> x,double gamma_star,double core_radius_star){
 auto b=x.request(); if(b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("x must be Nx3"); ssize_t n=b.shape[0]; auto out=py::array_t<double>({n,(ssize_t)3}); auto bo=out.request(); const double* p=(const double*)b.ptr; double* v=(double*)bo.ptr; double coeff=gamma_star/(4.0*3.14159265358979323846),a2=core_radius_star*core_radius_star;
 #pragma omp parallel for
 for(ssize_t i=0;i<n;++i){double vx=0,vy=0,vz=0,xi=p[3*i],yi=p[3*i+1],zi=p[3*i+2]; for(ssize_t j=0;j<n;++j){ssize_t j2=(j+1)%n; double dlx=p[3*j2]-p[3*j],dly=p[3*j2+1]-p[3*j+1],dlz=p[3*j2+2]-p[3*j+2]; double mx=.5*(p[3*j2]+p[3*j]),my=.5*(p[3*j2+1]+p[3*j+1]),mz=.5*(p[3*j2+2]+p[3*j+2]); double rx=xi-mx,ry=yi-my,rz=zi-mz,d2=rx*rx+ry*ry+rz*rz+a2,den=std::pow(d2,1.5); vx+=(dly*rz-dlz*ry)/den; vy+=(dlz*rx-dlx*rz)/den; vz+=(dlx*ry-dly*rx)/den;} v[3*i]=coeff*vx; v[3*i+1]=coeff*vy; v[3*i+2]=coeff*vz;} return out;}
PYBIND11_MODULE(_native,m){m.def("biot_savart_velocity",&biot_savart_velocity);}
