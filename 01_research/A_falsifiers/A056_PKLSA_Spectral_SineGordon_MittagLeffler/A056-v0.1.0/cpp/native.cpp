#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;

py::tuple phase_features(py::array_t<double,py::array::c_style|py::array::forcecast> phi, double dt, double ds, bool periodic){
 auto P=phi.unchecked<2>(); const py::ssize_t nt=P.shape(0), ns=P.shape(1);
 if(nt<3 || ns<3) throw std::runtime_error("phase grid too small");
 const py::ssize_t nsi=periodic?ns:ns-2;
 py::array_t<double> y({nt-2,nsi}), ss({nt-2,nsi}), ph({nt-2,nsi});
 auto Y=y.mutable_unchecked<2>(); auto S=ss.mutable_unchecked<2>(); auto H=ph.mutable_unchecked<2>();
 const double idt2=1.0/(dt*dt), ids2=1.0/(ds*ds);
 #pragma omp parallel for if(nt>32)
 for(py::ssize_t i=1;i<nt-1;++i){
   for(py::ssize_t jj=0;jj<nsi;++jj){
     py::ssize_t j=periodic?jj:jj+1;
     py::ssize_t jm=periodic?(j+ns-1)%ns:j-1, jp=periodic?(j+1)%ns:j+1;
     double p=P(i,j);
     Y(i-1,jj)=(P(i+1,j)-2*p+P(i-1,j))*idt2;
     S(i-1,jj)=(P(i,jp)-2*p+P(i,jm))*ids2;
     H(i-1,jj)=p;
   }
 }
 return py::make_tuple(y,ss,ph);
}

long double ml_scalar(long double x,long double a){
 if(x==0) return 1.0L; if(std::fabs(a-1.0L)<1e-14L) return std::exp(-x);
 long double sum=1.0L;
 for(int k=1;k<=500;++k){
   long double term=std::pow(-x,(long double)k)/std::tgammal(a*k+1.0L);
   long double nsum=sum+term;
   if(std::fabs(term)<1e-14L*std::max((long double)1.0,std::fabs(nsum)) && k>8) return nsum;
   sum=nsum;
   if(!std::isfinite((double)sum)) break;
 }
 if(a>0 && a<1 && x>2.5L){
   long double s=0;
   for(int k=1;k<=12;++k){
     long double g=std::tgammal(1.0L-a*k); if(!std::isfinite((double)g) || g==0) continue;
     long double term=((k%2)?1.0L:-1.0L)/(std::pow(x,(long double)k)*g); s+=term;
     if(std::fabs(term)<1e-14L*std::max((long double)1.0,std::fabs(s))) break;
   }
   return s;
 }
 return sum;
}

py::array_t<double> mittag_leffler_alpha1_neg(py::array_t<double,py::array::c_style|py::array::forcecast> x,double alpha){
 auto X=x.unchecked<1>(); py::array_t<double> out(X.shape(0)); auto O=out.mutable_unchecked<1>();
 #pragma omp parallel for if(X.shape(0)>64)
 for(py::ssize_t i=0;i<X.shape(0);++i) O(i)=(double)ml_scalar((long double)X(i),(long double)alpha);
 return out;
}
PYBIND11_MODULE(_a056_native,m){m.def("phase_features",&phase_features);m.def("mittag_leffler_alpha1_neg",&mittag_leffler_alpha1_neg);}
