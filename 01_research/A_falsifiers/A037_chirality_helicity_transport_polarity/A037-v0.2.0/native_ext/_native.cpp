#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using Vec3 = std::array<double,3>;
static constexpr double PI = 3.141592653589793238462643383279502884;

static inline Vec3 add(const Vec3&a,const Vec3&b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static inline Vec3 sub(const Vec3&a,const Vec3&b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static inline Vec3 mul(double s,const Vec3&a){return {s*a[0],s*a[1],s*a[2]};}
static inline double dot(const Vec3&a,const Vec3&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static inline double norm2(const Vec3&a){return dot(a,a);}

struct Segment {
    Vec3 mid;
    Vec3 dl;
    std::size_t comp;
    std::size_t local;
    std::size_t ncomp;
};

static std::vector<Vec3> read_xyz(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr, bool allow_small=false) {
    auto b=arr.request();
    if(b.ndim!=2 || b.shape[1]!=3) throw std::runtime_error("Expected shape (N,3)");
    const py::ssize_t n=b.shape[0];
    if((!allow_small && n<4) || n<0) throw std::runtime_error("Point array too small");
    const double* p=static_cast<const double*>(b.ptr);
    std::vector<Vec3> out(static_cast<std::size_t>(n));
    for(py::ssize_t i=0;i<n;++i) out[static_cast<std::size_t>(i)]={p[3*i],p[3*i+1],p[3*i+2]};
    return out;
}

static std::vector<std::size_t> read_offsets(const py::array_t<std::int64_t, py::array::c_style | py::array::forcecast>& arr, std::size_t npts){
    auto b=arr.request();
    if(b.ndim!=1 || b.shape[0]<2) throw std::runtime_error("offsets must be 1D length >=2");
    const auto* p=static_cast<const std::int64_t*>(b.ptr);
    std::vector<std::size_t> o(static_cast<std::size_t>(b.shape[0]));
    for(py::ssize_t i=0;i<b.shape[0];++i){
        if(p[i]<0) throw std::runtime_error("negative offset");
        o[static_cast<std::size_t>(i)]=static_cast<std::size_t>(p[i]);
    }
    if(o.front()!=0 || o.back()!=npts) throw std::runtime_error("offsets must start at 0 and end at N");
    for(std::size_t c=0;c+1<o.size();++c){
        if(o[c+1]<=o[c] || o[c+1]-o[c]<4) throw std::runtime_error("each component needs >=4 points");
    }
    return o;
}

static std::vector<Segment> build_segments(const std::vector<Vec3>& x, const std::vector<std::size_t>& o){
    std::vector<Segment> segs; segs.reserve(x.size());
    for(std::size_t c=0;c+1<o.size();++c){
        const std::size_t a=o[c], b=o[c+1], nc=b-a;
        for(std::size_t j=0;j<nc;++j){
            const std::size_t i=a+j, k=a+((j+1)%nc);
            segs.push_back({mul(0.5,add(x[i],x[k])), sub(x[k],x[i]), c, j, nc});
        }
    }
    return segs;
}

static std::vector<Vec3> velocity_vec_multi(const std::vector<Vec3>& curve, const std::vector<std::size_t>& offsets,
                                             const std::vector<Vec3>& points, double core, double gamma){
    if(!(core>0.0)) throw std::runtime_error("core must be >0");
    const auto segs=build_segments(curve,offsets);
    const double pref=gamma/(4.0*PI), a2=core*core;
    std::vector<Vec3> out(points.size(),{0.0,0.0,0.0});
    bool parallel_ok=true;
#ifdef _OPENMP
    parallel_ok=!omp_in_parallel();
#endif
    #pragma omp parallel for if(parallel_ok && points.size()>32) schedule(static)
    for(py::ssize_t ii=0;ii<static_cast<py::ssize_t>(points.size());++ii){
        const Vec3 p=points[static_cast<std::size_t>(ii)];
        Vec3 v{0.0,0.0,0.0};
        for(const auto&s:segs){
            const Vec3 r=sub(p,s.mid);
            const double den=std::pow(norm2(r)+a2,1.5);
            const Vec3 q=cross(s.dl,r);
            v[0]+=q[0]/den; v[1]+=q[1]/den; v[2]+=q[2]/den;
        }
        out[static_cast<std::size_t>(ii)]=mul(pref,v);
    }
    return out;
}

static py::array_t<double> vec_to_array(const std::vector<Vec3>& v){
    py::array_t<double> out({static_cast<py::ssize_t>(v.size()),py::ssize_t(3)});
    auto b=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<static_cast<py::ssize_t>(v.size());++i)
        for(py::ssize_t k=0;k<3;++k) b(i,k)=v[static_cast<std::size_t>(i)][static_cast<std::size_t>(k)];
    return out;
}

static py::array_t<double> velocity_at_points_multi(
    const py::array_t<double,py::array::c_style|py::array::forcecast>& curve_arr,
    const py::array_t<std::int64_t,py::array::c_style|py::array::forcecast>& offsets_arr,
    const py::array_t<double,py::array::c_style|py::array::forcecast>& pts_arr,
    double core,double gamma){
    auto c=read_xyz(curve_arr); auto o=read_offsets(offsets_arr,c.size()); auto p=read_xyz(pts_arr,true);
    std::vector<Vec3> v; {py::gil_scoped_release release; v=velocity_vec_multi(c,o,p,core,gamma);} return vec_to_array(v);
}

static py::array_t<double> curve_velocity_multi(
    const py::array_t<double,py::array::c_style|py::array::forcecast>& curve_arr,
    const py::array_t<std::int64_t,py::array::c_style|py::array::forcecast>& offsets_arr,
    double core,double gamma){
    auto c=read_xyz(curve_arr); auto o=read_offsets(offsets_arr,c.size());
    std::vector<Vec3> v; {py::gil_scoped_release release; v=velocity_vec_multi(c,o,c,core,gamma);} return vec_to_array(v);
}

static py::array_t<double> transverse_jacobian_multi(
    const py::array_t<double,py::array::c_style|py::array::forcecast>& curve_arr,
    const py::array_t<std::int64_t,py::array::c_style|py::array::forcecast>& offsets_arr,
    const py::array_t<double,py::array::c_style|py::array::forcecast>& normal_arr,
    const py::array_t<double,py::array::c_style|py::array::forcecast>& binormal_arr,
    double core,double gamma,double eps){
    auto c=read_xyz(curve_arr), nrm=read_xyz(normal_arr), bin=read_xyz(binormal_arr); auto o=read_offsets(offsets_arr,c.size());
    if(c.size()!=nrm.size() || c.size()!=bin.size()) throw std::runtime_error("frame size mismatch");
    if(!(eps>0.0)) throw std::runtime_error("eps must be >0");
    const std::size_t n=c.size(), dim=2*n; std::vector<double> J(dim*dim,0.0);
    {py::gil_scoped_release release;
    #pragma omp parallel for schedule(dynamic)
    for(py::ssize_t cc=0;cc<static_cast<py::ssize_t>(dim);++cc){
        const std::size_t col=static_cast<std::size_t>(cc), p=col%n; const bool use_bin=col>=n;
        const Vec3 dir=use_bin?bin[p]:nrm[p]; auto cp=c,cm=c;
        cp[p]=add(cp[p],mul(eps,dir)); cm[p]=sub(cm[p],mul(eps,dir));
        auto vp=velocity_vec_multi(cp,o,cp,core,gamma); auto vm=velocity_vec_multi(cm,o,cm,core,gamma);
        for(std::size_t i=0;i<n;++i){
            const Vec3 dv=mul(1.0/(2.0*eps),sub(vp[i],vm[i]));
            J[i*dim+col]=dot(dv,nrm[i]); J[(n+i)*dim+col]=dot(dv,bin[i]);
        }
    }}
    py::array_t<double> out({static_cast<py::ssize_t>(dim),static_cast<py::ssize_t>(dim)}); auto b=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<static_cast<py::ssize_t>(dim);++i) for(py::ssize_t j=0;j<static_cast<py::ssize_t>(dim);++j)
        b(i,j)=J[static_cast<std::size_t>(i)*dim+static_cast<std::size_t>(j)];
    return out;
}

static double gauss_xi_multi(
    const py::array_t<double,py::array::c_style|py::array::forcecast>& curve_arr,
    const py::array_t<std::int64_t,py::array::c_style|py::array::forcecast>& offsets_arr,
    double eps){
    auto c=read_xyz(curve_arr); auto o=read_offsets(offsets_arr,c.size()); auto segs=build_segments(c,o);
    const double e2=eps*eps; double sum=0.0;
    #pragma omp parallel for reduction(+:sum) schedule(static)
    for(py::ssize_t ii=0;ii<static_cast<py::ssize_t>(segs.size());++ii){
        const auto&i=segs[static_cast<std::size_t>(ii)];
        for(std::size_t jj=static_cast<std::size_t>(ii)+1;jj<segs.size();++jj){
            const auto&j=segs[jj];
            if(i.comp==j.comp){
                const std::size_t d=(i.local>j.local)?i.local-j.local:j.local-i.local;
                if(d==1 || d==i.ncomp-1) continue;
            }
            const Vec3 r=sub(i.mid,j.mid); const double den=std::pow(norm2(r)+e2,1.5);
            sum += 2.0*dot(cross(i.dl,j.dl),r)/den;
        }
    }
    return sum/(4.0*PI);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST v0.2 multi-component finite-core kernels";
    m.def("velocity_at_points_multi",&velocity_at_points_multi,py::arg("curve"),py::arg("offsets"),py::arg("points"),py::arg("core"),py::arg("gamma")=1.0);
    m.def("curve_velocity_multi",&curve_velocity_multi,py::arg("curve"),py::arg("offsets"),py::arg("core"),py::arg("gamma")=1.0);
    m.def("transverse_jacobian_multi",&transverse_jacobian_multi,py::arg("curve"),py::arg("offsets"),py::arg("normal"),py::arg("binormal"),py::arg("core"),py::arg("gamma")=1.0,py::arg("eps")=1e-5);
    m.def("gauss_xi_multi",&gauss_xi_multi,py::arg("curve"),py::arg("offsets"),py::arg("eps")=1e-9);
}
