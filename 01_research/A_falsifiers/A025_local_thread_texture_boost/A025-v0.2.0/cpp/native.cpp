#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstdint>
#include <vector>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py=pybind11;
static constexpr double INV4PI=1.0/(4.0*3.141592653589793238462643383279502884);

struct Vec3 { double x,y,z; };
inline Vec3 add(Vec3 a,Vec3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline Vec3 sub(Vec3 a,Vec3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline Vec3 mul(double s,Vec3 a){return {s*a.x,s*a.y,s*a.z};}
inline Vec3 cross(Vec3 a,Vec3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}

static void velocity_kernel(const std::vector<Vec3>& X,
                            const std::vector<Vec3>& P,
                            const std::vector<std::int64_t>& O,
                            const std::vector<double>& G,
                            double core,
                            std::vector<Vec3>& V)
{
    if(G.size()+1!=O.size()) throw std::runtime_error("gamma/component mismatch");
    const double a2=core*core;
    V.assign(X.size(),{0,0,0});
    #pragma omp parallel for if(X.size()>64)
    for(std::int64_t ii=0; ii<(std::int64_t)X.size(); ++ii){
        Vec3 sum{0,0,0};
        for(std::size_t c=0;c+1<O.size();++c){
            const std::int64_t lo=O[c],hi=O[c+1];
            if(hi-lo<3) continue;
            const double pref=G[c]*INV4PI;
            for(std::int64_t j=lo;j<hi;++j){
                const std::int64_t k=(j+1<hi)?j+1:lo;
                Vec3 dl=sub(P[k],P[j]);
                Vec3 mid=mul(0.5,add(P[k],P[j]));
                Vec3 r=sub(X[ii],mid);
                const double den=std::pow(r.x*r.x+r.y*r.y+r.z*r.z+a2,1.5);
                if(den<=0) continue;
                Vec3 cr=cross(dl,r);
                sum.x+=pref*cr.x/den; sum.y+=pref*cr.y/den; sum.z+=pref*cr.z/den;
            }
        }
        V[ii]=sum;
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

py::array_t<double> evolve_frozen_background(
    py::array_t<double,py::array::c_style|py::array::forcecast> points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> knot_offsets,
    double knot_gamma,double knot_core,
    py::array_t<double,py::array::c_style|py::array::forcecast> thread_points,
    py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> thread_offsets,
    py::array_t<double,py::array::c_style|py::array::forcecast> thread_gammas,
    double thread_core,double dt,int steps,
    py::array_t<double,py::array::c_style|py::array::forcecast> boost)
{
    auto P=array_to_vec(points); const auto P0=P;
    auto KO=offsets_to_vec(knot_offsets);
    std::vector<double> KG(KO.size()>0?KO.size()-1:0,knot_gamma);
    auto T0=array_to_vec(thread_points); auto TO=offsets_to_vec(thread_offsets); auto TG=gamma_to_vec(thread_gammas);
    auto B=boost.unchecked<1>(); if(B.shape(0)!=3) throw std::runtime_error("boost must have length 3");
    Vec3 U{B(0),B(1),B(2)};
    std::vector<Vec3> vself,vbg,v1,v2,Pm,T,Tm;
    for(int s=0;s<steps;++s){
        const double t=s*dt;
        T=T0; for(auto& q:T) q=add(q,mul(t,U));
        velocity_kernel(P,P,KO,KG,knot_core,vself);
        if(!T.empty()) velocity_kernel(P,T,TO,TG,thread_core,vbg); else vbg.assign(P.size(),{0,0,0});
        v1.resize(P.size()); Pm.resize(P.size());
        for(std::size_t i=0;i<P.size();++i){v1[i]=add(add(vself[i],vbg[i]),U); Pm[i]=add(P[i],mul(0.5*dt,v1[i]));}
        Tm=T0; for(auto& q:Tm) q=add(q,mul(t+0.5*dt,U));
        velocity_kernel(Pm,Pm,KO,KG,knot_core,vself);
        if(!Tm.empty()) velocity_kernel(Pm,Tm,TO,TG,thread_core,vbg); else vbg.assign(P.size(),{0,0,0});
        v2.resize(P.size());
        for(std::size_t i=0;i<P.size();++i){v2[i]=add(add(vself[i],vbg[i]),U); P[i]=add(P[i],mul(dt,v2[i]));}
    }
    return vec_to_array(P);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST v0.2.1 C++17 explicit closed-thread Biot-Savart and RK2 evolution kernel";
    m.def("filament_velocity",&filament_velocity,py::arg("eval_points"),py::arg("filament_points"),py::arg("component_offsets"),py::arg("gammas"),py::arg("core_radius")=0.05);
    m.def("evolve_frozen_background",&evolve_frozen_background,
          py::arg("points"),py::arg("component_offsets"),py::arg("gamma"),py::arg("knot_core_radius"),
          py::arg("thread_points"),py::arg("thread_offsets"),py::arg("thread_gammas"),py::arg("thread_core_radius"),
          py::arg("dt"),py::arg("steps"),py::arg("boost"));
}
