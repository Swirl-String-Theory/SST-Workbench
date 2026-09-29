#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstddef>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

static py::array_t<double> biot_savart_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> samples,
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_a,
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_b,
    double gamma, double core_radius, int threads = 0)
{
    auto s=samples.unchecked<2>(); auto a=seg_a.unchecked<2>(); auto b=seg_b.unchecked<2>();
    if(s.shape(1)!=3||a.shape(1)!=3||b.shape(1)!=3||a.shape(0)!=b.shape(0)) throw std::runtime_error("Nx3 arrays required");
    const py::ssize_t n=s.shape(0), m=a.shape(0);
    py::array_t<double> out({n,py::ssize_t(3)}); auto o=out.mutable_unchecked<2>();
    const double eps2=core_radius*core_radius, pref=gamma/(4.0*PI);
#ifdef _OPENMP
    if(threads>0) omp_set_num_threads(threads);
#pragma omp parallel for schedule(static)
#endif
    for(py::ssize_t i=0;i<n;++i){
        double vx=0,vy=0,vz=0; const double sx=s(i,0),sy=s(i,1),sz=s(i,2);
        for(py::ssize_t j=0;j<m;++j){
            const double dlx=b(j,0)-a(j,0), dly=b(j,1)-a(j,1), dlz=b(j,2)-a(j,2);
            const double mx=.5*(a(j,0)+b(j,0)), my=.5*(a(j,1)+b(j,1)), mz=.5*(a(j,2)+b(j,2));
            const double rx=sx-mx, ry=sy-my, rz=sz-mz;
            const double r2=rx*rx+ry*ry+rz*rz+eps2, inv=1.0/(r2*std::sqrt(r2));
            vx+=(dly*rz-dlz*ry)*inv; vy+=(dlz*rx-dlx*rz)*inv; vz+=(dlx*ry-dly*rx)*inv;
        }
        o(i,0)=pref*vx; o(i,1)=pref*vy; o(i,2)=pref*vz;
    }
    return out;
}

static double circulation_midpoint(
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_a,
    py::array_t<double, py::array::c_style | py::array::forcecast> seg_b,
    py::array_t<double, py::array::c_style | py::array::forcecast> probe,
    double gamma, double core_radius, int threads = 0)
{
    auto a=seg_a.unchecked<2>(); auto b=seg_b.unchecked<2>(); auto p=probe.unchecked<2>();
    if(a.shape(1)!=3||b.shape(1)!=3||p.shape(1)!=3||a.shape(0)!=b.shape(0)||p.shape(0)<3) throw std::runtime_error("Nx3 arrays required");
    const py::ssize_t ns=a.shape(0), np=p.shape(0); const double eps2=core_radius*core_radius, pref=gamma/(4.0*PI);
    double total=0.0;
#ifdef _OPENMP
    if(threads>0) omp_set_num_threads(threads);
#pragma omp parallel for reduction(+:total) schedule(static)
#endif
    for(py::ssize_t i=0;i<np;++i){
        const py::ssize_t k=(i+1)%np;
        const double dx=p(k,0)-p(i,0), dy=p(k,1)-p(i,1), dz=p(k,2)-p(i,2);
        const double sx=.5*(p(i,0)+p(k,0)), sy=.5*(p(i,1)+p(k,1)), sz=.5*(p(i,2)+p(k,2));
        double vx=0,vy=0,vz=0;
        for(py::ssize_t j=0;j<ns;++j){
            const double dlx=b(j,0)-a(j,0), dly=b(j,1)-a(j,1), dlz=b(j,2)-a(j,2);
            const double mx=.5*(a(j,0)+b(j,0)), my=.5*(a(j,1)+b(j,1)), mz=.5*(a(j,2)+b(j,2));
            const double rx=sx-mx, ry=sy-my, rz=sz-mz;
            const double r2=rx*rx+ry*ry+rz*rz+eps2, inv=1.0/(r2*std::sqrt(r2));
            vx+=(dly*rz-dlz*ry)*inv; vy+=(dlz*rx-dlx*rz)*inv; vz+=(dlx*ry-dly*rx)*inv;
        }
        total += pref*(vx*dx+vy*dy+vz*dz);
    }
    return total;
}

static py::dict build_info(){
    py::dict d;
#ifdef _OPENMP
    d["openmp"]=true; d["openmp_max_threads"]=omp_get_max_threads();
#else
    d["openmp"]=false; d["openmp_max_threads"]=1;
#endif
    d["kernels"]="regularized_midpoint_biot_savart,circulation_midpoint";
    d["cpp_standard"]="c++17"; d["protocol"]="3_Maxwell_v0.3.0"; return d;
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST Maxwell-3 v0.3.0 independent Biot-Savart/circulation kernels";
    m.def("biot_savart_velocity",&biot_savart_velocity,py::arg("samples"),py::arg("seg_a"),py::arg("seg_b"),py::arg("gamma"),py::arg("core_radius"),py::arg("threads")=0);
    m.def("circulation_midpoint",&circulation_midpoint,py::arg("seg_a"),py::arg("seg_b"),py::arg("probe"),py::arg("gamma"),py::arg("core_radius")=0.0,py::arg("threads")=0);
    m.def("build_info",&build_info);
}
