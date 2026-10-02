#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <limits>
#include <array>
#include <algorithm>
#include <cstddef>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;

struct V3 { double x,y,z; };
static inline V3 sub(V3 a,V3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static inline V3 add(V3 a,V3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static inline V3 mul(V3 a,double s){return {a.x*s,a.y*s,a.z*s};}
static inline double dot(V3 a,V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static inline V3 cross(V3 a,V3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static inline double norm(V3 a){return std::sqrt(dot(a,a));}
static inline V3 at(const double* p, std::ptrdiff_t i){return {p[3*i],p[3*i+1],p[3*i+2]};}
static inline int csep(int i,int j,int n){int d=std::abs(i-j);return std::min(d,n-d);}

static double segdist(V3 p1,V3 q1,V3 p2,V3 q2){
    const double EPS=1e-15;
    V3 d1=sub(q1,p1), d2=sub(q2,p2), r=sub(p1,p2);
    double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r), s=0,t=0;
    if(a<=EPS && e<=EPS) return norm(r);
    if(a<=EPS){ s=0; t=std::clamp(f/e,0.0,1.0); }
    else {
        double c=dot(d1,r);
        if(e<=EPS){ t=0; s=std::clamp(-c/a,0.0,1.0); }
        else {
            double b=dot(d1,d2), den=a*e-b*b;
            if(den!=0) s=std::clamp((b*f-c*e)/den,0.0,1.0); else s=0;
            t=(b*s+f)/e;
            if(t<0){t=0;s=std::clamp(-c/a,0.0,1.0);} else if(t>1){t=1;s=std::clamp((b-c)/a,0.0,1.0);}
        }
    }
    return norm(sub(add(p1,mul(d1,s)),add(p2,mul(d2,t))));
}

static double min_nonlocal_segment_distance(py::array_t<double,py::array::c_style|py::array::forcecast> arr,int exclusion){
    auto b=arr.request(); if(b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("Nx3 expected");
    int n=(int)b.shape[0]; const double* p=(const double*)b.ptr; double best=std::numeric_limits<double>::infinity();
#ifdef _OPENMP
    #pragma omp parallel
    {
        double local_best=std::numeric_limits<double>::infinity();
        #pragma omp for schedule(dynamic,8) nowait
        for(int i=0;i<n;i++) for(int j=i+1;j<n;j++){
            if(csep(i,j,n)<=exclusion || csep(i,(j+1)%n,n)<=exclusion || csep((i+1)%n,j,n)<=exclusion) continue;
            double d=segdist(at(p,i),at(p,(i+1)%n),at(p,j),at(p,(j+1)%n));
            if(d<local_best) local_best=d;
        }
        #pragma omp critical(pklsa_min_nonlocal_update)
        { if(local_best<best) best=local_best; }
    }
#else
    for(int i=0;i<n;i++) for(int j=i+1;j<n;j++){
        if(csep(i,j,n)<=exclusion || csep(i,(j+1)%n,n)<=exclusion || csep((i+1)%n,j,n)<=exclusion) continue;
        double d=segdist(at(p,i),at(p,(i+1)%n),at(p,j),at(p,(j+1)%n));
        if(d<best) best=d;
    }
#endif
    return best;
}

static double min_intercomponent_segment_distance(py::array_t<double,py::array::c_style|py::array::forcecast> A,py::array_t<double,py::array::c_style|py::array::forcecast> B){
    auto a=A.request(),b=B.request(); if(a.ndim!=2||a.shape[1]!=3||b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("Nx3 expected");
    int n=(int)a.shape[0],m=(int)b.shape[0]; const double* p=(const double*)a.ptr; const double* q=(const double*)b.ptr; double best=std::numeric_limits<double>::infinity();
#ifdef _OPENMP
    #pragma omp parallel
    {
        double local_best=std::numeric_limits<double>::infinity();
        #pragma omp for schedule(dynamic,8) nowait
        for(int i=0;i<n;i++) for(int j=0;j<m;j++){
            double d=segdist(at(p,i),at(p,(i+1)%n),at(q,j),at(q,(j+1)%m));
            if(d<local_best) local_best=d;
        }
        #pragma omp critical(pklsa_min_intercomponent_update)
        { if(local_best<best) best=local_best; }
    }
#else
    for(int i=0;i<n;i++) for(int j=0;j<m;j++){
        double d=segdist(at(p,i),at(p,(i+1)%n),at(q,j),at(q,(j+1)%m));
        if(d<best) best=d;
    }
#endif
    return best;
}

static double approximate_dcsd(py::array_t<double,py::array::c_style|py::array::forcecast> P,py::array_t<double,py::array::c_style|py::array::forcecast> T,int exclusion,double orth_tol){
    auto a=P.request(),b=T.request(); if(a.ndim!=2||a.shape[1]!=3||b.ndim!=2||b.shape[1]!=3||a.shape[0]!=b.shape[0]) throw std::runtime_error("matching Nx3 expected");
    int n=(int)a.shape[0];const double* p=(const double*)a.ptr;const double* t=(const double*)b.ptr;double best=std::numeric_limits<double>::infinity();
#ifdef _OPENMP
    #pragma omp parallel
    {
        double local_best=std::numeric_limits<double>::infinity();
        #pragma omp for schedule(dynamic,8) nowait
        for(int i=0;i<n;i++) for(int j=i+1;j<n;j++){
            if(csep(i,j,n)<=exclusion)continue;
            V3 d=sub(at(p,j),at(p,i));double dn=norm(d);if(dn<=0)continue;V3 u=mul(d,1.0/dn);
            if(std::abs(dot(u,at(t,i)))<=orth_tol && std::abs(dot(u,at(t,j)))<=orth_tol && dn<local_best)local_best=dn;
        }
        #pragma omp critical(pklsa_dcsd_update)
        { if(local_best<best) best=local_best; }
    }
#else
    for(int i=0;i<n;i++) for(int j=i+1;j<n;j++){
        if(csep(i,j,n)<=exclusion)continue;
        V3 d=sub(at(p,j),at(p,i));double dn=norm(d);if(dn<=0)continue;V3 u=mul(d,1.0/dn);
        if(std::abs(dot(u,at(t,i)))<=orth_tol && std::abs(dot(u,at(t,j)))<=orth_tol && dn<best)best=dn;
    }
#endif
    return best;
}

static py::tuple writhe_acn(py::array_t<double,py::array::c_style|py::array::forcecast> P){
    auto a=P.request(); if(a.ndim!=2||a.shape[1]!=3) throw std::runtime_error("Nx3 expected");int n=(int)a.shape[0];const double* p=(const double*)a.ptr;double wr=0,acn=0;
    #pragma omp parallel for reduction(+:wr,acn) schedule(dynamic,8)
    for(int i=0;i<n;i++){
        V3 pi=at(p,i), qi=at(p,(i+1)%n), di=sub(qi,pi), mi=mul(add(pi,qi),.5);
        for(int j=i+1;j<n;j++){
            if(csep(i,j,n)<=1)continue;V3 pj=at(p,j),qj=at(p,(j+1)%n),dj=sub(qj,pj),mj=mul(add(pj,qj),.5),r=sub(mi,mj);double rn=norm(r);if(rn<=1e-15)continue;
            double g=dot(cross(di,dj),r)/(rn*rn*rn);wr+=2*g;acn+=2*std::abs(g);
        }
    }
    constexpr double PI=3.141592653589793238462643383279502884; double c=1.0/(4.0*PI);return py::make_tuple(wr*c,acn*c);
}

static double linking_number(py::array_t<double,py::array::c_style|py::array::forcecast> A,py::array_t<double,py::array::c_style|py::array::forcecast> B){
    auto a=A.request(),b=B.request(); if(a.ndim!=2||a.shape[1]!=3||b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("Nx3 expected");int n=(int)a.shape[0],m=(int)b.shape[0];const double* p=(const double*)a.ptr;const double* q=(const double*)b.ptr;double s=0;
    #pragma omp parallel for reduction(+:s) schedule(dynamic,8)
    for(int i=0;i<n;i++){
        V3 pi=at(p,i),qi=at(p,(i+1)%n),di=sub(qi,pi),mi=mul(add(pi,qi),.5);
        for(int j=0;j<m;j++){V3 pj=at(q,j),qj=at(q,(j+1)%m),dj=sub(qj,pj),mj=mul(add(pj,qj),.5),r=sub(mi,mj);double rn=norm(r);if(rn>1e-15)s+=dot(cross(di,dj),r)/(rn*rn*rn);}
    }
    constexpr double PI=3.141592653589793238462643383279502884; return s/(4.0*PI);
}

PYBIND11_MODULE(_native,m){
    m.doc()="PKLSA v0.3 high-resolution nonlocal geometry kernels";
    m.def("min_nonlocal_segment_distance",&min_nonlocal_segment_distance);
    m.def("min_intercomponent_segment_distance",&min_intercomponent_segment_distance);
    m.def("approximate_dcsd",&approximate_dcsd);
    m.def("writhe_acn",&writhe_acn);
    m.def("linking_number",&linking_number);
#ifdef _OPENMP
    m.attr("openmp_enabled")=true;
#else
    m.attr("openmp_enabled")=false;
#endif
}
