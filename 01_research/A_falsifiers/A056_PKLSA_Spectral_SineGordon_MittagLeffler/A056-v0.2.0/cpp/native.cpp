#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <algorithm>
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
PYBIND11_MODULE(_a056_native,m){m.def("phase_features",&phase_features);m.def("mittag_leffler_alpha1_neg",&ml_vec);m.attr("backend")="cpp17-openmp";}
