#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

struct V3 {
    double x, y, z;
};
static inline V3 add(V3 a, V3 b){ return {a.x+b.x,a.y+b.y,a.z+b.z}; }
static inline V3 sub(V3 a, V3 b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
static inline V3 mul(V3 a, double s){ return {a.x*s,a.y*s,a.z*s}; }
static inline double dot(V3 a, V3 b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
static inline V3 cross(V3 a, V3 b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
static inline double norm2(V3 a){ return dot(a,a); }
static inline double norm(V3 a){ return std::sqrt(norm2(a)); }
static inline V3 unit(V3 a){ double n=norm(a); return n>0 ? mul(a,1.0/n) : V3{0,0,0}; }

struct Seg {
    V3 a,b,m,dl,t;
    int comp;
    int local;
    int ncompseg;
};

static std::vector<Seg> make_segments(py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
                                      const std::vector<int>& offsets) {
    auto v = vertices.unchecked<2>();
    if (v.shape(1) != 3) throw std::runtime_error("vertices must have shape (N,3)");
    if (offsets.size() < 2) throw std::runtime_error("offsets must contain at least [0,N]");
    std::vector<Seg> segs;
    for (size_t c=0;c+1<offsets.size();++c){
        int lo=offsets[c], hi=offsets[c+1];
        int n=hi-lo;
        if(n<3) continue;
        for(int i=0;i<n;++i){
            int i0=lo+i, i1=lo+((i+1)%n);
            V3 a{v(i0,0),v(i0,1),v(i0,2)};
            V3 b{v(i1,0),v(i1,1),v(i1,2)};
            V3 dl=sub(b,a);
            double ln=norm(dl);
            if(ln<=0) continue;
            segs.push_back({a,b,mul(add(a,b),0.5),dl,mul(dl,1.0/ln),(int)c,i,n});
        }
    }
    return segs;
}

py::array_t<double> biot_savart_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> queries,
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    const std::vector<int>& offsets,
    double gamma,
    double core)
{
    auto q=queries.unchecked<2>();
    if(q.shape(1)!=3) throw std::runtime_error("queries must have shape (N,3)");
    auto segs=make_segments(vertices, offsets);
    py::array_t<double> out({q.shape(0), (py::ssize_t)3});
    auto o=out.mutable_unchecked<2>();
    const double fac=gamma/(4.0*PI);
    const double a2=core*core;
    for(py::ssize_t p=0;p<q.shape(0);++p){
        V3 x{q(p,0),q(p,1),q(p,2)};
        V3 u{0,0,0};
        for(const auto& s:segs){
            V3 r=sub(x,s.m);
            double d2=norm2(r)+a2;
            double inv=1.0/(d2*std::sqrt(d2));
            V3 du=mul(cross(s.dl,r),fac*inv);
            u=add(u,du);
        }
        o(p,0)=u.x; o(p,1)=u.y; o(p,2)=u.z;
    }
    return out;
}

double regularized_energy(
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    const std::vector<int>& offsets,
    double rho,
    double gamma,
    double core)
{
    auto segs=make_segments(vertices, offsets);
    long double sum=0.0L;
    const double a2=core*core;
    for(size_t i=0;i<segs.size();++i){
        for(size_t j=i;j<segs.size();++j){
            V3 r=sub(segs[i].m,segs[j].m);
            double den=std::sqrt(norm2(r)+a2);
            long double term=(long double)dot(segs[i].dl,segs[j].dl)/(long double)den;
            sum += (i==j) ? term : 2.0L*term;
        }
    }
    return (rho*gamma*gamma/(8.0*PI))*(double)sum;
}

// Midpoint Gauss integral approximation. Converges rapidly for well-resolved disjoint curves.
double gauss_linking_components(
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    const std::vector<int>& offsets,
    int comp_a,
    int comp_b)
{
    auto segs=make_segments(vertices, offsets);
    long double sum=0.0L;
    for(const auto& sa:segs){
        if(sa.comp!=comp_a) continue;
        for(const auto& sb:segs){
            if(sb.comp!=comp_b) continue;
            V3 r=sub(sa.m,sb.m);
            double r2=norm2(r);
            if(r2<=1e-30) continue;
            double inv=1.0/(r2*std::sqrt(r2));
            sum += (long double)dot(cross(sa.dl,sb.dl),r)*(long double)inv;
        }
    }
    return (double)(sum/(4.0*PI));
}

double gauss_writhe_component(
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    const std::vector<int>& offsets,
    int comp)
{
    auto segs=make_segments(vertices, offsets);
    std::vector<const Seg*> s;
    for(const auto& x:segs) if(x.comp==comp) s.push_back(&x);
    const int n=(int)s.size();
    long double sum=0.0L;
    for(int i=0;i<n;++i){
        for(int j=0;j<n;++j){
            if(i==j) continue;
            int d=std::abs(i-j); d=std::min(d,n-d);
            if(d<=1) continue;
            V3 r=sub(s[i]->m,s[j]->m);
            double r2=norm2(r);
            if(r2<=1e-30) continue;
            double inv=1.0/(r2*std::sqrt(r2));
            sum += (long double)dot(cross(s[i]->dl,s[j]->dl),r)*(long double)inv;
        }
    }
    return (double)(sum/(4.0*PI));
}

static double segment_segment_distance(V3 p1,V3 q1,V3 p2,V3 q2){
    const double EPS=1e-15;
    V3 d1=sub(q1,p1), d2=sub(q2,p2), r=sub(p1,p2);
    double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
    double s=0.0,t=0.0;
    if(a<=EPS && e<=EPS) return norm(r);
    if(a<=EPS){ s=0.0; t=std::clamp(f/e,0.0,1.0); }
    else {
        double c=dot(d1,r);
        if(e<=EPS){ t=0.0; s=std::clamp(-c/a,0.0,1.0); }
        else {
            double b=dot(d1,d2), denom=a*e-b*b;
            if(denom!=0.0) s=std::clamp((b*f-c*e)/denom,0.0,1.0); else s=0.0;
            t=(b*s+f)/e;
            if(t<0.0){ t=0.0; s=std::clamp(-c/a,0.0,1.0); }
            else if(t>1.0){ t=1.0; s=std::clamp((b-c)/a,0.0,1.0); }
        }
    }
    V3 c1=add(p1,mul(d1,s)), c2=add(p2,mul(d2,t));
    return norm(sub(c1,c2));
}

py::list nearest_segment_contacts(
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    const std::vector<int>& offsets,
    int adjacency_exclusion,
    int top_k)
{
    auto segs=make_segments(vertices, offsets);
    struct Rec { double dist,dotv; int ca,ia,cb,ib; };
    std::vector<Rec> recs;
    recs.reserve(std::min<size_t>((size_t)top_k*8,segs.size()*2));
    for(size_t i=0;i<segs.size();++i){
        for(size_t j=i+1;j<segs.size();++j){
            const auto& a=segs[i]; const auto& b=segs[j];
            if(a.comp==b.comp){
                int d=std::abs(a.local-b.local); d=std::min(d,a.ncompseg-d);
                if(d<=adjacency_exclusion) continue;
            }
            double dist=segment_segment_distance(a.a,a.b,b.a,b.b);
            recs.push_back({dist,dot(a.t,b.t),a.comp,a.local,b.comp,b.local});
        }
    }
    std::sort(recs.begin(),recs.end(),[](const Rec& x,const Rec& y){ return x.dist<y.dist; });
    if((int)recs.size()>top_k) recs.resize(top_k);
    py::list out;
    for(const auto& r:recs){
        py::dict d;
        d["distance"]=r.dist; d["tangent_dot"]=r.dotv;
        d["comp_a"]=r.ca; d["seg_a"]=r.ia; d["comp_b"]=r.cb; d["seg_b"]=r.ib;
        out.append(d);
    }
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Native kernels for SST six-source blind falsifier.";
    m.def("biot_savart_velocity", &biot_savart_velocity, py::arg("queries"), py::arg("vertices"), py::arg("offsets"), py::arg("gamma"), py::arg("core"));
    m.def("regularized_energy", &regularized_energy, py::arg("vertices"), py::arg("offsets"), py::arg("rho"), py::arg("gamma"), py::arg("core"));
    m.def("gauss_linking_components", &gauss_linking_components, py::arg("vertices"), py::arg("offsets"), py::arg("comp_a"), py::arg("comp_b"));
    m.def("gauss_writhe_component", &gauss_writhe_component, py::arg("vertices"), py::arg("offsets"), py::arg("comp"));
    m.def("nearest_segment_contacts", &nearest_segment_contacts, py::arg("vertices"), py::arg("offsets"), py::arg("adjacency_exclusion")=3, py::arg("top_k")=32);
}
