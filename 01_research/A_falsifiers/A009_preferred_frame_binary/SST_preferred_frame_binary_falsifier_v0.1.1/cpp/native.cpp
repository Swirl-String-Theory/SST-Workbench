#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;
using V3 = std::array<double,3>;
static inline V3 sub3(const V3&a,const V3&b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static inline V3 add3(const V3&a,const V3&b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static inline V3 mul3(const V3&a,double s){return {a[0]*s,a[1]*s,a[2]*s};}
static inline double dot3(const V3&a,const V3&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static inline V3 cross3(const V3&a,const V3&b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static inline double norm2(const V3&a){return dot3(a,a);}

struct Segment { V3 dl, mid; };
static std::vector<Segment> make_segments(py::detail::unchecked_reference<double,2> p,
                                          const std::vector<ssize_t>& off){
    std::vector<Segment> seg;
    for(size_t k=0;k+1<off.size();++k){
        if(off[k+1]-off[k]<3) throw std::runtime_error("each component needs >=3 points");
        for(ssize_t i=off[k]; i<off[k+1]; ++i){
            ssize_t ip=(i+1<off[k+1])?i+1:off[k];
            V3 a{p(i,0),p(i,1),p(i,2)}, b{p(ip,0),p(ip,1),p(ip,2)};
            seg.push_back({sub3(b,a),mul3(add3(a,b),0.5)});
        }
    }
    return seg;
}
static std::vector<ssize_t> read_offsets(py::array_t<long long,py::array::c_style|py::array::forcecast> offsets,ssize_t n){
    auto o=offsets.unchecked<1>(); if(o.shape(0)<2) throw std::runtime_error("offsets length >=2 required");
    std::vector<ssize_t> off(o.shape(0)); for(ssize_t i=0;i<o.shape(0);++i) off[i]=(ssize_t)o(i);
    if(off.front()!=0||off.back()!=n) throw std::runtime_error("offsets must start 0 and end N");
    for(size_t i=1;i<off.size();++i) if(off[i]<=off[i-1]) throw std::runtime_error("offsets must increase");
    return off;
}

double filament_system_energy(py::array_t<double,py::array::c_style|py::array::forcecast> points,
                              py::array_t<long long,py::array::c_style|py::array::forcecast> offsets,
                              double rho,double gamma,double core_radius){
    auto p=points.unchecked<2>(); if(p.shape(1)!=3||p.shape(0)<3) throw std::runtime_error("points must be (N,3)");
    auto off=read_offsets(offsets,p.shape(0)); auto seg=make_segments(p,off); const double a2=core_radius*core_radius; double sum=0;
    for(const auto& si:seg) for(const auto& sj:seg){auto r=sub3(si.mid,sj.mid);sum+=dot3(si.dl,sj.dl)/std::sqrt(norm2(r)+a2);}
    return rho*gamma*gamma*sum/(8.0*PI);
}

py::array_t<double> biot_savart_system_velocity(py::array_t<double,py::array::c_style|py::array::forcecast> points,
                              py::array_t<long long,py::array::c_style|py::array::forcecast> offsets,
                              double gamma,double core_radius,
                              py::array_t<double,py::array::c_style|py::array::forcecast> background){
    auto p=points.unchecked<2>(); auto bg=background.unchecked<1>(); if(p.shape(1)!=3||bg.shape(0)!=3) throw std::runtime_error("shape error");
    auto off=read_offsets(offsets,p.shape(0)); auto seg=make_segments(p,off); const double a2=core_radius*core_radius,pref=gamma/(4.0*PI);
    py::array_t<double> out({p.shape(0),(ssize_t)3}); auto v=out.mutable_unchecked<2>();
    for(ssize_t i=0;i<p.shape(0);++i){ V3 x{p(i,0),p(i,1),p(i,2)}, vi{bg(0),bg(1),bg(2)};
        for(const auto&s:seg){auto r=sub3(x,s.mid);double den=std::pow(norm2(r)+a2,1.5);auto c=cross3(s.dl,r);vi[0]+=pref*c[0]/den;vi[1]+=pref*c[1]/den;vi[2]+=pref*c[2]/den;}
        v(i,0)=vi[0];v(i,1)=vi[1];v(i,2)=vi[2]; }
    return out;
}

double filament_energy(py::array_t<double,py::array::c_style|py::array::forcecast> points,double rho,double gamma,double core_radius){
    auto p=points.unchecked<2>(); long long n=(long long)p.shape(0); py::array_t<long long> o(2); auto oo=o.mutable_unchecked<1>();oo(0)=0;oo(1)=n;
    return filament_system_energy(points,o,rho,gamma,core_radius);
}
py::array_t<double> biot_savart_velocity(py::array_t<double,py::array::c_style|py::array::forcecast> points,double gamma,double core_radius,py::array_t<double,py::array::c_style|py::array::forcecast> background){
    auto p=points.unchecked<2>(); long long n=(long long)p.shape(0); py::array_t<long long> o(2); auto oo=o.mutable_unchecked<1>();oo(0)=0;oo(1)=n;
    return biot_savart_system_velocity(points,o,gamma,core_radius,background);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST preferred-frame finite-core filament kernels v0.1.1";
    m.def("filament_energy",&filament_energy); m.def("biot_savart_velocity",&biot_savart_velocity);
    m.def("filament_system_energy",&filament_system_energy); m.def("biot_savart_system_velocity",&biot_savart_system_velocity);
}
