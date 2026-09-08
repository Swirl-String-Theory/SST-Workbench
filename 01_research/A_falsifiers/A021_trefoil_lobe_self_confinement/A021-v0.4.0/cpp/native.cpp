#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif
#ifdef SST_HAVE_SYCL
#include <sycl/sycl.hpp>
#include <memory>
#endif
namespace py = pybind11;
namespace {
constexpr double PI = 3.141592653589793238462643383279502884;
double g_last_ms = 0.0; std::string g_last_backend = "serial";
struct Timer { std::chrono::steady_clock::time_point t0{std::chrono::steady_clock::now()}; void stop(const std::string& b){auto t1=std::chrono::steady_clock::now(); g_last_ms=std::chrono::duration<double,std::milli>(t1-t0).count(); g_last_backend=b;} };
std::string host_name(){
#ifdef _OPENMP
return "openmp";
#else
return "serial";
#endif
}
inline int cyc_dist(int a,int b,int n){int d=std::abs(a-b); return std::min(d,n-d);} 
void biot_host(const double* p, long long n, const double* q, long long m, double gamma, double core, double* out){
 const double s=gamma/(4.0*PI), a2=core*core;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if(m>32)
#endif
 for(long long i=0;i<m;++i){double vx=0,vy=0,vz=0; const double x=q[3*i],y=q[3*i+1],z=q[3*i+2];
  for(long long j=0;j<n;++j){long long k=(j+1)%n; double ax=p[3*j],ay=p[3*j+1],az=p[3*j+2], bx=p[3*k],by=p[3*k+1],bz=p[3*k+2];
   double dlx=bx-ax,dly=by-ay,dlz=bz-az, mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz), rx=x-mx,ry=y-my,rz=z-mz;
   double D=rx*rx+ry*ry+rz*rz+a2, inv=1.0/(D*std::sqrt(D));
   vx += s*(dly*rz-dlz*ry)*inv; vy += s*(dlz*rx-dlx*rz)*inv; vz += s*(dlx*ry-dly*rx)*inv;
  } out[3*i]=vx;out[3*i+1]=vy;out[3*i+2]=vz;
 }
}
#ifdef SST_HAVE_SYCL
struct QState{std::unique_ptr<sycl::queue> q; std::string name="none"; bool gpu=false;}; QState gq;
QState& getq(bool allow_cpu){if(gq.q){if(!gq.gpu&&!allow_cpu) throw std::runtime_error("SYCL queue is CPU-only"); return gq;} sycl::device d; try{d=sycl::device(sycl::gpu_selector_v);}catch(...){if(!allow_cpu) throw std::runtime_error("No SYCL GPU visible"); d=sycl::device(sycl::default_selector_v);} gq.q=std::make_unique<sycl::queue>(d);gq.name=d.get_info<sycl::info::device::name>();gq.gpu=d.is_gpu();return gq;}
void biot_sycl(const double* p,long long n,const double* q,long long m,double gamma,double core,double* out,bool allow_cpu){auto& st=getq(allow_cpu); size_t N=n,M=m; double s=gamma/(4.0*PI),a2=core*core; sycl::buffer<double,1>P(const_cast<double*>(p),sycl::range<1>(3*N)); sycl::buffer<double,1>Q(const_cast<double*>(q),sycl::range<1>(3*M)); sycl::buffer<double,1>V(out,sycl::range<1>(3*M)); st.q->submit([&](sycl::handler&h){auto P_=P.get_access<sycl::access_mode::read>(h);auto Q_=Q.get_access<sycl::access_mode::read>(h);auto V_=V.get_access<sycl::access_mode::write>(h);h.parallel_for(sycl::range<1>(M),[=](sycl::id<1> ii){size_t i=ii[0];double x=Q_[3*i],y=Q_[3*i+1],z=Q_[3*i+2],vx=0,vy=0,vz=0;for(size_t j=0;j<N;++j){size_t k=(j+1)%N;double ax=P_[3*j],ay=P_[3*j+1],az=P_[3*j+2],bx=P_[3*k],by=P_[3*k+1],bz=P_[3*k+2];double dlx=bx-ax,dly=by-ay,dlz=bz-az,mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz),rx=x-mx,ry=y-my,rz=z-mz;double D=rx*rx+ry*ry+rz*rz+a2,inv=1.0/(D*sycl::sqrt(D));vx+=s*(dly*rz-dlz*ry)*inv;vy+=s*(dlz*rx-dlx*rz)*inv;vz+=s*(dlx*ry-dly*rx)*inv;}V_[3*i]=vx;V_[3*i+1]=vy;V_[3*i+2]=vz;});});st.q->wait();}
#endif
}
py::array_t<double> biot_savart(py::array_t<double,py::array::c_style|py::array::forcecast> P, py::array_t<double,py::array::c_style|py::array::forcecast> Q, double gamma,double core,bool use_sycl,bool allow_cpu){auto bp=P.request(),bq=Q.request();if(bp.ndim!=2||bp.shape[1]!=3||bq.ndim!=2||bq.shape[1]!=3)throw std::runtime_error("points/queries must be Nx3");long long n=bp.shape[0],m=bq.shape[0];py::array_t<double> out({static_cast<py::ssize_t>(m), static_cast<py::ssize_t>(3)});auto bo=out.request();Timer t;{
 py::gil_scoped_release rel;
#ifdef SST_HAVE_SYCL
 if(use_sycl){biot_sycl((double*)bp.ptr,n,(double*)bq.ptr,m,gamma,core,(double*)bo.ptr,allow_cpu);t.stop("sycl");}
 else
#else
 (void)use_sycl;(void)allow_cpu;
#endif
 {biot_host((double*)bp.ptr,n,(double*)bq.ptr,m,gamma,core,(double*)bo.ptr);t.stop(host_name());}}
 return out;}
py::dict centerline_split(py::array_t<double,py::array::c_style|py::array::forcecast>P, py::array_t<int,py::array::c_style|py::array::forcecast>L,double gamma,double core,int local_span){auto bp=P.request(),bl=L.request();if(bp.ndim!=2||bp.shape[1]!=3)throw std::runtime_error("points must be Nx3");long long n=bp.shape[0];if(bl.size!=n)throw std::runtime_error("labels length mismatch");const double*p=(double*)bp.ptr;const int*lab=(int*)bl.ptr;py::array_t<double> total({static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(3)}),local({static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(3)}),same({static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(3)}),cross({static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(3)}),trans({static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(3)});double*ot=(double*)total.request().ptr,*ol=(double*)local.request().ptr,*os=(double*)same.request().ptr,*oc=(double*)cross.request().ptr,*ox=(double*)trans.request().ptr;double scale=gamma/(4*PI),a2=core*core;Timer tm;{
 py::gil_scoped_release rel;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if(n>64)
#endif
 for(long long i=0;i<n;++i){double vt[3]={0,0,0},vl[3]={0,0,0},vs[3]={0,0,0},vc[3]={0,0,0},vx_[3]={0,0,0};double x=p[3*i],y=p[3*i+1],z=p[3*i+2];for(long long j=0;j<n;++j){long long k=(j+1)%n;double ax=p[3*j],ay=p[3*j+1],az=p[3*j+2],bx=p[3*k],by=p[3*k+1],bz=p[3*k+2],dlx=bx-ax,dly=by-ay,dlz=bz-az,mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz),rx=x-mx,ry=y-my,rz=z-mz,D=rx*rx+ry*ry+rz*rz+a2,inv=1.0/(D*std::sqrt(D));double c[3]={scale*(dly*rz-dlz*ry)*inv,scale*(dlz*rx-dlx*rz)*inv,scale*(dlx*ry-dly*rx)*inv};for(int zc=0;zc<3;++zc)vt[zc]+=c[zc];int ed=std::min(cyc_dist((int)i,(int)j,(int)n),cyc_dist((int)i,(int)k,(int)n));if(ed<=local_span){for(int zc=0;zc<3;++zc)vl[zc]+=c[zc];}else{int sl=(lab[j]==lab[k]?lab[j]:-1);double*dst=(sl<0?vx_:(sl==lab[i]?vs:vc));for(int zc=0;zc<3;++zc)dst[zc]+=c[zc];}}
  for(int zc=0;zc<3;++zc){ot[3*i+zc]=vt[zc];ol[3*i+zc]=vl[zc];os[3*i+zc]=vs[zc];oc[3*i+zc]=vc[zc];ox[3*i+zc]=vx_[zc];}}
 tm.stop(host_name());}
 py::dict d;d["total"]=total;d["local"]=local;d["same_lobe"]=same;d["cross_lobe"]=cross;d["transition"]=trans;return d;}
py::dict min_nonlocal_distance(py::array_t<double,py::array::c_style|py::array::forcecast>P,int skip){auto bp=P.request();if(bp.ndim!=2||bp.shape[1]!=3)throw std::runtime_error("points must be Nx3");long long n=bp.shape[0];const double*p=(double*)bp.ptr;double best=std::numeric_limits<double>::infinity();long long bi=-1,bj=-1;
#ifdef _OPENMP
#pragma omp parallel
#endif
 {double lb=std::numeric_limits<double>::infinity();long long li=-1,lj=-1;
#ifdef _OPENMP
#pragma omp for schedule(static) nowait
#endif
 for(long long i=0;i<n;++i)for(long long j=i+1;j<n;++j){if(cyc_dist((int)i,(int)j,(int)n)<=skip)continue;double dx=p[3*i]-p[3*j],dy=p[3*i+1]-p[3*j+1],dz=p[3*i+2]-p[3*j+2],d=std::sqrt(dx*dx+dy*dy+dz*dz);if(d<lb){lb=d;li=i;lj=j;}}
#ifdef _OPENMP
#pragma omp critical
#endif
 {if(lb<best){best=lb;bi=li;bj=lj;}}}
 py::dict d;d["distance"]=best;d["i"]=bi;d["j"]=bj;return d;}
py::dict backend_info(){py::dict d;d["last_backend"]=g_last_backend;d["last_kernel_ms"]=g_last_ms;
#ifdef SST_HAVE_SYCL
 d["sycl_compiled"]=true;if(gq.q){d["device_name"]=gq.name;d["is_gpu"]=gq.gpu;}else{d["device_name"]="not-initialized";d["is_gpu"]=false;}
#else
 d["sycl_compiled"]=false;d["device_name"]="host";d["is_gpu"]=false;
#endif
#ifdef _OPENMP
 d["openmp_compiled"]=true;d["openmp_max_threads"]=omp_get_max_threads();
#else
 d["openmp_compiled"]=false;d["openmp_max_threads"]=1;
#endif
 return d;}
bool probe_sycl_gpu(){
#ifdef SST_HAVE_SYCL
 try{sycl::device d(sycl::gpu_selector_v);return d.is_gpu();}catch(...){return false;}
#else
 return false;
#endif
}
PYBIND11_MODULE(_native,m){m.doc()="SST trefoil lobe-orientation blind falsifier kernels";m.def("biot_savart",&biot_savart,py::arg("points"),py::arg("queries"),py::arg("gamma")=1.0,py::arg("core")=.04,py::arg("use_sycl")=false,py::arg("allow_sycl_cpu")=false);m.def("centerline_split",&centerline_split,py::arg("points"),py::arg("labels"),py::arg("gamma")=1.0,py::arg("core")=.04,py::arg("local_span")=4);m.def("min_nonlocal_distance",&min_nonlocal_distance,py::arg("points"),py::arg("skip")=8);m.def("backend_info",&backend_info);m.def("probe_sycl_gpu",&probe_sycl_gpu);
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
