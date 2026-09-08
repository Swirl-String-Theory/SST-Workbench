#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
static constexpr double INV4PI = 1.0/(4.0*3.141592653589793238462643383279502884);

struct Vec3 { double x,y,z; };
inline Vec3 add(Vec3 a, Vec3 b){ return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline Vec3 sub(Vec3 a, Vec3 b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline Vec3 mul(double s, Vec3 a){ return {s*a.x,s*a.y,s*a.z}; }
inline double dot(Vec3 a, Vec3 b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
inline double norm(Vec3 a){ return std::sqrt(dot(a,a)); }
inline Vec3 cross(Vec3 a, Vec3 b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }

// Exact straight-segment integral for the Rosenhead-regularized Biot--Savart kernel.
// Integrates e x r / (|r|^2+a^2)^(3/2) dl from p0 to p1 analytically.
inline Vec3 regularized_segment_integral(Vec3 x, Vec3 p0, Vec3 p1, double core){
    Vec3 d=sub(p1,p0);
    const double L=norm(d);
    if(!(L>0.0) || !std::isfinite(L)) return {0,0,0};
    Vec3 e=mul(1.0/L,d);
    Vec3 r0=sub(x,p0);
    const double z0=dot(e,r0);
    Vec3 rperp=sub(r0,mul(z0,e));
    const double A=dot(rperp,rperp)+core*core;
    if(!(A>0.0) || !std::isfinite(A)) return {0,0,0};
    const double z1=z0-L;
    const double f0=z0/(A*std::sqrt(A+z0*z0));
    const double f1=z1/(A*std::sqrt(A+z1*z1));
    return mul(f0-f1,cross(e,rperp));
}

static void velocity_kernel(const std::vector<Vec3>& X,
                            const std::vector<Vec3>& P,
                            const std::vector<std::int64_t>& O,
                            const std::vector<double>& G,
                            double core,
                            std::vector<Vec3>& V)
{
    if(G.size()+1!=O.size()) throw std::runtime_error("gamma/component mismatch");
    if(!(core>0.0)) throw std::runtime_error("core_radius must be > 0");
    V.assign(X.size(),{0,0,0});
    #pragma omp parallel for if(X.size()>64)
    for(std::int64_t ii=0; ii<(std::int64_t)X.size(); ++ii){
        Vec3 sum{0,0,0};
        for(std::size_t c=0;c+1<O.size();++c){
            const std::int64_t lo=O[c], hi=O[c+1];
            if(hi-lo<3) continue;
            const double pref=G[c]*INV4PI;
            for(std::int64_t j=lo;j<hi;++j){
                const std::int64_t k=(j+1<hi)?j+1:lo;
                Vec3 s=regularized_segment_integral(X[(std::size_t)ii],P[(std::size_t)j],P[(std::size_t)k],core);
                sum.x+=pref*s.x; sum.y+=pref*s.y; sum.z+=pref*s.z;
            }
        }
        V[(std::size_t)ii]=sum;
    }
}

static std::vector<Vec3> array_to_vec(py::array_t<double,py::array::c_style|py::array::forcecast> a){
    auto A=a.unchecked<2>();
    if(A.shape(1)!=3) throw std::runtime_error("array must have shape (N,3)");
    std::vector<Vec3> v((std::size_t)A.shape(0));
    for(py::ssize_t i=0;i<A.shape(0);++i) v[(std::size_t)i]={A(i,0),A(i,1),A(i,2)};
    return v;
}
static std::vector<std::int64_t> offsets_to_vec(py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> a){
    auto A=a.unchecked<1>(); std::vector<std::int64_t> v((std::size_t)A.shape(0));
    for(py::ssize_t i=0;i<A.shape(0);++i) v[(std::size_t)i]=A(i); return v;
}
static std::vector<double> gamma_to_vec(py::array_t<double,py::array::c_style|py::array::forcecast> a){
    auto A=a.unchecked<1>(); std::vector<double> v((std::size_t)A.shape(0));
    for(py::ssize_t i=0;i<A.shape(0);++i) v[(std::size_t)i]=A(i); return v;
}
static py::array_t<double> vec_to_array(const std::vector<Vec3>& v){
    py::array_t<double> out(std::vector<py::ssize_t>{(py::ssize_t)v.size(),(py::ssize_t)3});
    auto A=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<(py::ssize_t)v.size();++i){A(i,0)=v[(std::size_t)i].x;A(i,1)=v[(std::size_t)i].y;A(i,2)=v[(std::size_t)i].z;}
    return out;
}

static void reparameterize_component(std::vector<Vec3>& P, std::int64_t lo, std::int64_t hi){
    const std::int64_t n=hi-lo;
    if(n<3) return;
    std::vector<double> seg((std::size_t)n), cum((std::size_t)n+1,0.0);
    double L=0.0;
    for(std::int64_t j=0;j<n;++j){
        const std::int64_t k=(j+1<n)?j+1:0;
        seg[(std::size_t)j]=norm(sub(P[(std::size_t)(lo+k)],P[(std::size_t)(lo+j)]));
        L+=seg[(std::size_t)j]; cum[(std::size_t)j+1]=L;
    }
    if(!(L>0.0) || !std::isfinite(L)) return;
    std::vector<Vec3> q((std::size_t)n);
    std::int64_t j=0;
    for(std::int64_t i=0;i<n;++i){
        const double target=L*(double)i/(double)n;
        while(j+1<n && cum[(std::size_t)j+1]<=target) ++j;
        const std::int64_t k=(j+1<n)?j+1:0;
        const double den=seg[(std::size_t)j];
        const double u=(den>0.0)?(target-cum[(std::size_t)j])/den:0.0;
        q[(std::size_t)i]=add(mul(1.0-u,P[(std::size_t)(lo+j)]),mul(u,P[(std::size_t)(lo+k)]));
    }
    for(std::int64_t i=0;i<n;++i) P[(std::size_t)(lo+i)]=q[(std::size_t)i];
}

static void reparameterize_all(std::vector<Vec3>& P, const std::vector<std::int64_t>& O){
    for(std::size_t c=0;c+1<O.size();++c) reparameterize_component(P,O[c],O[c+1]);
}

static void rhs(const std::vector<Vec3>& P,
                const std::vector<std::int64_t>& KO,
                const std::vector<double>& KG,
                double knot_core,
                const std::vector<Vec3>& T0,
                const std::vector<std::int64_t>& TO,
                const std::vector<double>& TG,
                double thread_core,
                Vec3 U, double t,
                std::vector<Vec3>& out)
{
    std::vector<Vec3> vself,vbg,T;
    velocity_kernel(P,P,KO,KG,knot_core,vself);
    if(!T0.empty()){
        T=T0;
        for(auto& q:T) q=add(q,mul(t,U));
        velocity_kernel(P,T,TO,TG,thread_core,vbg);
    } else vbg.assign(P.size(),{0,0,0});
    out.resize(P.size());
    for(std::size_t i=0;i<P.size();++i) out[i]=add(add(vself[i],vbg[i]),U);
}

py::array_t<double> filament_velocity(
    py::array_t<double,py::array::c_style|py::array::forcecast> eval_points,
    py::array_t<double,py::array::c_style|py::array::forcecast> filament_points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> offsets,
    py::array_t<double,py::array::c_style|py::array::forcecast> gammas,
    double core_radius)
{
    auto X=array_to_vec(eval_points); auto P=array_to_vec(filament_points);
    auto O=offsets_to_vec(offsets); auto G=gamma_to_vec(gammas); std::vector<Vec3> V;
    velocity_kernel(X,P,O,G,core_radius,V); return vec_to_array(V);
}

py::array_t<double> reparameterize_closed(
    py::array_t<double,py::array::c_style|py::array::forcecast> points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> offsets)
{
    auto P=array_to_vec(points); auto O=offsets_to_vec(offsets); reparameterize_all(P,O); return vec_to_array(P);
}

py::array_t<double> evolve_frozen_background(
    py::array_t<double,py::array::c_style|py::array::forcecast> points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> knot_offsets,
    double knot_gamma,double knot_core,
    py::array_t<double,py::array::c_style|py::array::forcecast> thread_points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> thread_offsets,
    py::array_t<double,py::array::c_style|py::array::forcecast> thread_gammas,
    double thread_core,double dt,int steps,
    py::array_t<double,py::array::c_style|py::array::forcecast> boost,
    int reparameterize_every)
{
    auto P=array_to_vec(points); auto KO=offsets_to_vec(knot_offsets);
    std::vector<double> KG(KO.size()>0?KO.size()-1:0,knot_gamma);
    auto T0=array_to_vec(thread_points); auto TO=offsets_to_vec(thread_offsets); auto TG=gamma_to_vec(thread_gammas);
    auto B=boost.unchecked<1>(); if(B.shape(0)!=3) throw std::runtime_error("boost must have length 3");
    Vec3 U{B(0),B(1),B(2)};
    std::vector<Vec3> k1,k2,k3,k4,tmp;
    for(int s=0;s<steps;++s){
        const double t=s*dt;
        rhs(P,KO,KG,knot_core,T0,TO,TG,thread_core,U,t,k1);
        tmp.resize(P.size()); for(std::size_t i=0;i<P.size();++i) tmp[i]=add(P[i],mul(0.5*dt,k1[i]));
        rhs(tmp,KO,KG,knot_core,T0,TO,TG,thread_core,U,t+0.5*dt,k2);
        for(std::size_t i=0;i<P.size();++i) tmp[i]=add(P[i],mul(0.5*dt,k2[i]));
        rhs(tmp,KO,KG,knot_core,T0,TO,TG,thread_core,U,t+0.5*dt,k3);
        for(std::size_t i=0;i<P.size();++i) tmp[i]=add(P[i],mul(dt,k3[i]));
        rhs(tmp,KO,KG,knot_core,T0,TO,TG,thread_core,U,t+dt,k4);
        for(std::size_t i=0;i<P.size();++i){
            Vec3 acc=add(add(k1[i],mul(2.0,k2[i])),add(mul(2.0,k3[i]),k4[i]));
            P[i]=add(P[i],mul(dt/6.0,acc));
        }
        if(reparameterize_every>0 && ((s+1)%reparameterize_every)==0) reparameterize_all(P,KO);
    }
    return vec_to_array(P);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST v0.3.0 exact regularized straight-segment Biot-Savart + RK4 kernel";
    m.def("filament_velocity",&filament_velocity,py::arg("eval_points"),py::arg("filament_points"),py::arg("component_offsets"),py::arg("gammas"),py::arg("core_radius")=0.05);
    m.def("reparameterize_closed",&reparameterize_closed,py::arg("points"),py::arg("component_offsets"));
    m.def("evolve_frozen_background",&evolve_frozen_background,
          py::arg("points"),py::arg("component_offsets"),py::arg("gamma"),py::arg("knot_core_radius"),
          py::arg("thread_points"),py::arg("thread_offsets"),py::arg("thread_gammas"),py::arg("thread_core_radius"),
          py::arg("dt"),py::arg("steps"),py::arg("boost"),py::arg("reparameterize_every")=0);
}
