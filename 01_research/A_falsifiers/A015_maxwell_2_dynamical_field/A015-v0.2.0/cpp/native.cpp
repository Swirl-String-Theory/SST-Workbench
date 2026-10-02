#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <thread>
#include <vector>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

struct V3 { double x,y,z; };
inline V3 add(V3 a,V3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline V3 sub(V3 a,V3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline V3 mul(V3 a,double s){return {a.x*s,a.y*s,a.z*s};}
inline double dot(V3 a,V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline V3 cross(V3 a,V3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline double norm(V3 a){return std::sqrt(dot(a,a));}

template<class F>
void parallel_for(std::size_t n, int threads, F fn){
    if(n==0) return;
    unsigned hw=std::thread::hardware_concurrency();
    int nt=threads>0?threads:(hw?static_cast<int>(hw):1);
    nt=std::max(1,std::min<int>(nt,static_cast<int>(n)));
    if(nt==1 || n<64){ for(std::size_t i=0;i<n;++i) fn(i); return; }
    std::vector<std::thread> pool; pool.reserve(nt);
    std::atomic<std::size_t> next{0};
    for(int t=0;t<nt;++t) pool.emplace_back([&](){
        for(;;){ auto i=next.fetch_add(1); if(i>=n) break; fn(i); }
    });
    for(auto &th:pool) th.join();
}

std::vector<V3> read_points(const py::array_t<double, py::array::c_style | py::array::forcecast>& a){
    auto b=a.request(); if(b.ndim!=2 || b.shape[1]!=3) throw std::runtime_error("points must be Nx3");
    const double* p=static_cast<const double*>(b.ptr); std::vector<V3> out(b.shape[0]);
    for(ssize_t i=0;i<b.shape[0];++i) out[i]={p[3*i],p[3*i+1],p[3*i+2]}; return out;
}

py::dict polyline_stats(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr, bool closed=true){
    auto p=read_points(arr); if(p.size()<2) throw std::runtime_error("need >=2 points");
    std::size_t m=closed?p.size():p.size()-1; std::vector<double> e(m); double L=0, mn=1e300, mx=0;
    V3 c{0,0,0}; for(auto q:p)c=add(c,q); c=mul(c,1.0/p.size());
    for(std::size_t i=0;i<m;++i){auto d=sub(p[(i+1)%p.size()],p[i]); e[i]=norm(d); L+=e[i]; mn=std::min(mn,e[i]); mx=std::max(mx,e[i]);}
    double mean=L/m, var=0; for(double x:e){double q=x-mean;var+=q*q;} var/=m;
    py::dict d; d["n_vertices"]=p.size(); d["length"]=L; d["edge_mean"]=mean; d["edge_min"]=mn; d["edge_max"]=mx; d["edge_cv"]=std::sqrt(var)/std::max(mean,1e-300);
    d["centroid"]=py::make_tuple(c.x,c.y,c.z); return d;
}

struct Seg {V3 m,dl;};
std::vector<Seg> segments(const std::vector<V3>& p){
    std::vector<Seg> s(p.size()); for(std::size_t i=0;i<p.size();++i){auto q=p[(i+1)%p.size()]; auto dl=sub(q,p[i]); s[i]={mul(add(q,p[i]),0.5),dl};} return s;
}

double interaction_energy(const py::array_t<double, py::array::c_style | py::array::forcecast>& aa,
                          const py::array_t<double, py::array::c_style | py::array::forcecast>& bb,
                          double core_radius=0.0, int threads=0){
    auto A=segments(read_points(aa)); auto B=segments(read_points(bb)); double a2=core_radius*core_radius; std::vector<double> partial(A.size(),0.0);
    {py::gil_scoped_release release; parallel_for(A.size(),threads,[&](std::size_t i){double s=0; for(auto &b:B){auto r=sub(A[i].m,b.m); s+=dot(A[i].dl,b.dl)/std::sqrt(dot(r,r)+a2);} partial[i]=s;});}
    double sum=0;for(double v:partial)sum+=v;return sum/(4.0*PI);
}

py::array_t<double> interaction_force_gradient(const py::array_t<double, py::array::c_style | py::array::forcecast>& aa,
                                               const py::array_t<double, py::array::c_style | py::array::forcecast>& bb,
                                               double core_radius=0.0, int threads=0){
    auto A=segments(read_points(aa)); auto B=segments(read_points(bb)); double a2=core_radius*core_radius; std::vector<V3> partial(A.size(),{0,0,0});
    {py::gil_scoped_release release; parallel_for(A.size(),threads,[&](std::size_t i){V3 f{0,0,0}; for(auto &b:B){auto r=sub(A[i].m,b.m); double den=std::pow(dot(r,r)+a2,1.5); f=add(f,mul(r,dot(A[i].dl,b.dl)/den));} partial[i]=f;});}
    V3 f{0,0,0};for(auto v:partial)f=add(f,v); f=mul(f,1.0/(4.0*PI)); py::array_t<double> out(3); auto o=out.mutable_unchecked<1>();o(0)=f.x;o(1)=f.y;o(2)=f.z;return out;
}

py::array_t<double> biot_savart(const py::array_t<double, py::array::c_style | py::array::forcecast>& source,
                                const py::array_t<double, py::array::c_style | py::array::forcecast>& query,
                                double core_radius=0.0, int threads=0){
    auto S=segments(read_points(source)); auto Q=read_points(query); double a2=core_radius*core_radius; py::array_t<double> out({(ssize_t)Q.size(),(ssize_t)3}); auto ob=out.request(); double* dst=static_cast<double*>(ob.ptr);
    {py::gil_scoped_release release; parallel_for(Q.size(),threads,[&](std::size_t i){V3 v{0,0,0}; for(auto &s:S){auto r=sub(Q[i],s.m); double den=std::pow(dot(r,r)+a2,1.5);v=add(v,mul(cross(s.dl,r),1.0/den));}v=mul(v,1.0/(4.0*PI));dst[3*i]=v.x;dst[3*i+1]=v.y;dst[3*i+2]=v.z;});}
    return out;
}

PYBIND11_MODULE(_native,m){
 m.doc()="Maxwell-SST DFC v0.2.0 native centerline kernels";
 m.def("polyline_stats",&polyline_stats,py::arg("points"),py::arg("closed")=true);
 m.def("interaction_energy",&interaction_energy,py::arg("a"),py::arg("b"),py::arg("core_radius")=0.0,py::arg("threads")=0);
 m.def("interaction_force_gradient",&interaction_force_gradient,py::arg("a"),py::arg("b"),py::arg("core_radius")=0.0,py::arg("threads")=0);
 m.def("biot_savart",&biot_savart,py::arg("source"),py::arg("query"),py::arg("core_radius")=0.0,py::arg("threads")=0);
}
