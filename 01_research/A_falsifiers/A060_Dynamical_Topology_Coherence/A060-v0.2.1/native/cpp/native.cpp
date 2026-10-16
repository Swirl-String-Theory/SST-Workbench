#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
#include <string>
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
py::dict backend_info(){py::dict d;d["backend"]=backend_name();d["precision"]="float64";
#ifdef _OPENMP
d["openmp_compiled"]=true;d["openmp_max_threads"]=omp_get_max_threads();
#else
d["openmp_compiled"]=false;d["openmp_max_threads"]=1;
#endif
return d;}

py::array_t<double> tensor_diagnostics(py::array_t<double,py::array::c_style|py::array::forcecast> matrix) {
    auto b=matrix.request();if(b.ndim!=2||b.shape[0]!=3||b.shape[1]!=3) throw std::runtime_error("tensor must be 3x3");
    const double *a=static_cast<const double*>(b.ptr);
    auto at=[&](int i,int j){return a[3*i+j];};
    double S[3][3]={{0}},w[3]={at(2,1)-at(1,2),at(0,2)-at(2,0),at(1,0)-at(0,1)};
    for(int i=0;i<3;++i)for(int j=0;j<3;++j)S[i][j]=0.5*(at(i,j)+at(j,i));
    double tr=at(0,0)+at(1,1)+at(2,2),trAA=0,st2=0;
    for(int i=0;i<3;++i)for(int j=0;j<3;++j){trAA+=at(i,j)*at(j,i);st2+=S[i][j]*S[i][j];}
    double det=at(0,0)*(at(1,1)*at(2,2)-at(1,2)*at(2,1))
              -at(0,1)*(at(1,0)*at(2,2)-at(1,2)*at(2,0))
              +at(0,2)*(at(1,0)*at(2,1)-at(1,1)*at(2,0));
    double Sw[3]={0,0,0}, s3=0,vs=0,wn2=0;
    for(int i=0;i<3;++i) {wn2+=w[i]*w[i];for(int j=0;j<3;++j)Sw[i]+=S[i][j]*w[j];vs+=w[i]*Sw[i];}
    for(int i=0;i<3;++i)for(int j=0;j<3;++j)for(int k=0;k<3;++k) s3+=S[i][j]*S[j][k]*S[k][i];
    double rs=-s3/3.0;
    py::array_t<double> out({py::ssize_t(8)});
    auto v=out.mutable_unchecked<1>();v(0)=tr;v(1)=-.5*trAA;v(2)=-det;v(3)=.5*wn2;v(4)=st2;v(5)=rs;v(6)=vs;v(7)=3*rs+vs/4;
    return out;
}

PYBIND11_MODULE(_sst_native,m){m.doc()="Instance-local C++17/OpenMP reference kernel; extend per falsifier";m.def("biot_savart",&biot_savart,py::arg("points"),py::arg("queries"),py::arg("gamma")=1.0,py::arg("core")=.04);m.def("backend_info",&backend_info);m.def("tensor_diagnostics",&tensor_diagnostics,py::arg("A"));}
