#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

struct V3 { double x,y,z; };
inline V3 sub(const V3&a,const V3&b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline V3 add(const V3&a,const V3&b){ return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline V3 mul(const V3&a,double s){ return {a.x*s,a.y*s,a.z*s}; }
inline V3 cross(const V3&a,const V3&b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline double norm2(const V3&a){ return a.x*a.x+a.y*a.y+a.z*a.z; }

struct Seg { V3 a,b,mid,ds; };

static std::vector<Seg> make_segments(const double* p, py::ssize_t n, const std::vector<int>& offsets){
    if (offsets.size() < 2 || offsets.front()!=0 || offsets.back()!=n) throw std::runtime_error("invalid component offsets");
    std::vector<Seg> segs;
    segs.reserve((size_t)n);
    for(size_t c=0;c+1<offsets.size();++c){
        int lo=offsets[c], hi=offsets[c+1];
        if(hi-lo<3) throw std::runtime_error("each component needs at least 3 points");
        for(int j=lo;j<hi;++j){
            int k = (j+1<hi)? j+1 : lo;
            V3 a{p[3*j],p[3*j+1],p[3*j+2]};
            V3 b{p[3*k],p[3*k+1],p[3*k+2]};
            V3 ds=sub(b,a);
            V3 mid=mul(add(a,b),0.5);
            segs.push_back({a,b,mid,ds});
        }
    }
    return segs;
}

static py::array_t<double> velocity_impl(
    py::array_t<double, py::array::c_style | py::array::forcecast> targets,
    py::array_t<double, py::array::c_style | py::array::forcecast> curve,
    const std::vector<int>& offsets,
    double core_radius,
    double circulation,
    int threads)
{
    if(core_radius<=0.0) throw std::runtime_error("core_radius must be >0");
    auto tb=targets.request(); auto cb=curve.request();
    if(tb.ndim!=2 || tb.shape[1]!=3 || cb.ndim!=2 || cb.shape[1]!=3) throw std::runtime_error("arrays must have shape (N,3)");
    py::ssize_t nt=tb.shape[0], nc=cb.shape[0];
    auto segs=make_segments((const double*)cb.ptr,nc,offsets);
    py::array_t<double> out({nt,(py::ssize_t)3}); auto ob=out.request();
    const double* tp=(const double*)tb.ptr; double* op=(double*)ob.ptr;
    double a2=core_radius*core_radius;
    double pref=circulation/(4.0*PI);
#ifdef _OPENMP
    if(threads>0) omp_set_num_threads(threads);
#pragma omp parallel for schedule(static)
#endif
    for(py::ssize_t i=0;i<nt;++i){
        V3 x{tp[3*i],tp[3*i+1],tp[3*i+2]};
        V3 v{0,0,0};
        for(const auto& s:segs){
            V3 r=sub(x,s.mid);
            double d2=norm2(r)+a2;
            double inv=1.0/(d2*std::sqrt(d2));
            V3 c=cross(s.ds,r);
            v.x += pref*c.x*inv; v.y += pref*c.y*inv; v.z += pref*c.z*inv;
        }
        op[3*i]=v.x; op[3*i+1]=v.y; op[3*i+2]=v.z;
    }
    return out;
}

static py::array_t<double> induced_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> curve,
    const std::vector<int>& offsets,
    double core_radius,
    double circulation,
    int threads)
{
    return velocity_impl(curve,curve,offsets,core_radius,circulation,threads);
}

static py::array_t<double> velocity_at_points(
    py::array_t<double, py::array::c_style | py::array::forcecast> targets,
    py::array_t<double, py::array::c_style | py::array::forcecast> curve,
    const std::vector<int>& offsets,
    double core_radius,
    double circulation,
    int threads)
{
    return velocity_impl(targets,curve,offsets,core_radius,circulation,threads);
}

static std::string backend_info(){
#ifdef _OPENMP
    return std::string("cpp17-pybind11-openmp");
#else
    return std::string("cpp17-pybind11");
#endif
}

PYBIND11_MODULE(_native,m){
    m.doc()="Kelvin/Kirchhoff SST regularized Biot-Savart kernels";
    m.def("induced_velocity", &induced_velocity, py::arg("curve"), py::arg("offsets"), py::arg("core_radius"), py::arg("circulation")=1.0, py::arg("threads")=0);
    m.def("velocity_at_points", &velocity_at_points, py::arg("targets"), py::arg("curve"), py::arg("offsets"), py::arg("core_radius"), py::arg("circulation")=1.0, py::arg("threads")=0);
    m.def("backend_info", &backend_info);
}
