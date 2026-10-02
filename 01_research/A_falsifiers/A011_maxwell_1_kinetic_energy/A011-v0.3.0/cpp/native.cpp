#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;
using Arr2 = py::array_t<double, py::array::c_style | py::array::forcecast>;

namespace {
constexpr double PI = 3.141592653589793238462643383279502884;

struct V3 { double x, y, z; };
inline V3 add(V3 a, V3 b){ return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline V3 sub(V3 a, V3 b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline V3 mul(V3 a, double s){ return {a.x*s,a.y*s,a.z*s}; }
inline double dot(V3 a,V3 b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
inline V3 cross(V3 a,V3 b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline double norm2(V3 a){ return dot(a,a); }
inline double norm(V3 a){ return std::sqrt(norm2(a)); }

std::vector<V3> read_points(const Arr2& a) {
    auto b = a.request();
    if (b.ndim != 2 || b.shape[1] != 3) throw std::runtime_error("points must have shape (N,3)");
    auto* p = static_cast<double*>(b.ptr);
    std::vector<V3> out(static_cast<size_t>(b.shape[0]));
    for (ssize_t i=0;i<b.shape[0];++i) out[static_cast<size_t>(i)] = {p[3*i],p[3*i+1],p[3*i+2]};
    return out;
}

py::array_t<double> vector_to_array(const std::vector<double>& v, ssize_t nrow, ssize_t ncol=1) {
    if (ncol == 1) {
        py::array_t<double> out(nrow);
        std::memcpy(out.mutable_data(), v.data(), sizeof(double)*v.size());
        return out;
    }
    py::array_t<double> out({nrow,ncol});
    std::memcpy(out.mutable_data(), v.data(), sizeof(double)*v.size());
    return out;
}

double segseg_dist2(V3 p1, V3 q1, V3 p2, V3 q2) {
    const double EPS = 1e-30;
    V3 d1 = sub(q1,p1), d2 = sub(q2,p2), r = sub(p1,p2);
    double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
    double s=0.0,t=0.0;
    if (a <= EPS && e <= EPS) return norm2(r);
    if (a <= EPS) {
        s=0.0; t=std::clamp(f/e,0.0,1.0);
    } else {
        double c=dot(d1,r);
        if (e <= EPS) { t=0.0; s=std::clamp(-c/a,0.0,1.0); }
        else {
            double b=dot(d1,d2), denom=a*e-b*b;
            if (std::abs(denom) > EPS) s=std::clamp((b*f-c*e)/denom,0.0,1.0);
            else s=0.0;
            t=(b*s+f)/e;
            if (t<0.0){ t=0.0; s=std::clamp(-c/a,0.0,1.0); }
            else if(t>1.0){ t=1.0; s=std::clamp((b-c)/a,0.0,1.0); }
        }
    }
    V3 c1=add(p1,mul(d1,s)), c2=add(p2,mul(d2,t));
    return norm2(sub(c1,c2));
}
}

py::array_t<double> segment_lengths(const Arr2& points, bool closed=true) {
    auto p = read_points(points);
    const size_t n=p.size();
    const size_t m = closed ? n : (n>0?n-1:0);
    std::vector<double> out(m,0.0);
    {
        py::gil_scoped_release release;
        for(size_t i=0;i<m;++i){ size_t j=(i+1)%n; out[i]=norm(sub(p[j],p[i])); }
    }
    return vector_to_array(out, static_cast<ssize_t>(m));
}

py::array_t<double> biot_savart_velocity(const Arr2& source, const Arr2& evaluation,
                                         double gamma=1.0, double core_radius=1e-3,
                                         bool source_closed=true) {
    auto s=read_points(source), e=read_points(evaluation);
    if(s.size()<2) throw std::runtime_error("source requires >=2 points");
    if(core_radius < 0) throw std::runtime_error("core_radius must be >=0");
    const size_t ns=s.size(), ne=e.size(), nseg=source_closed?ns:ns-1;
    std::vector<double> out(ne*3,0.0);
    const double pref=gamma/(4.0*PI), a2=core_radius*core_radius;
    {
        py::gil_scoped_release release;
        for(size_t k=0;k<ne;++k){
            V3 vv{0,0,0};
            for(size_t i=0;i<nseg;++i){
                size_t j=(i+1)%ns;
                V3 dl=sub(s[j],s[i]);
                V3 mid=mul(add(s[i],s[j]),0.5);
                V3 r=sub(e[k],mid);
                double den=std::pow(norm2(r)+a2,1.5);
                if(den>1e-300) vv=add(vv,mul(cross(dl,r),pref/den));
            }
            out[3*k]=vv.x; out[3*k+1]=vv.y; out[3*k+2]=vv.z;
        }
    }
    return vector_to_array(out, static_cast<ssize_t>(ne), 3);
}

double writhe_midpoint(const Arr2& points, bool closed=true) {
    auto p=read_points(points);
    if(p.size()<4) return 0.0;
    const size_t n=p.size(), nseg=closed?n:n-1;
    std::vector<V3> dl(nseg), mid(nseg);
    for(size_t i=0;i<nseg;++i){ size_t j=(i+1)%n; dl[i]=sub(p[j],p[i]); mid[i]=mul(add(p[i],p[j]),0.5); }
    double sum=0.0;
    {
        py::gil_scoped_release release;
        for(size_t i=0;i<nseg;++i){
            for(size_t j=i+1;j<nseg;++j){
                if(j==i+1) continue;
                if(closed && i==0 && j==nseg-1) continue;
                V3 r=sub(mid[i],mid[j]);
                double r2=norm2(r);
                if(r2<=1e-24) continue;
                sum += dot(r,cross(dl[i],dl[j]))/(r2*std::sqrt(r2));
            }
        }
    }
    return sum/(2.0*PI); // i<j; the symmetric double integral contributes twice.
}

double min_segment_distance(const Arr2& a, const Arr2& b, bool closed_a=true, bool closed_b=true) {
    auto A=read_points(a), B=read_points(b);
    if(A.size()<2 || B.size()<2) return std::numeric_limits<double>::quiet_NaN();
    const size_t na=A.size(), nb=B.size(), sa=closed_a?na:na-1, sb=closed_b?nb:nb-1;
    double best=std::numeric_limits<double>::infinity();
    {
        py::gil_scoped_release release;
        for(size_t i=0;i<sa;++i){
            V3 p=A[i], q=A[(i+1)%na];
            for(size_t j=0;j<sb;++j){
                V3 u=B[j], v=B[(j+1)%nb];
                double d2=segseg_dist2(p,q,u,v);
                if(d2<best) best=d2;
            }
        }
    }
    return std::sqrt(best);
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Fast geometry and regularized Biot-Savart kernels for Maxwell-SST Kinetic Falsifier v0.3.0";
    m.def("segment_lengths", &segment_lengths, py::arg("points"), py::arg("closed")=true);
    m.def("biot_savart_velocity", &biot_savart_velocity,
          py::arg("source"), py::arg("evaluation"), py::arg("gamma")=1.0,
          py::arg("core_radius")=1e-3, py::arg("source_closed")=true);
    m.def("writhe_midpoint", &writhe_midpoint, py::arg("points"), py::arg("closed")=true);
    m.def("min_segment_distance", &min_segment_distance,
          py::arg("a"), py::arg("b"), py::arg("closed_a")=true, py::arg("closed_b")=true);
    m.def("backend_version", [](){ return std::string("0.3.0-cpp17"); });
}
