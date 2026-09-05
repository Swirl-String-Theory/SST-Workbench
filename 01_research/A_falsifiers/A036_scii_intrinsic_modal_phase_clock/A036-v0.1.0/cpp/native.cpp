#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstdint>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
static inline void cross3(double ax,double ay,double az,double bx,double by,double bz,double &cx,double &cy,double &cz){cx=ay*bz-az*by;cy=az*bx-ax*bz;cz=ax*by-ay*bx;}

static py::array_t<double> velocity_impl(py::array_t<double,py::array::c_style|py::array::forcecast> x,double gamma,py::array_t<double,py::array::c_style|py::array::forcecast> core_by_segment,const std::int64_t* NEXT){
 auto b=x.request(),ba=core_by_segment.request(); if(b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("x must have shape (N,3)");
 const py::ssize_t N=b.shape[0]; if(ba.ndim!=1||ba.shape[0]!=N) throw std::runtime_error("core_by_segment must have shape (N,)");
 auto out=py::array_t<double>({N,(py::ssize_t)3}); auto bo=out.request(); const double* X=(const double*)b.ptr; const double* A=(const double*)ba.ptr; double* U=(double*)bo.ptr;
 const double pref=gamma/(4.0*3.141592653589793238462643383279502884); py::gil_scoped_release release;
 #pragma omp parallel for if(N>48)
 for(py::ssize_t i=0;i<N;i++){
  double xi=X[3*i],yi=X[3*i+1],zi=X[3*i+2],ux=0,uy=0,uz=0;
  for(py::ssize_t j=0;j<N;j++){
   py::ssize_t k=NEXT?(py::ssize_t)NEXT[j]:(j+1)%N;
   double sx=X[3*k]-X[3*j],sy=X[3*k+1]-X[3*j+1],sz=X[3*k+2]-X[3*j+2];
   double mx=.5*(X[3*j]+X[3*k]),my=.5*(X[3*j+1]+X[3*k+1]),mz=.5*(X[3*j+2]+X[3*k+2]);
   double rx=xi-mx,ry=yi-my,rz=zi-mz,cx,cy,cz; cross3(sx,sy,sz,rx,ry,rz,cx,cy,cz);
   double den=std::pow(rx*rx+ry*ry+rz*rz+A[j]*A[j],1.5); if(den>0){ux+=pref*cx/den;uy+=pref*cy/den;uz+=pref*cz/den;}
  }
  U[3*i]=ux;U[3*i+1]=uy;U[3*i+2]=uz;
 }
 return out;
}

py::array_t<double> velocity_variable_core(py::array_t<double,py::array::c_style|py::array::forcecast> x,double gamma,py::array_t<double,py::array::c_style|py::array::forcecast> core_by_segment){return velocity_impl(x,gamma,core_by_segment,nullptr);}
py::array_t<double> velocity_variable_core_indexed(py::array_t<double,py::array::c_style|py::array::forcecast> x,double gamma,py::array_t<double,py::array::c_style|py::array::forcecast> core_by_segment,py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> next_index){
 auto b=x.request(),bn=next_index.request(); if(bn.ndim!=1||bn.shape[0]!=b.shape[0]) throw std::runtime_error("next_index must have shape (N,)"); const std::int64_t* NXT=(const std::int64_t*)bn.ptr; return velocity_impl(x,gamma,core_by_segment,NXT);
}

static py::array_t<double> stretch_impl(py::array_t<double,py::array::c_style|py::array::forcecast> x,py::array_t<double,py::array::c_style|py::array::forcecast> u,const std::int64_t* NEXT){
 auto bx=x.request(),bu=u.request(); if(bx.ndim!=2||bx.shape[1]!=3||bu.ndim!=2||bu.shape[0]!=bx.shape[0]||bu.shape[1]!=3) throw std::runtime_error("x,u must both have shape (N,3)");
 const py::ssize_t N=bx.shape[0]; auto out=py::array_t<double>(N); auto bo=out.request(); const double* X=(const double*)bx.ptr; const double* U=(const double*)bu.ptr; double* S=(double*)bo.ptr; py::gil_scoped_release release;
 #pragma omp parallel for if(N>48)
 for(py::ssize_t j=0;j<N;j++){
  py::ssize_t k=NEXT?(py::ssize_t)NEXT[j]:(j+1)%N; double dx=X[3*k]-X[3*j],dy=X[3*k+1]-X[3*j+1],dz=X[3*k+2]-X[3*j+2]; double ell=std::sqrt(dx*dx+dy*dy+dz*dz); if(ell<1e-15){S[j]=0;continue;} double tx=dx/ell,ty=dy/ell,tz=dz/ell; double dux=U[3*k]-U[3*j],duy=U[3*k+1]-U[3*j+1],duz=U[3*k+2]-U[3*j+2]; S[j]=(dux*tx+duy*ty+duz*tz)/ell;
 }
 return out;
}
py::array_t<double> stretch_rate(py::array_t<double,py::array::c_style|py::array::forcecast> x,py::array_t<double,py::array::c_style|py::array::forcecast> u){return stretch_impl(x,u,nullptr);}
py::array_t<double> stretch_rate_indexed(py::array_t<double,py::array::c_style|py::array::forcecast> x,py::array_t<double,py::array::c_style|py::array::forcecast> u,py::array_t<std::int64_t,py::array::c_style|py::array::forcecast> next_index){auto b=x.request(),bn=next_index.request();if(bn.ndim!=1||bn.shape[0]!=b.shape[0]) throw std::runtime_error("next_index must have shape (N,)"); return stretch_impl(x,u,(const std::int64_t*)bn.ptr);}

PYBIND11_MODULE(_native,m){m.doc()="SST intrinsic modal clock O(N^2) indexed multi-component Biot-Savart + stretch kernel";m.def("velocity_variable_core",&velocity_variable_core);m.def("velocity_variable_core_indexed",&velocity_variable_core_indexed);m.def("stretch_rate",&stretch_rate);m.def("stretch_rate_indexed",&stretch_rate_indexed);
#ifdef _OPENMP
m.attr("openmp")=true;
#else
m.attr("openmp")=false;
#endif
}
