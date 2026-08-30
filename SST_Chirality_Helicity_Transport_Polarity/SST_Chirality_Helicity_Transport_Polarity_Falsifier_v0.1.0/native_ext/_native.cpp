#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <array>
#include <stdexcept>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using Vec3 = std::array<double, 3>;
static constexpr double PI = 3.141592653589793238462643383279502884;

static inline Vec3 add(const Vec3&a,const Vec3&b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static inline Vec3 sub(const Vec3&a,const Vec3&b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static inline Vec3 mul(double s,const Vec3&a){return {s*a[0],s*a[1],s*a[2]};}
static inline double dot(const Vec3&a,const Vec3&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static inline double norm2(const Vec3&a){return dot(a,a);}

static std::vector<Vec3> read_xyz(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr) {
    auto b = arr.request();
    if (b.ndim != 2 || b.shape[1] != 3) throw std::runtime_error("Expected shape (N,3)");
    const py::ssize_t n = b.shape[0];
    if (n < 4) throw std::runtime_error("Curve/point array too small");
    const double* p = static_cast<const double*>(b.ptr);
    std::vector<Vec3> out(static_cast<size_t>(n));
    for (py::ssize_t i=0;i<n;++i) out[static_cast<size_t>(i)]={p[3*i],p[3*i+1],p[3*i+2]};
    return out;
}

static std::vector<Vec3> read_points_allow_small(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr) {
    auto b = arr.request();
    if (b.ndim != 2 || b.shape[1] != 3) throw std::runtime_error("Expected shape (M,3)");
    const py::ssize_t n = b.shape[0];
    const double* p = static_cast<const double*>(b.ptr);
    std::vector<Vec3> out(static_cast<size_t>(n));
    for (py::ssize_t i=0;i<n;++i) out[static_cast<size_t>(i)]={p[3*i],p[3*i+1],p[3*i+2]};
    return out;
}

static std::vector<Vec3> velocity_points_vec(const std::vector<Vec3>& curve, const std::vector<Vec3>& points, double core, double gamma) {
    const size_t n=curve.size(), m=points.size();
    if (!(core > 0.0)) throw std::runtime_error("core must be > 0");
    const double pref = gamma/(4.0*PI);
    const double a2 = core*core;
    std::vector<Vec3> mids(n), dls(n), out(m, {0.0,0.0,0.0});
    for(size_t j=0;j<n;++j){
        const Vec3 &a=curve[j], &b=curve[(j+1)%n];
        dls[j]=sub(b,a); mids[j]=mul(0.5,add(a,b));
    }
    bool parallel_ok = true;
#ifdef _OPENMP
    parallel_ok = !omp_in_parallel();
#endif
    #pragma omp parallel for if(parallel_ok && m > 64)
    for(py::ssize_t ii=0; ii<static_cast<py::ssize_t>(m); ++ii){
        Vec3 v{0.0,0.0,0.0};
        const Vec3 x=points[static_cast<size_t>(ii)];
        for(size_t j=0;j<n;++j){
            Vec3 r=sub(x,mids[j]);
            double d=std::pow(norm2(r)+a2,1.5);
            Vec3 c=cross(dls[j],r);
            v[0]+=c[0]/d; v[1]+=c[1]/d; v[2]+=c[2]/d;
        }
        out[static_cast<size_t>(ii)] = mul(pref,v);
    }
    return out;
}

static py::array_t<double> vec_to_array(const std::vector<Vec3>& v){
    py::array_t<double> out({static_cast<py::ssize_t>(v.size()), py::ssize_t(3)});
    auto b=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<static_cast<py::ssize_t>(v.size());++i)
        for(py::ssize_t k=0;k<3;++k) b(i,k)=v[static_cast<size_t>(i)][static_cast<size_t>(k)];
    return out;
}

static py::array_t<double> velocity_at_points(
    const py::array_t<double, py::array::c_style | py::array::forcecast>& curve_arr,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& pts_arr,
    double core, double gamma){
    auto c=read_xyz(curve_arr); auto p=read_points_allow_small(pts_arr);
    std::vector<Vec3> v;
    { py::gil_scoped_release release; v=velocity_points_vec(c,p,core,gamma); }
    return vec_to_array(v);
}

static py::array_t<double> curve_velocity(
    const py::array_t<double, py::array::c_style | py::array::forcecast>& curve_arr,
    double core, double gamma){
    auto c=read_xyz(curve_arr);
    std::vector<Vec3> v;
    { py::gil_scoped_release release; v=velocity_points_vec(c,c,core,gamma); }
    return vec_to_array(v);
}

static py::array_t<double> transverse_jacobian(
    const py::array_t<double, py::array::c_style | py::array::forcecast>& curve_arr,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& normal_arr,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& binormal_arr,
    double core, double gamma, double eps){
    auto c=read_xyz(curve_arr), nrm=read_xyz(normal_arr), bin=read_xyz(binormal_arr);
    if(c.size()!=nrm.size() || c.size()!=bin.size()) throw std::runtime_error("frame size mismatch");
    if(!(eps>0.0)) throw std::runtime_error("eps must be >0");
    const size_t n=c.size(); const size_t dim=2*n;
    std::vector<double> J(dim*dim,0.0);
    { py::gil_scoped_release release;
    #pragma omp parallel for schedule(dynamic)
    for(py::ssize_t col=0; col<static_cast<py::ssize_t>(dim); ++col){
        size_t p=static_cast<size_t>(col)%n;
        bool use_bin = static_cast<size_t>(col)>=n;
        const Vec3 dir = use_bin ? bin[p] : nrm[p];
        auto cp=c, cm=c;
        cp[p]=add(cp[p],mul(eps,dir));
        cm[p]=sub(cm[p],mul(eps,dir));
        auto vp=velocity_points_vec(cp,cp,core,gamma);
        auto vm=velocity_points_vec(cm,cm,core,gamma);
        for(size_t i=0;i<n;++i){
            Vec3 dv=mul(1.0/(2.0*eps), sub(vp[i],vm[i]));
            J[i*dim+static_cast<size_t>(col)] = dot(dv,nrm[i]);
            J[(n+i)*dim+static_cast<size_t>(col)] = dot(dv,bin[i]);
        }
    }
    }
    py::array_t<double> out({static_cast<py::ssize_t>(dim),static_cast<py::ssize_t>(dim)});
    auto b=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<static_cast<py::ssize_t>(dim);++i)
        for(py::ssize_t j=0;j<static_cast<py::ssize_t>(dim);++j)
            b(i,j)=J[static_cast<size_t>(i)*dim+static_cast<size_t>(j)];
    return out;
}

static double writhe(const py::array_t<double, py::array::c_style | py::array::forcecast>& curve_arr, double eps){
    auto c=read_xyz(curve_arr); const size_t n=c.size();
    std::vector<Vec3> mid(n), dl(n);
    for(size_t i=0;i<n;++i){ const auto&a=c[i]; const auto&b=c[(i+1)%n]; dl[i]=sub(b,a); mid[i]=mul(0.5,add(a,b)); }
    double sum=0.0; const double e2=eps*eps;
    #pragma omp parallel for reduction(+:sum) schedule(static)
    for(py::ssize_t ii=0; ii<static_cast<py::ssize_t>(n); ++ii){
        size_t i=static_cast<size_t>(ii);
        for(size_t j=i+1;j<n;++j){
            if(j==i || j==(i+1)%n || i==(j+1)%n) continue;
            Vec3 r=sub(mid[i],mid[j]);
            double d=std::pow(norm2(r)+e2,1.5);
            sum += 2.0*dot(cross(dl[i],dl[j]),r)/d;
        }
    }
    return sum/(4.0*PI);
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST chirality-helicity falsifier native finite-core kernels";
    m.def("velocity_at_points", &velocity_at_points, py::arg("curve"),py::arg("points"),py::arg("core"),py::arg("gamma")=1.0);
    m.def("curve_velocity", &curve_velocity, py::arg("curve"),py::arg("core"),py::arg("gamma")=1.0);
    m.def("transverse_jacobian", &transverse_jacobian, py::arg("curve"),py::arg("normal"),py::arg("binormal"),py::arg("core"),py::arg("gamma")=1.0,py::arg("eps")=1e-5);
    m.def("writhe", &writhe, py::arg("curve"),py::arg("eps")=1e-9);
}
