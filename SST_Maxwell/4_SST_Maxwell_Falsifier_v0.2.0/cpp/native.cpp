#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
constexpr double PI=3.141592653589793238462643383279502884;
struct V{double x,y,z;};
static inline V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static inline V add(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static inline V mul(V a,double s){return {a.x*s,a.y*s,a.z*s};}
static inline V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static inline double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
template<class A> static inline V get(const A& a, ssize_t i){return {a(i,0),a(i,1),a(i,2)};}

py::array_t<double> bs(py::array_t<double,py::array::c_style|py::array::forcecast> pts,
                       py::array_t<double,py::array::c_style|py::array::forcecast> curve,
                       double gamma,double core){
  auto P=pts.unchecked<2>(); auto C=curve.unchecked<2>();
  ssize_t M=P.shape(0),N=C.shape(0); py::array_t<double> out({M,(ssize_t)3}); auto O=out.mutable_unchecked<2>();
  double fac=gamma/(4*PI),a2=core*core;
  py::gil_scoped_release release;
  #pragma omp parallel for schedule(static) if(M>8)
  for(ssize_t i=0;i<M;i++){
    V x=get(P,i),sum{0,0,0};
    for(ssize_t j=0;j<N;j++){
      V p=get(C,j),q=get(C,(j+1)%N),dl=sub(q,p),m=mul(add(p,q),0.5),r=sub(x,m),cr=cross(dl,r);
      double rr=dot(r,r)+a2; if(rr>0) sum=add(sum,mul(cr,1.0/(rr*std::sqrt(rr))));
    }
    O(i,0)=fac*sum.x; O(i,1)=fac*sum.y; O(i,2)=fac*sum.z;
  }
  return out;
}

double lk(py::array_t<double,py::array::c_style|py::array::forcecast> c1,
          py::array_t<double,py::array::c_style|py::array::forcecast> c2){
  auto A=c1.unchecked<2>();auto B=c2.unchecked<2>();ssize_t N=A.shape(0),M=B.shape(0);double s=0;
  py::gil_scoped_release release;
  #pragma omp parallel for reduction(+:s) schedule(static) if(N>32)
  for(ssize_t i=0;i<N;i++){
    V a=get(A,i),a2=get(A,(i+1)%N),da=sub(a2,a),ma=mul(add(a,a2),0.5); double local=0;
    for(ssize_t j=0;j<M;j++){
      V b=get(B,j),b2=get(B,(j+1)%M),db=sub(b2,b),mb=mul(add(b,b2),0.5),r=sub(ma,mb); double rr=dot(r,r);
      if(rr<1e-30) continue; local += dot(cross(da,db),r)/(rr*std::sqrt(rr));
    } s += local;
  } return s/(4*PI);
}

double energy(py::array_t<double,py::array::c_style|py::array::forcecast> c,double gamma,double rho,double core){
  auto C=c.unchecked<2>(); ssize_t N=C.shape(0); double s=0; double a2=core*core;
  py::gil_scoped_release release;
  #pragma omp parallel for reduction(+:s) schedule(static) if(N>32)
  for(ssize_t i=0;i<N;i++){
    V p=get(C,i),q=get(C,(i+1)%N),di=sub(q,p),mi=mul(add(p,q),0.5); double local=0;
    for(ssize_t j=0;j<N;j++){
      V a=get(C,j),b=get(C,(j+1)%N),dj=sub(b,a),mj=mul(add(a,b),0.5),r=sub(mi,mj);
      local += dot(di,dj)/std::sqrt(dot(r,r)+a2);
    } s += local;
  } return rho*gamma*gamma/(8*PI)*s;
}

double writhe(py::array_t<double,py::array::c_style|py::array::forcecast> c,int exclude_near){
  auto C=c.unchecked<2>(); ssize_t N=C.shape(0); double s=0;
  py::gil_scoped_release release;
  #pragma omp parallel for reduction(+:s) schedule(static) if(N>32)
  for(ssize_t i=0;i<N;i++){
    V a=get(C,i),a2=get(C,(i+1)%N),da=sub(a2,a),ma=mul(add(a,a2),0.5); double local=0;
    for(ssize_t j=0;j<N;j++){
      ssize_t d=std::llabs((long long)i-(long long)j); d=std::min(d,N-d); if(d<=exclude_near) continue;
      V b=get(C,j),b2=get(C,(j+1)%N),db=sub(b2,b),mb=mul(add(b,b2),0.5),r=sub(ma,mb); double rr=dot(r,r);
      if(rr<1e-30) continue; local += dot(cross(da,db),r)/(rr*std::sqrt(rr));
    } s+=local;
  } return s/(4*PI);
}

void set_threads(int n){
  #ifdef _OPENMP
  omp_set_num_threads(std::max(1,n));
  #else
  (void)n;
  #endif
}
py::dict info(){
  py::dict d; d["backend"]="cpp"; d["native"]=true;
  #ifdef _OPENMP
  d["openmp"]=true; d["threads"]=omp_get_max_threads();
  #else
  d["openmp"]=false; d["threads"]=1;
  #endif
  return d;
}
PYBIND11_MODULE(_native,m){
  m.doc()="4_SST Maxwell v0.2.0 high-throughput pybind11 kernels";
  m.def("biot_savart_points",&bs); m.def("gauss_linking",&lk); m.def("regularized_energy",&energy); m.def("writhe_midpoint",&writhe);
  m.def("set_num_threads",&set_threads); m.def("backend_info",&info);
}
