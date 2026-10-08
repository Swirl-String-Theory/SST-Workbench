#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py = pybind11;
namespace { constexpr double PI=3.141592653589793238462643383279502884;
std::string backend_name(){
#ifdef _OPENMP
return "openmp";
#else
return "serial";
#endif
}
}

py::array_t<double> biot_savart(py::array_t<double,py::array::c_style|py::array::forcecast> points,py::array_t<double,py::array::c_style|py::array::forcecast> queries,double gamma,double core){
    if(!(std::isfinite(gamma)&&std::isfinite(core))||core<=0.0) throw std::runtime_error("gamma/core invalid; core must be >0");
    auto bp=points.request(), bq=queries.request();
    if(bp.ndim!=2||bp.shape[1]!=3||bq.ndim!=2||bq.shape[1]!=3) throw std::runtime_error("points/queries must be Nx3");
    const py::ssize_t n=bp.shape[0],m=bq.shape[0]; if(n<3) throw std::runtime_error("need >=3 closed filament points");
    const double* p=static_cast<const double*>(bp.ptr); const double* q=static_cast<const double*>(bq.ptr);
    py::array_t<double> out({m,py::ssize_t(3)}); auto bo=out.request(); double* v=static_cast<double*>(bo.ptr);
    const double scale=gamma/(4.0*PI),a2=core*core;
    { py::gil_scoped_release rel;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if(m>64)
#endif
      for(long long j=0;j<m;++j){ double vx=0,vy=0,vz=0; const double* x=q+3*j;
        for(py::ssize_t s=0;s<n;++s){ py::ssize_t t=(s+1)%n; const double* a=p+3*s; const double* b=p+3*t;
          double dlx=b[0]-a[0],dly=b[1]-a[1],dlz=b[2]-a[2]; double mx=.5*(a[0]+b[0]),my=.5*(a[1]+b[1]),mz=.5*(a[2]+b[2]);
          double rx=x[0]-mx,ry=x[1]-my,rz=x[2]-mz,D=rx*rx+ry*ry+rz*rz+a2,inv3=1.0/(D*std::sqrt(D));
          vx+=scale*(dly*rz-dlz*ry)*inv3; vy+=scale*(dlz*rx-dlx*rz)*inv3; vz+=scale*(dlx*ry-dly*rx)*inv3; }
        v[3*j]=vx;v[3*j+1]=vy;v[3*j+2]=vz; }
    }
    return out;
}

static inline double wrap_periodic_seed(double x, double L) { return x - L * std::round(x / L); }

py::array_t<double> centerline_vorticity_seed(
    py::array_t<double, py::array::c_style | py::array::forcecast> centerline,
    int N, double Lbox, double sigma, double circulation_sign)
{
    if (N < 8 || sigma <= 0.0 || Lbox <= 0.0) throw std::runtime_error("invalid seed parameters");
    auto P=centerline.unchecked<2>();
    if (P.shape(1)!=3 || P.shape(0)<16) throw std::runtime_error("centerline must have shape (M,3), M>=16");
    const int M=(int)P.shape(0);
    struct Q { double x,y,z,tx,ty,tz; };
    std::vector<Q> pts; pts.reserve(M);
    for (int m=0;m<M;m++) {
        const int im=(m+M-1)%M, ip=(m+1)%M;
        double tx=P(ip,0)-P(im,0), ty=P(ip,1)-P(im,1), tz=P(ip,2)-P(im,2);
        const double n=std::sqrt(tx*tx+ty*ty+tz*tz);
        if (!(n>0.0) || !std::isfinite(n)) throw std::runtime_error("degenerate centerline tangent");
        tx/=n; ty/=n; tz/=n;
        pts.push_back({P(m,0),P(m,1),P(m,2),tx,ty,tz});
    }
    auto out=py::array_t<double>({3,N,N,N}); auto a=out.mutable_unchecked<4>();
    for(py::ssize_t c=0;c<3;c++) for(int i=0;i<N;i++) for(int j=0;j<N;j++) for(int k=0;k<N;k++) a(c,i,j,k)=0.0;
    const double dx=Lbox/N, x0=-0.5*Lbox, inv2s2=1.0/(2.0*sigma*sigma);
    { py::gil_scoped_release rel;
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for(int i=0;i<N;i++) { const double x=x0+(i+0.5)*dx;
      for(int j=0;j<N;j++) { const double y=x0+(j+0.5)*dx;
        for(int k=0;k<N;k++) { const double z=x0+(k+0.5)*dx;
          double wx=0,wy=0,wz=0;
          for(const auto &q:pts) {
            const double ddx=wrap_periodic_seed(x-q.x,Lbox), ddy=wrap_periodic_seed(y-q.y,Lbox), ddz=wrap_periodic_seed(z-q.z,Lbox);
            const double d2=ddx*ddx+ddy*ddy+ddz*ddz;
            if(d2>18.0*sigma*sigma) continue;
            const double w=std::exp(-d2*inv2s2); wx+=w*q.tx; wy+=w*q.ty; wz+=w*q.tz;
          }
          a(0,i,j,k)=circulation_sign*wx; a(1,i,j,k)=circulation_sign*wy; a(2,i,j,k)=circulation_sign*wz;
        }
      }
    }}
    return out;
}

py::tuple phase_features(py::array_t<double,py::array::c_style|py::array::forcecast> arr,double dt,double ds,bool periodic){
    auto b=arr.request(); if(b.ndim!=2) throw std::runtime_error("phi must be 2D");
    const py::ssize_t nt=b.shape[0], ns=b.shape[1]; if(nt<3||ns<3) throw std::runtime_error("grid too small");
    const auto *p=static_cast<const double*>(b.ptr); py::ssize_t nso=periodic?ns:ns-2, nto=nt-2;
    py::array_t<double> y({nto,nso}), ss({nto,nso}), ph({nto,nso});
    auto Y=y.mutable_unchecked<2>(); auto S=ss.mutable_unchecked<2>(); auto P=ph.mutable_unchecked<2>();
    const double idt2=1.0/(dt*dt), ids2=1.0/(ds*ds);
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for(long long i=1;i<nt-1;++i){
      for(py::ssize_t jo=0;jo<nso;++jo){
        py::ssize_t j=periodic?jo:jo+1, jm=periodic?(j+ns-1)%ns:j-1, jp=periodic?(j+1)%ns:j+1;
        auto at=[&](py::ssize_t ii,py::ssize_t jj){return p[ii*ns+jj];};
        Y(i-1,jo)=(at(i+1,j)-2*at(i,j)+at(i-1,j))*idt2;
        S(i-1,jo)=(at(i,jp)-2*at(i,j)+at(i,jm))*ids2; P(i-1,jo)=at(i,j);
      }
    }
    return py::make_tuple(y,ss,ph);
}

double ml_scalar(double x,double a){
    if(x==0) return 1.0; if(std::abs(a-1.0)<1e-12) return std::exp(-x);
    long double sum=1.0L;
    for(int k=1;k<=500;++k){
      long double logmag=(long double)k*std::log(x)-std::lgamma(a*k+1.0);
      long double mag=std::exp(logmag), term=(k%2?-mag:mag), next=sum+term;
      if(std::isfinite((double)next)&&std::abs(term)<=1e-13L*std::max(1.0L,std::abs(next))&&k>8) return (double)next;
      sum=next; if(!std::isfinite((double)sum)) break;
    }
    if(a>0.0 && a<1.0 && x>2.5){
      long double s=0.0L;
      for(int k=1;k<=12;++k){
        long double g=std::tgamma(1.0-a*k); if(!std::isfinite((double)g)||g==0.0L) continue;
        long double term=((k%2)?1.0L:-1.0L)/(std::pow((long double)x,(long double)k)*g); s+=term;
        if(std::abs(term)<1e-13L*std::max(1.0L,std::abs(s))) break;
      }
      return (double)s;
    }
    return (double)sum;
}

py::array_t<double> ml_vec(py::array_t<double,py::array::c_style|py::array::forcecast> x,double a){
    auto b=x.request(); py::array_t<double> out(b.shape); const auto *xp=static_cast<const double*>(b.ptr); auto *op=static_cast<double*>(out.request().ptr);
    py::ssize_t n=1; for(auto s:b.shape)n*=s;
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for(long long i=0;i<n;++i) op[i]=ml_scalar(xp[i],a); return out;
}

py::dict backend_info(){py::dict d;d["backend"]=backend_name();d["precision"]="float64";
#ifdef _OPENMP
 d["openmp_compiled"]=true;d["openmp_max_threads"]=omp_get_max_threads();
#else
 d["openmp_compiled"]=false;d["openmp_max_threads"]=1;
#endif
#if defined(_MSC_VER)
 d["compiler_family"]="msvc"; d["compiler_version_macro"]=_MSC_VER;
#elif defined(__clang__)
 d["compiler_family"]="clang"; d["compiler_version_macro"]=std::string(__clang_version__);
#elif defined(__GNUC__)
 d["compiler_family"]="gcc"; d["compiler_version_macro"]=std::string(__VERSION__);
#else
 d["compiler_family"]="unknown";
#endif
 return d;}

PYBIND11_MODULE(_sst_native,m){
 m.doc()="A056 v0.2.3 instance-local C++17/OpenMP certification kernels";
 m.def("biot_savart",&biot_savart,py::arg("points"),py::arg("queries"),py::arg("gamma")=1.0,py::arg("core")=.04);
 m.def("centerline_vorticity_seed",&centerline_vorticity_seed,py::arg("centerline"),py::arg("N"),py::arg("Lbox"),py::arg("sigma"),py::arg("circulation_sign")=1.0);
 m.def("phase_features",&phase_features);
 m.def("mittag_leffler_alpha1_neg",&ml_vec);
 m.def("backend_info",&backend_info);
}
