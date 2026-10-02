#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

struct Vec3 { double x,y,z; };
inline Vec3 add(Vec3 a, Vec3 b){ return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline Vec3 sub(Vec3 a, Vec3 b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline Vec3 mul(double s, Vec3 a){ return {s*a.x,s*a.y,s*a.z}; }
inline double dot(Vec3 a, Vec3 b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
inline Vec3 cross(Vec3 a, Vec3 b){ return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline double norm(Vec3 a){ return std::sqrt(dot(a,a)); }

static std::vector<Vec3> read_points(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr){
    if(arr.ndim()!=2 || arr.shape(1)!=3) throw std::runtime_error("points must have shape (N,3)");
    auto r=arr.unchecked<2>();
    std::vector<Vec3> p((size_t)arr.shape(0));
    for(py::ssize_t i=0;i<arr.shape(0);++i) p[(size_t)i]={r(i,0),r(i,1),r(i,2)};
    return p;
}
static Vec3 read_vec3(const py::array_t<double, py::array::c_style | py::array::forcecast>& a){
    if(a.size()!=3) throw std::runtime_error("vector must have three components");
    auto r=a.unchecked<1>(); return {r(0),r(1),r(2)};
}
static py::array_t<double> write_points(const std::vector<Vec3>& p){
    py::array::ShapeContainer shape{static_cast<py::ssize_t>(p.size()), static_cast<py::ssize_t>(3)};
    py::array_t<double> out(shape); auto w=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<(py::ssize_t)p.size();++i){ w(i,0)=p[(size_t)i].x; w(i,1)=p[(size_t)i].y; w(i,2)=p[(size_t)i].z; }
    return out;
}

static std::vector<Vec3> velocity_cpp(const std::vector<Vec3>& p,double core,double gamma,Vec3 u){
    const size_t n=p.size(); std::vector<Vec3> dl(n),mid(n),out(n);
    for(size_t j=0;j<n;++j){ size_t k=(j+1)%n; dl[j]=sub(p[k],p[j]); mid[j]=mul(0.5,add(p[k],p[j])); }
    const double pref=gamma/(4.0*PI); const double a2=core*core;
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for(long long ii=0; ii<(long long)n; ++ii){
        size_t i=(size_t)ii; Vec3 s{0,0,0};
        for(size_t j=0;j<n;++j){
            Vec3 r=sub(p[i],mid[j]); double r2=dot(r,r)+a2; double den=r2*std::sqrt(r2);
            Vec3 c=cross(dl[j],r); s.x+=c.x/den; s.y+=c.y/den; s.z+=c.z/den;
        }
        out[i]={pref*s.x+u.x,pref*s.y+u.y,pref*s.z+u.z};
    }
    return out;
}

py::array_t<double> biot_savart_velocity(py::array_t<double, py::array::c_style | py::array::forcecast> arr,double core,double gamma,
                                         py::array_t<double, py::array::c_style | py::array::forcecast> uniform){
    return write_points(velocity_cpp(read_points(arr),core,gamma,read_vec3(uniform)));
}

double filament_energy(py::array_t<double, py::array::c_style | py::array::forcecast> arr,double core,double rho,double gamma){
    auto p=read_points(arr); size_t n=p.size(); std::vector<Vec3> dl(n),mid(n);
    for(size_t i=0;i<n;++i){size_t k=(i+1)%n; dl[i]=sub(p[k],p[i]); mid[i]=mul(0.5,add(p[k],p[i]));}
    double sum=0.0; double a2=core*core;
    #ifdef _OPENMP
    #pragma omp parallel for reduction(+:sum) schedule(static)
    #endif
    for(long long ii=0;ii<(long long)n;++ii){ size_t i=(size_t)ii; double local=0.0;
        for(size_t j=0;j<n;++j){ Vec3 r=sub(mid[i],mid[j]); double den=std::sqrt(dot(r,r)+a2); local += dot(dl[i],dl[j])/den; }
        sum += local;
    }
    return rho*gamma*gamma/(8.0*PI)*sum;
}

py::array_t<double> impulse(py::array_t<double, py::array::c_style | py::array::forcecast> arr,double rho,double gamma){
    auto p=read_points(arr); Vec3 s{0,0,0};
    for(size_t i=0;i<p.size();++i){ Vec3 c=cross(p[i],p[(i+1)%p.size()]); s=add(s,c); }
    s=mul(0.5*rho*gamma,s);
    py::array::ShapeContainer shape{static_cast<py::ssize_t>(3)}; py::array_t<double> out(shape); auto w=out.mutable_unchecked<1>();
    w(0)=s.x;w(1)=s.y;w(2)=s.z;return out;
}

py::array_t<double> curvature(py::array_t<double, py::array::c_style | py::array::forcecast> arr){
    auto p=read_points(arr); size_t n=p.size(); py::array::ShapeContainer shape{static_cast<py::ssize_t>(n)}; py::array_t<double> out(shape); auto w=out.mutable_unchecked<1>();
    for(size_t i=0;i<n;++i){ Vec3 pm=p[(i+n-1)%n], pc=p[i], pp=p[(i+1)%n]; Vec3 a=sub(pc,pm), b=sub(pp,pc), c=sub(pp,pm); double den=norm(a)*norm(b)*norm(c); w((py::ssize_t)i)=den>1e-300 ? 2.0*norm(cross(a,b))/den : 0.0; }
    return out;
}

py::array_t<double> rk4_step(py::array_t<double, py::array::c_style | py::array::forcecast> arr,double dt,double core,double gamma,
                             py::array_t<double, py::array::c_style | py::array::forcecast> uniform){
    auto p=read_points(arr); Vec3 u=read_vec3(uniform); size_t n=p.size();
    auto k1=velocity_cpp(p,core,gamma,u); std::vector<Vec3> q(n);
    for(size_t i=0;i<n;++i) q[i]=add(p[i],mul(0.5*dt,k1[i]));
    auto k2=velocity_cpp(q,core,gamma,u);
    for(size_t i=0;i<n;++i) q[i]=add(p[i],mul(0.5*dt,k2[i]));
    auto k3=velocity_cpp(q,core,gamma,u);
    for(size_t i=0;i<n;++i) q[i]=add(p[i],mul(dt,k3[i]));
    auto k4=velocity_cpp(q,core,gamma,u);
    for(size_t i=0;i<n;++i){ Vec3 s=add(add(k1[i],mul(2.0,k2[i])),add(mul(2.0,k3[i]),k4[i])); q[i]=add(p[i],mul(dt/6.0,s)); }
    return write_points(q);
}

int set_threads(int n){
#ifdef _OPENMP
    if(n>0) omp_set_num_threads(n); return omp_get_max_threads();
#else
    return 1;
#endif
}
int native_threads(){
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}

PYBIND11_MODULE(_native,m){
    m.doc()="Einstein–SST blind falsifier native kernels";
    m.def("biot_savart_velocity",&biot_savart_velocity);
    m.def("filament_energy",&filament_energy);
    m.def("impulse",&impulse);
    m.def("curvature",&curvature);
    m.def("rk4_step",&rk4_step);
    m.def("set_threads",&set_threads);
    m.def("native_threads",&native_threads);
}
