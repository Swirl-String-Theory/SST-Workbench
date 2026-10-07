#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <string>
namespace py=pybind11;

py::tuple phase_features(py::array_t<double,py::array::c_style|py::array::forcecast> arr,double dt,double ds,bool periodic){
    auto b=arr.request(); if(b.ndim!=2) throw std::runtime_error("phi must be 2D");
    const py::ssize_t nt=b.shape[0], ns=b.shape[1]; if(nt<3||ns<3) throw std::runtime_error("grid too small");
    auto *p=static_cast<double*>(b.ptr);
    py::ssize_t nso=periodic?ns:ns-2; py::ssize_t nto=nt-2;
    py::array_t<double> y({nto,nso}), ss({nto,nso}), ph({nto,nso});
    auto Y=y.mutable_unchecked<2>(); auto S=ss.mutable_unchecked<2>(); auto P=ph.mutable_unchecked<2>();
    const double idt2=1.0/(dt*dt), ids2=1.0/(ds*ds);
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for(py::ssize_t i=1;i<nt-1;++i){
      for(py::ssize_t jo=0;jo<nso;++jo){
        py::ssize_t j=periodic?jo:jo+1; py::ssize_t jm=periodic?(j+ns-1)%ns:j-1, jp=periodic?(j+1)%ns:j+1;
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
      long double mag=std::exp(logmag); long double term=(k%2?-mag:mag); long double next=sum+term;
      if(std::isfinite((double)next)&&std::abs(term)<=1e-13L*std::max(1.0L,std::abs(next))&&k>8) return (double)next;
      sum=next; if(!std::isfinite((double)sum)) break;
    }
    if(a>0.0 && a<1.0 && x>2.5){
      long double s=0.0L;
      for(int k=1;k<=12;++k){
        long double g=std::tgamma(1.0-a*k);
        if(!std::isfinite((double)g) || g==0.0L) continue;
        long double term=((k%2)?1.0L:-1.0L)/(std::pow((long double)x,(long double)k)*g);
        s+=term; if(std::abs(term)<1e-13L*std::max(1.0L,std::abs(s))) break;
      }
      return (double)s;
    }
    return (double)sum;
}

py::array_t<double> ml_vec(py::array_t<double,py::array::c_style|py::array::forcecast> x,double a){
    auto b=x.request(); py::array_t<double> out(b.shape); auto *xp=(double*)b.ptr; auto *op=(double*)out.request().ptr;
    py::ssize_t n=1; for(auto s:b.shape)n*=s;
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for(py::ssize_t i=0;i<n;++i) op[i]=ml_scalar(xp[i],a); return out;
}

py::array_t<double> softened_velocity(
    py::array_t<double,py::array::c_style|py::array::forcecast> targets,
    py::array_t<double,py::array::c_style|py::array::forcecast> mids,
    py::array_t<double,py::array::c_style|py::array::forcecast> dls,
    double gamma,double core){
    auto bt=targets.request(), bm=mids.request(), bd=dls.request();
    if(bt.ndim!=2||bm.ndim!=2||bd.ndim!=2||bt.shape[1]!=3||bm.shape[1]!=3||bd.shape[1]!=3||bm.shape[0]!=bd.shape[0])
        throw std::runtime_error("targets/mids/dls must have shape (N,3)");
    const auto nt=bt.shape[0], ns=bm.shape[0];
    auto *t=(double*)bt.ptr; auto *m=(double*)bm.ptr; auto *dl=(double*)bd.ptr;
    py::array_t<double> out({nt,(py::ssize_t)3}); auto *o=(double*)out.request().ptr;
    const double fac=gamma/(4.0*3.141592653589793238462643383279502884), a2=core*core;
    #ifdef _OPENMP
    #pragma omp parallel for
    #endif
    for(py::ssize_t i=0;i<nt;++i){
        double vx=0,vy=0,vz=0;
        const double tx=t[3*i],ty=t[3*i+1],tz=t[3*i+2];
        for(py::ssize_t j=0;j<ns;++j){
            double x=tx-m[3*j], y=ty-m[3*j+1], z=tz-m[3*j+2];
            double den=std::pow(x*x+y*y+z*z+a2,1.5);
            double ax=dl[3*j], ay=dl[3*j+1], az=dl[3*j+2];
            vx+=(ay*z-az*y)/den; vy+=(az*x-ax*z)/den; vz+=(ax*y-ay*x)/den;
        }
        o[3*i]=fac*vx; o[3*i+1]=fac*vy; o[3*i+2]=fac*vz;
    }
    return out;
}

py::dict build_info(){
    py::dict d;
    #if defined(_MSC_VER)
      d["compiler_family"]="msvc"; d["compiler_version_macro"]=_MSC_VER;
    #elif defined(__clang__)
      d["compiler_family"]="clang"; d["compiler_version_macro"]=std::string(__clang_version__);
    #elif defined(__GNUC__)
      d["compiler_family"]="gcc"; d["compiler_version_macro"]=std::string(__VERSION__);
    #else
      d["compiler_family"]="unknown"; d["compiler_version_macro"]="unknown";
    #endif
    #ifdef _OPENMP
      d["openmp"] = true; d["openmp_macro"] = _OPENMP;
    #else
      d["openmp"] = false; d["openmp_macro"] = py::none();
    #endif
    d["cplusplus"]=(long long)__cplusplus;
    d["precision"]="IEEE-binary64";
    d["backend"]="cpp17-openmp";
    return d;
}

PYBIND11_MODULE(_a056_native,m){
    m.def("phase_features",&phase_features);
    m.def("mittag_leffler_alpha1_neg",&ml_vec);
    m.def("softened_velocity",&softened_velocity);
    m.def("build_info",&build_info);
    m.attr("backend")="cpp17-openmp";
}
