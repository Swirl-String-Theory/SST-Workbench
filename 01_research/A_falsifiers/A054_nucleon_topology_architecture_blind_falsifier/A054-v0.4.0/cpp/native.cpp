#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
using Arr=py::array_t<double,py::array::c_style|py::array::forcecast>;

Arr elastic_raw(const Arr& a){ auto x=a.unchecked<2>(); ssize_t n=x.shape(0); Arr out({n,(ssize_t)3}); auto o=out.mutable_unchecked<2>();
 std::vector<double> lap(n*3), bi(n*3),t(n*3); double ds=0; for(ssize_t i=0;i<n;i++){ssize_t ip=(i+1)%n; double s=0;for(int k=0;k<3;k++){double d=x(ip,k)-x(i,k);s+=d*d;}ds+=std::sqrt(s);} ds=std::max(ds/n,1e-12);
 for(ssize_t i=0;i<n;i++){ssize_t im=(i+n-1)%n,ip=(i+1)%n;for(int k=0;k<3;k++){lap[3*i+k]=(x(ip,k)-2*x(i,k)+x(im,k))/(ds*ds);t[3*i+k]=x(ip,k)-x(im,k);} double nn=std::sqrt(t[3*i]*t[3*i]+t[3*i+1]*t[3*i+1]+t[3*i+2]*t[3*i+2]);for(int k=0;k<3;k++)t[3*i+k]/=std::max(nn,1e-15);}
 for(ssize_t i=0;i<n;i++){ssize_t im=(i+n-1)%n,ip=(i+1)%n;for(int k=0;k<3;k++)bi[3*i+k]=-(lap[3*ip+k]-2*lap[3*i+k]+lap[3*im+k])/(ds*ds); double tx=t[3*i],ty=t[3*i+1],tz=t[3*i+2],fx=bi[3*i],fy=bi[3*i+1],fz=bi[3*i+2]; o(i,0)=ty*fz-tz*fy;o(i,1)=tz*fx-tx*fz;o(i,2)=tx*fy-ty*fx; }
 return out; }

Arr core_force(const Arr& a,const std::vector<Arr>& others,double core,double sr_mult,double sa_mult,double chi){auto x=a.unchecked<2>();ssize_t n=x.shape(0);Arr out({n,(ssize_t)3});auto o=out.mutable_unchecked<2>();double sr=std::max(sr_mult*core,1e-9),sa=std::max(sa_mult*core,1e-9);
 #pragma omp parallel for if(n>32)
 for(ssize_t i=0;i<n;i++){double F[3]={0,0,0};for(auto &ar:others){auto y=ar.unchecked<2>();ssize_t m=y.shape(0);for(ssize_t j=0;j<m;j++){double d0=x(i,0)-y(j,0),d1=x(i,1)-y(j,1),d2=x(i,2)-y(j,2);double r2=d0*d0+d1*d1+d2*d2;double w=std::exp(-r2/(2*sr*sr))/(sr*sr)-chi*std::exp(-r2/(2*sa*sa))/(sa*sa);F[0]+=w*d0/m;F[1]+=w*d1/m;F[2]+=w*d2/m;}}o(i,0)=F[0];o(i,1)=F[1];o(i,2)=F[2];}return out;}
PYBIND11_MODULE(_native,m){m.def("openmp_enabled",[](){
#ifdef _OPENMP
return true;
#else
return false;
#endif
});m.def("elastic_raw",&elastic_raw);m.def("core_force",&core_force);}
