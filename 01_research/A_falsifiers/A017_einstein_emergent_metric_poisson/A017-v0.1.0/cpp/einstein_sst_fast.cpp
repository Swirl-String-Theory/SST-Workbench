#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <array>
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
using Vec=std::array<double,3>;
static constexpr double PI=3.141592653589793238462643383279502884;
static inline Vec sub(const Vec&a,const Vec&b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static inline Vec add(const Vec&a,const Vec&b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static inline Vec mul(const Vec&a,double s){return {a[0]*s,a[1]*s,a[2]*s};}
static inline double dot(const Vec&a,const Vec&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static inline double norm(const Vec&a){return std::sqrt(dot(a,a));}
static inline Vec cross(const Vec&a,const Vec&b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static std::vector<Vec> to_vecs(py::array_t<double,py::array::c_style|py::array::forcecast> arr){
 auto b=arr.request(); if(b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("array must be Nx3");
 const double* x=(const double*)b.ptr; std::vector<Vec> p((size_t)b.shape[0]);
 for(size_t i=0;i<p.size();++i)p[i]={x[3*i],x[3*i+1],x[3*i+2]};
 if(p.size()>=2){Vec mn=p[0],mx=p[0]; for(auto &v:p)for(int j=0;j<3;++j){mn[j]=std::min(mn[j],v[j]);mx[j]=std::max(mx[j],v[j]);}
  double sc=std::max(norm(sub(mx,mn)),1e-300); if(norm(sub(p.front(),p.back()))<=1e-12*sc)p.pop_back();}
 if(p.size()<8) throw std::runtime_error("need >=8 unique points"); return p;
}
static double closed_length_vec(const std::vector<Vec>&p){double L=0;for(size_t i=0;i<p.size();++i)L+=norm(sub(p[(i+1)%p.size()],p[i]));return L;}
py::array_t<double> resample_closed(py::array_t<double,py::array::c_style|py::array::forcecast> arr,int nout){
 auto p=to_vecs(arr); if(nout<8)throw std::runtime_error("nout>=8 required"); size_t n=p.size(); std::vector<double> cum(n+1,0);
 for(size_t i=0;i<n;++i)cum[i+1]=cum[i]+norm(sub(p[(i+1)%n],p[i])); double L=cum[n]; py::array_t<double> out({nout,3}); auto o=out.mutable_unchecked<2>();
 #pragma omp parallel for if(nout>256)
 for(int j=0;j<nout;++j){double s=L*(double)j/(double)nout; auto it=std::upper_bound(cum.begin(),cum.end(),s); size_t i=(size_t)std::max<long long>(0,(long long)(it-cum.begin())-1); if(i>=n)i=n-1; double ds=cum[i+1]-cum[i]; double f=ds>0?(s-cum[i])/ds:0; Vec q=add(mul(p[i],1-f),mul(p[(i+1)%n],f)); o(j,0)=q[0];o(j,1)=q[1];o(j,2)=q[2];}
 return out;
}
py::dict estimate_thickness(py::array_t<double,py::array::c_style|py::array::forcecast> arr,int exclude_steps){
 auto p=to_vecs(arr); size_t n=p.size(); double local=INFINITY;
 for(size_t i=0;i<n;++i){Vec a=p[(i+n-1)%n],b=p[i],c=p[(i+1)%n];Vec ab=sub(b,a),bc=sub(c,b),ac=sub(c,a);double la=norm(ab),lb=norm(bc),lc=norm(ac);double area2=norm(cross(ab,bc));double kap=2*area2/std::max(la*lb*lc,1e-300);if(kap>1e-14/std::max(la,1e-300))local=std::min(local,1.0/kap);}
 std::vector<Vec> tang(n); for(size_t i=0;i<n;++i){Vec tt=sub(p[(i+1)%n],p[(i+n-1)%n]);double nt=std::max(norm(tt),1e-300);tang[i]=mul(tt,1.0/nt);}
 double dmin=INFINITY; const double perp_tol=0.15;
 #pragma omp parallel for reduction(min:dmin) schedule(static) if(n>256)
 for(long long ii=0;ii<(long long)n;++ii){size_t i=(size_t)ii; for(size_t j=i+1;j<n;++j){size_t d=j-i;size_t sep=std::min(d,n-d);if((int)sep<=exclude_steps)continue;Vec rr=sub(p[j],p[i]);double dd=norm(rr);if(!(dd>0))continue;if(std::abs(dot(rr,tang[i]))/dd>perp_tol)continue;if(std::abs(dot(rr,tang[j]))/dd>perp_tol)continue;if(dd<dmin)dmin=dd;}}
 double nonlocal=0.5*dmin,th=std::min(local,nonlocal); py::dict d;d["thickness"]=th;d["local_curvature_radius_min"]=local;d["nonlocal_half_distance_min"]=nonlocal;d["limiter"]=(local<=nonlocal?"curvature":"self_distance");return d;
}
py::dict velocity_gradient(py::array_t<double,py::array::c_style|py::array::forcecast> parr,py::array_t<double,py::array::c_style|py::array::forcecast> qarr,double gamma,double core){
 auto p=to_vecs(parr); auto qb=qarr.request(); if(qb.ndim!=2||qb.shape[1]!=3)throw std::runtime_error("queries must be Mx3"); const double* q=(const double*)qb.ptr; size_t M=(size_t)qb.shape[0],N=p.size();
 py::array_t<double> va({(py::ssize_t)M,3}); py::array_t<double> ga({(py::ssize_t)M,3,3}); auto V=va.mutable_unchecked<2>(); auto G=ga.mutable_unchecked<3>(); double C=gamma/(4.0*PI),a2=core*core;
 #pragma omp parallel for schedule(static) if(M>64)
 for(long long mm=0;mm<(long long)M;++mm){Vec x={q[3*mm],q[3*mm+1],q[3*mm+2]};double vv[3]={0,0,0};double gg[3][3]={{0,0,0},{0,0,0},{0,0,0}};
  for(size_t s=0;s<N;++s){Vec a=p[s],b=p[(s+1)%N],dl=sub(b,a),mid=mul(add(a,b),0.5),r=sub(x,mid);double D=dot(r,r)+a2,inv3=1.0/(D*std::sqrt(D)),inv5=inv3/D;Vec cr=cross(dl,r);for(int i=0;i<3;++i)vv[i]+=C*cr[i]*inv3;
   for(int j=0;j<3;++j){Vec e={0,0,0};e[j]=1;Vec ce=cross(dl,e);for(int i=0;i<3;++i)gg[i][j]+=C*(ce[i]*inv3-3.0*cr[i]*r[j]*inv5);}}
  for(int i=0;i<3;++i){V(mm,i)=vv[i];for(int j=0;j<3;++j)G(mm,i,j)=gg[i][j];}}
 py::dict d;d["velocity"]=va;d["gradient"]=ga;return d;
}
PYBIND11_MODULE(_fast,m){m.doc()="OpenMP Biot-Savart/gradient backend for Einstein-SST closure gates";m.def("resample_closed",&resample_closed);m.def("estimate_thickness",&estimate_thickness,py::arg("points"),py::arg("exclude_steps")=8);m.def("velocity_gradient",&velocity_gradient,py::arg("points"),py::arg("queries"),py::arg("gamma")=1.0,py::arg("core_radius")=1.0);
#ifdef _OPENMP
 m.attr("openmp_enabled")=true;m.attr("openmp_max_threads")=omp_get_max_threads();
#else
 m.attr("openmp_enabled")=false;m.attr("openmp_max_threads")=1;
#endif
}
