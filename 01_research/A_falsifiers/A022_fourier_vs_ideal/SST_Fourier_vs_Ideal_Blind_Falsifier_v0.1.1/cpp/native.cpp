#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include <cstdlib>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
constexpr double PI=3.1415926535897932384626433832795;
struct V3{double x,y,z;};
inline V3 add(V3 a,V3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline V3 sub(V3 a,V3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline V3 mul(V3 a,double s){return {a.x*s,a.y*s,a.z*s};}
inline double dot(V3 a,V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline double norm(V3 a){return std::sqrt(dot(a,a));}
inline V3 cross(V3 a,V3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
struct Seg{int comp;long long local;V3 m,dl;double g;};

static std::vector<Seg> make_segments(
  py::array_t<double,py::array::c_style|py::array::forcecast> pts,
  py::array_t<long long,py::array::c_style|py::array::forcecast> offs,
  py::array_t<double,py::array::c_style|py::array::forcecast> gam){
  auto P=pts.unchecked<2>();auto O=offs.unchecked<1>();auto G=gam.unchecked<1>();
  if(P.shape(1)!=3||O.shape(0)!=G.shape(0)+1)throw std::runtime_error("shape mismatch");
  std::vector<Seg>s;s.reserve((size_t)P.shape(0));
  for(py::ssize_t c=0;c<G.shape(0);++c){long long a=O(c),b=O(c+1),n=b-a;
    for(long long j=0;j<n;++j){long long k=(j+1)%n;V3 x{P(a+j,0),P(a+j,1),P(a+j,2)},y{P(a+k,0),P(a+k,1),P(a+k,2)};
      s.push_back({(int)c,j,mul(add(x,y),0.5),sub(y,x),G(c)});}}
  return s;
}


inline double segdist2(V3 p1,V3 q1,V3 p2,V3 q2){
  V3 u=sub(q1,p1),v=sub(q2,p2),w=sub(p1,p2);double a=dot(u,u),b=dot(u,v),c=dot(v,v),d=dot(u,w),e=dot(v,w);
  const double eps=1e-30;double D=a*c-b*b,sN,sD=D,tN,tD=D;
  if(D<eps){sN=0.0;sD=1.0;tN=e;tD=c;}else{sN=b*e-c*d;tN=a*e-b*d;if(sN<0.0){sN=0.0;tN=e;tD=c;}else if(sN>sD){sN=sD;tN=e+b;tD=c;}}
  if(tN<0.0){tN=0.0;if(-d<0.0)sN=0.0;else if(-d>a)sN=sD;else{sN=-d;sD=a;}}
  else if(tN>tD){tN=tD;if((-d+b)<0.0)sN=0.0;else if((-d+b)>a)sN=sD;else{sN=(-d+b);sD=a;}}
  double sc=(std::abs(sN)<eps)?0.0:sN/std::max(sD,eps),tc=(std::abs(tN)<eps)?0.0:tN/std::max(tD,eps);V3 dp=add(w,sub(mul(u,sc),mul(v,tc)));return dot(dp,dp);
}

double min_nonlocal_segment_distance(
  py::array_t<double,py::array::c_style|py::array::forcecast> pts,
  py::array_t<long long,py::array::c_style|py::array::forcecast> offs,int adjacency){
  auto P=pts.unchecked<2>();auto O=offs.unchecked<1>();if(P.shape(1)!=3)throw std::runtime_error("shape mismatch");
  double best=1e300;py::gil_scoped_release release;
  for(py::ssize_t ci=0;ci<O.shape(0)-1;++ci){long long a0=O(ci),na=O(ci+1)-a0;
    for(py::ssize_t cj=ci;cj<O.shape(0)-1;++cj){long long b0=O(cj),nb=O(cj+1)-b0;
      for(long long i=0;i<na;++i){V3 p1{P(a0+i,0),P(a0+i,1),P(a0+i,2)},q1{P(a0+(i+1)%na,0),P(a0+(i+1)%na,1),P(a0+(i+1)%na,2)};
        long long j0=(ci==cj)?i+1:0;for(long long j=j0;j<nb;++j){if(ci==cj){long long diff=std::llabs(i-j),cyc=std::min(diff,na-diff);if(cyc<=adjacency)continue;}
          V3 p2{P(b0+j,0),P(b0+j,1),P(b0+j,2)},q2{P(b0+(j+1)%nb,0),P(b0+(j+1)%nb,1),P(b0+(j+1)%nb,2)};best=std::min(best,segdist2(p1,q1,p2,q2));}}}}
  return std::sqrt(best);
}

py::array_t<double> vortexlab_velocity(
  py::array_t<double,py::array::c_style|py::array::forcecast> pts,
  py::array_t<long long,py::array::c_style|py::array::forcecast> offs,
  py::array_t<double,py::array::c_style|py::array::forcecast> gam,
  double core,double delta,double c0){
  auto P=pts.unchecked<2>();auto O=offs.unchecked<1>();auto G=gam.unchecked<1>();
  if(P.shape(1)!=3||O.shape(0)!=G.shape(0)+1)throw std::runtime_error("shape mismatch");
  if(core<=0)throw std::runtime_error("core must be >0");
  auto seg=make_segments(pts,offs,gam);
  py::array_t<double> out({P.shape(0),static_cast<py::ssize_t>(3)});auto Q=out.mutable_unchecked<2>();
  py::gil_scoped_release release;
  #pragma omp parallel for if(P.shape(0)>64)
  for(long long gi=0;gi<(long long)P.shape(0);++gi){
    int ci=0;while(ci+1<O.shape(0)&&gi>=O(ci+1))++ci;long long a=O(ci),b=O(ci+1),n=b-a,ii=gi-a;
    long long im=(ii+n-1)%n,ip=(ii+1)%n;
    V3 xm{P(a+im,0),P(a+im,1),P(a+im,2)},x{P(gi,0),P(gi,1),P(gi,2)},xp{P(a+ip,0),P(a+ip,1),P(a+ip,2)};
    V3 dm=sub(x,xm),dp=sub(xp,x);double lm=std::max(norm(dm),1e-14),lp=std::max(norm(dp),1e-14);
    V3 t=add(mul(dm,1.0/lm),mul(dp,1.0/lp));t=mul(t,1.0/std::max(norm(t),1e-14));double ds=0.5*(lm+lp);
    V3 kvec=mul(add(sub(xp,mul(x,2.0)),xm),1.0/std::max(ds*ds,1e-14));
    double arg=2.0*std::sqrt(lm*lp)/(std::exp(delta)*core);arg=std::max(arg,1.0000001);
    double Lam=std::log(arg)+c0;V3 u=mul(cross(t,kvec),G(ci)*Lam/(4.0*PI));
    for(auto const&s:seg){if(s.comp==ci&&(s.local==ii||s.local==im))continue;V3 r=sub(x,s.m);double r2=dot(r,r);double soft=(s.comp==ci)?0.0:core*core;double den=std::pow(r2+soft,1.5);if(den>1e-20)u=add(u,mul(cross(s.dl,r),s.g/(4.0*PI*den)));}
    Q(gi,0)=u.x;Q(gi,1)=u.y;Q(gi,2)=u.z;
  }
  return out;
}

double regularized_energy(
  py::array_t<double,py::array::c_style|py::array::forcecast> pts,
  py::array_t<long long,py::array::c_style|py::array::forcecast> offs,
  py::array_t<double,py::array::c_style|py::array::forcecast> gam,double core,double rho){
  auto s=make_segments(pts,offs,gam);double sum=0.0,a2=core*core;
  py::gil_scoped_release release;
  #pragma omp parallel for reduction(+:sum) if(s.size()>128)
  for(long long i=0;i<(long long)s.size();++i){for(size_t j=0;j<s.size();++j){V3 r=sub(s[i].m,s[j].m);sum+=s[i].g*s[j].g*dot(s[i].dl,s[j].dl)/std::sqrt(dot(r,r)+a2);}}
  return rho*sum/(8.0*PI);
}

PYBIND11_MODULE(_native,m){
  m.doc()="Native VortexLab-style filament kernels for blind Fourier-vs-ideal SST falsifier";
  m.def("vortexlab_velocity",&vortexlab_velocity);
  m.def("regularized_energy",&regularized_energy);
  m.def("min_nonlocal_segment_distance",&min_nonlocal_segment_distance);
}
