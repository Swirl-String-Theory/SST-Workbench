#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
#ifdef SST_HAVE_SYCL
#include <sycl/sycl.hpp>
#endif
namespace py=pybind11;
namespace {
constexpr double PI=3.141592653589793238462643383279502884;
double g_last_ms=0.0; std::string g_last_backend="serial";
struct Timer{std::chrono::steady_clock::time_point t0{std::chrono::steady_clock::now()};void stop(const std::string& b){auto t1=std::chrono::steady_clock::now();g_last_ms=std::chrono::duration<double,std::milli>(t1-t0).count();g_last_backend=b;}};
const double* ptr_nx3(py::array_t<double,py::array::c_style|py::array::forcecast>& a,py::ssize_t& n){auto b=a.request();if(b.ndim!=2||b.shape[1]!=3)throw std::runtime_error("array must be Nx3");n=b.shape[0];return static_cast<const double*>(b.ptr);} 
std::string host_backend(){
#ifdef _OPENMP
return "openmp";
#else
return "serial";
#endif
}
void biot_one(const double* p,py::ssize_t n,const double* x,double scale,double a2,double* o){double vx=0,vy=0,vz=0;for(py::ssize_t s=0;s<n;++s){py::ssize_t t=(s+1)%n;double ax=p[3*s],ay=p[3*s+1],az=p[3*s+2],bx=p[3*t],by=p[3*t+1],bz=p[3*t+2];double dx=bx-ax,dy=by-ay,dz=bz-az,mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz);double rx=x[0]-mx,ry=x[1]-my,rz=x[2]-mz,D=rx*rx+ry*ry+rz*rz+a2,inv=1.0/(D*std::sqrt(D));vx+=scale*(dy*rz-dz*ry)*inv;vy+=scale*(dz*rx-dx*rz)*inv;vz+=scale*(dx*ry-dy*rx)*inv;}o[0]=vx;o[1]=vy;o[2]=vz;}
void biot_host(const double* p,py::ssize_t n,const double* q,py::ssize_t m,double gamma,double core,double* v){double scale=gamma/(4*PI),a2=core*core;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if(m>32)
#endif
for(long long i=0;i<m;++i)biot_one(p,n,q+3*i,scale,a2,v+3*i);}
double hamiltonian_host(const double* p,py::ssize_t n,double rho,double gamma,double core){double a2=core*core,total=0.0;
#ifdef _OPENMP
#pragma omp parallel for reduction(+:total) schedule(static) if(n>32)
#endif
for(long long ii=0;ii<n;++ii){size_t i=(size_t)ii,ip=(i+1)%n;double aix=p[3*i],aiy=p[3*i+1],aiz=p[3*i+2],bix=p[3*ip],biy=p[3*ip+1],biz=p[3*ip+2];double dix=bix-aix,diy=biy-aiy,diz=biz-aiz,mix=.5*(aix+bix),miy=.5*(aiy+biy),miz=.5*(aiz+biz);double row=0.0;for(size_t j=0;j<(size_t)n;++j){size_t jp=(j+1)%n;double ajx=p[3*j],ajy=p[3*j+1],ajz=p[3*j+2],bjx=p[3*jp],bjy=p[3*jp+1],bjz=p[3*jp+2];double djx=bjx-ajx,djy=bjy-ajy,djz=bjz-ajz,mjx=.5*(ajx+bjx),mjy=.5*(ajy+bjy),mjz=.5*(ajz+bjz);double rx=mix-mjx,ry=miy-mjy,rz=miz-mjz;row+=(dix*djx+diy*djy+diz*djz)/std::sqrt(rx*rx+ry*ry+rz*rz+a2);}total+=row;}return rho*gamma*gamma/(8*PI)*total;}
void vec_add_host(const double*a,const double*b,double*c,py::ssize_t n){
#ifdef _OPENMP
#pragma omp parallel for if(n>256)
#endif
for(long long i=0;i<n;++i)c[i]=a[i]+b[i];}
double min_abs_host(const double*x,py::ssize_t n){double d=std::numeric_limits<double>::infinity();
#ifdef _OPENMP
#pragma omp parallel
#endif
{double local=std::numeric_limits<double>::infinity();
#ifdef _OPENMP
#pragma omp for nowait
#endif
for(long long i=0;i<n;++i)local=std::min(local,std::abs(x[i]));
#ifdef _OPENMP
#pragma omp critical
#endif
{d=std::min(d,local);}}
return d;}
#ifdef SST_HAVE_SYCL
struct QueueState{std::unique_ptr<sycl::queue> q;std::string name{"none"};bool gpu=false;bool reused=false;}; QueueState gq;
QueueState& queue_state(bool allow_cpu){if(gq.q){gq.reused=true;if(!gq.gpu&&!allow_cpu)throw std::runtime_error("SYCL queue is CPU-only");return gq;}sycl::device dev;try{dev=sycl::device(sycl::gpu_selector_v);}catch(...){if(!allow_cpu)throw std::runtime_error("No SYCL GPU visible");dev=sycl::device(sycl::default_selector_v);}gq.q=std::make_unique<sycl::queue>(dev);gq.name=dev.get_info<sycl::info::device::name>();gq.gpu=dev.is_gpu();return gq;}
void biot_sycl(const double*p,py::ssize_t n,const double*q,py::ssize_t m,double gamma,double core,double*v,bool allow_cpu){auto&st=queue_state(allow_cpu);size_t N=n,M=m;double scale=gamma/(4*PI),a2=core*core;sycl::buffer<double,1>P(const_cast<double*>(p),sycl::range<1>(3*N));sycl::buffer<double,1>Q(const_cast<double*>(q),sycl::range<1>(3*M));sycl::buffer<double,1>V(v,sycl::range<1>(3*M));st.q->submit([&](sycl::handler&h){auto P_=P.get_access<sycl::access_mode::read>(h),Q_=Q.get_access<sycl::access_mode::read>(h),V_=V.get_access<sycl::access_mode::write>(h);h.parallel_for(sycl::range<1>(M),[=](sycl::id<1> id){size_t i=id[0];double x=Q_[3*i],y=Q_[3*i+1],z=Q_[3*i+2],vx=0,vy=0,vz=0;for(size_t s=0;s<N;++s){size_t t=(s+1)%N;double ax=P_[3*s],ay=P_[3*s+1],az=P_[3*s+2],bx=P_[3*t],by=P_[3*t+1],bz=P_[3*t+2],dx=bx-ax,dy=by-ay,dz=bz-az,mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz),rx=x-mx,ry=y-my,rz=z-mz,D=rx*rx+ry*ry+rz*rz+a2,inv=1.0/(D*sycl::sqrt(D));vx+=scale*(dy*rz-dz*ry)*inv;vy+=scale*(dz*rx-dx*rz)*inv;vz+=scale*(dx*ry-dy*rx)*inv;}V_[3*i]=vx;V_[3*i+1]=vy;V_[3*i+2]=vz;});});st.q->wait();}
double hamiltonian_sycl(const double*p,py::ssize_t n,double rho,double gamma,double core,bool allow_cpu){auto&st=queue_state(allow_cpu);size_t N=n;double a2=core*core;std::vector<double> terms(N,0.0);{sycl::buffer<double,1>P(const_cast<double*>(p),sycl::range<1>(3*N));sycl::buffer<double,1>T(terms.data(),sycl::range<1>(N));st.q->submit([&](sycl::handler&h){auto P_=P.get_access<sycl::access_mode::read>(h),T_=T.get_access<sycl::access_mode::write>(h);h.parallel_for(sycl::range<1>(N),[=](sycl::id<1> id){size_t i=id[0],ip=(i+1)%N;double aix=P_[3*i],aiy=P_[3*i+1],aiz=P_[3*i+2],bix=P_[3*ip],biy=P_[3*ip+1],biz=P_[3*ip+2],dix=bix-aix,diy=biy-aiy,diz=biz-aiz,mix=.5*(aix+bix),miy=.5*(aiy+biy),miz=.5*(aiz+biz),row=0;for(size_t j=0;j<N;++j){size_t jp=(j+1)%N;double ajx=P_[3*j],ajy=P_[3*j+1],ajz=P_[3*j+2],bjx=P_[3*jp],bjy=P_[3*jp+1],bjz=P_[3*jp+2],djx=bjx-ajx,djy=bjy-ajy,djz=bjz-ajz,mjx=.5*(ajx+bjx),mjy=.5*(ajy+bjy),mjz=.5*(ajz+bjz),rx=mix-mjx,ry=miy-mjy,rz=miz-mjz;row+=(dix*djx+diy*djy+diz*djz)/sycl::sqrt(rx*rx+ry*ry+rz*rz+a2);}T_[i]=row;});});st.q->wait();}double total=0;for(double x:terms)total+=x;return rho*gamma*gamma/(8*PI)*total;}
#endif
}
py::array_t<double> vec_add(py::array_t<double,py::array::c_style|py::array::forcecast>a,py::array_t<double,py::array::c_style|py::array::forcecast>b,bool use_sycl,bool allow_cpu){auto A=a.request(),B=b.request();if(A.size!=B.size)throw std::runtime_error("size mismatch");py::array_t<double>o(A.size);auto O=o.request();Timer t;{py::gil_scoped_release r;vec_add_host((double*)A.ptr,(double*)B.ptr,(double*)O.ptr,A.size);t.stop(host_backend());}(void)use_sycl;(void)allow_cpu;return o;}
double min_abs_py(py::array_t<double,py::array::c_style|py::array::forcecast>x,bool use_sycl,bool allow_cpu){auto X=x.request();Timer t;double d;{py::gil_scoped_release r;d=min_abs_host((double*)X.ptr,X.size);t.stop(host_backend());}(void)use_sycl;(void)allow_cpu;return d;}
py::array_t<double> biot_savart(py::array_t<double,py::array::c_style|py::array::forcecast>points,py::array_t<double,py::array::c_style|py::array::forcecast>queries,double gamma,double core,bool use_sycl,bool allow_cpu){py::ssize_t n=0,m=0;const double*p=ptr_nx3(points,n),*q=ptr_nx3(queries,m);py::array_t<double>v({m,(py::ssize_t)3});auto V=v.request();Timer t;{py::gil_scoped_release r;
#ifdef SST_HAVE_SYCL
if(use_sycl){biot_sycl(p,n,q,m,gamma,core,(double*)V.ptr,allow_cpu);t.stop("sycl");}else
#else
(void)use_sycl;(void)allow_cpu;
#endif
{biot_host(p,n,q,m,gamma,core,(double*)V.ptr);t.stop(host_backend());}}
return v;}
double filament_hamiltonian(py::array_t<double,py::array::c_style|py::array::forcecast>points,double rho,double gamma,double core,bool use_sycl,bool allow_cpu){py::ssize_t n=0;const double*p=ptr_nx3(points,n);Timer t;double H;{py::gil_scoped_release r;
#ifdef SST_HAVE_SYCL
if(use_sycl){H=hamiltonian_sycl(p,n,rho,gamma,core,allow_cpu);t.stop("sycl");}else
#else
(void)use_sycl;(void)allow_cpu;
#endif
{H=hamiltonian_host(p,n,rho,gamma,core);t.stop(host_backend());}}
return H;}
py::dict backend_info(){py::dict d;
#ifdef SST_HAVE_SYCL
d["sycl_compiled"]=true;if(gq.q){d["device_name"]=gq.name;d["is_gpu"]=gq.gpu;d["queue_reused"]=gq.reused;}else{try{sycl::device dev(sycl::gpu_selector_v);d["device_name"]=dev.get_info<sycl::info::device::name>();d["is_gpu"]=dev.is_gpu();}catch(...){d["device_name"]="no-gpu-yet";d["is_gpu"]=false;}d["queue_reused"]=false;}
#else
d["sycl_compiled"]=false;d["device_name"]="host";d["is_gpu"]=false;d["queue_reused"]=false;
#endif
#ifdef _OPENMP
d["openmp_compiled"]=true;d["openmp_max_threads"]=omp_get_max_threads();
#else
d["openmp_compiled"]=false;d["openmp_max_threads"]=1;
#endif
d["last_backend"]=g_last_backend;d["last_kernel_ms"]=g_last_ms;d["backend"]=g_last_backend;return d;}
bool probe_sycl_gpu(){
#ifdef SST_HAVE_SYCL
try{sycl::device d(sycl::gpu_selector_v);return d.is_gpu();}catch(...){return false;}
#else
return false;
#endif
}
PYBIND11_MODULE(_native,m){m.doc()="Kelvin-Joule SST GPU-first regularized filament kernels";m.def("vec_add",&vec_add,py::arg("a"),py::arg("b"),py::arg("use_sycl")=false,py::arg("allow_sycl_cpu")=false);m.def("min_abs",&min_abs_py,py::arg("x"),py::arg("use_sycl")=false,py::arg("allow_sycl_cpu")=false);m.def("biot_savart",&biot_savart,py::arg("points"),py::arg("queries"),py::arg("gamma")=1.0,py::arg("core")=1.0,py::arg("use_sycl")=false,py::arg("allow_sycl_cpu")=false);m.def("filament_hamiltonian",&filament_hamiltonian,py::arg("points"),py::arg("rho"),py::arg("gamma"),py::arg("core"),py::arg("use_sycl")=false,py::arg("allow_sycl_cpu")=false);m.def("backend_info",&backend_info);m.def("probe_sycl_gpu",&probe_sycl_gpu);
#ifdef SST_HAVE_SYCL
m.attr("sycl_compiled")=true;
#else
m.attr("sycl_compiled")=false;
#endif
#ifdef _OPENMP
m.attr("openmp_compiled")=true;
#else
m.attr("openmp_compiled")=false;
#endif
}
