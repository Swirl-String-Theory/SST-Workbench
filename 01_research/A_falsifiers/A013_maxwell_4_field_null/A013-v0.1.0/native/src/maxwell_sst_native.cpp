#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
namespace py=pybind11;
struct V{double x,y,z;};
static V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static V add(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static V mul(V a,double s){return {a.x*s,a.y*s,a.z*s};}
static V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static V get(const py::detail::unchecked_reference<double,2>& a, ssize_t i){return {a(i,0),a(i,1),a(i,2)};}
py::array_t<double> bs(py::array_t<double> pts, py::array_t<double> curve,double gamma,double core){
 auto P=pts.unchecked<2>(); auto C=curve.unchecked<2>(); ssize_t M=P.shape(0),N=C.shape(0); py::array_t<double> out({M,(ssize_t)3}); auto O=out.mutable_unchecked<2>(); double fac=gamma/(4*M_PI),a2=core*core;
 for(ssize_t i=0;i<M;i++){V x=get(P,i),sum{0,0,0}; for(ssize_t j=0;j<N;j++){V p=get(C,j),q=get(C,(j+1)%N),dl=sub(q,p),m=mul(add(p,q),0.5),r=sub(x,m),cr=cross(dl,r); double d=std::pow(dot(r,r)+a2,1.5); if(d>0) sum=add(sum,mul(cr,1.0/d));} O(i,0)=fac*sum.x;O(i,1)=fac*sum.y;O(i,2)=fac*sum.z;} return out;}
double lk(py::array_t<double> c1,py::array_t<double> c2){auto A=c1.unchecked<2>();auto B=c2.unchecked<2>();ssize_t N=A.shape(0),M=B.shape(0);double s=0;for(ssize_t i=0;i<N;i++){V a=get(A,i),a2=get(A,(i+1)%N),da=sub(a2,a),ma=mul(add(a,a2),0.5);for(ssize_t j=0;j<M;j++){V b=get(B,j),b2=get(B,(j+1)%M),db=sub(b2,b),mb=mul(add(b,b2),0.5),r=sub(ma,mb);double rr=dot(r,r);if(rr<1e-30)continue;s+=dot(cross(da,db),r)/std::pow(rr,1.5);}}return s/(4*M_PI);}
double energy(py::array_t<double> c,double gamma,double rho,double core){auto C=c.unchecked<2>();ssize_t N=C.shape(0);double s=0;for(ssize_t i=0;i<N;i++){V p=get(C,i),q=get(C,(i+1)%N),di=sub(q,p),mi=mul(add(p,q),0.5);for(ssize_t j=0;j<N;j++){V a=get(C,j),b=get(C,(j+1)%N),dj=sub(b,a),mj=mul(add(a,b),0.5),r=sub(mi,mj);s+=dot(di,dj)/std::sqrt(dot(r,r)+core*core);}}return rho*gamma*gamma/(8*M_PI)*s;}
PYBIND11_MODULE(maxwell_sst_native,m){m.def("biot_savart_points",&bs);m.def("gauss_linking",&lk);m.def("regularized_energy",&energy);}
