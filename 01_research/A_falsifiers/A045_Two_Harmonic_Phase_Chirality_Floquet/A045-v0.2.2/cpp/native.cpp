#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using Vec = std::array<double,3>;
static Vec add(Vec a,Vec b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static Vec sub(Vec a,Vec b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static Vec mul(Vec a,double s){return {a[0]*s,a[1]*s,a[2]*s};}
static double dot(Vec a,Vec b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static double norm(Vec a){return std::sqrt(dot(a,a));}
static Vec crossv(Vec a,Vec b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}

static std::array<std::array<double,3>,3> drive_matrix(double t,double omega,double a1,double a2,double phase,const std::string& chir){
    const double s2=chir=="COR"?1.0:-1.0;
    Vec v{a1*std::cos(omega*t)+a2*std::cos(2.0*omega*t+phase), a1*std::sin(omega*t)+a2*s2*std::sin(2.0*omega*t+phase), 0.0};
    double q=v[0]*v[0]+v[1]*v[1];
    std::array<std::array<double,3>,3> A{};
    for(int i=0;i<3;i++) for(int j=0;j<3;j++) A[i][j]=v[i]*v[j];
    A[0][0]-=0.5*q; A[1][1]-=0.5*q;
    return A;
}
static double envelope(double t,double total,const std::string& kind){
    if(kind=="flat") return 1.0;
    if(kind=="sin2"){double x=std::min(1.0,std::max(0.0,t/total)); double s=std::sin(3.14159265358979323846*x); return s*s;}
    throw std::runtime_error("unknown envelope");
}

static std::vector<Vec> rhs(const std::vector<Vec>& X,double t,double t_origin,const py::dict& cfg){
    int n=(int)X.size(); std::vector<Vec> seg(n),mid(n); double mean_ds=0.0; Vec C{0,0,0};
    for(int j=0;j<n;j++){seg[j]=sub(X[(j+1)%n],X[j]); mid[j]=mul(add(X[j],X[(j+1)%n]),0.5); mean_ds+=norm(seg[j]); C=add(C,X[j]);}
    mean_ds/=n; C=mul(C,1.0/n);
    double core=py::cast<double>(cfg["core_radius_over_ds"])*mean_ds;
    double strength=py::cast<double>(cfg["bs_strength"])/(4.0*3.14159265358979323846);
    int skip=py::cast<int>(cfg["contact_skip"]);
    double omega=py::cast<double>(cfg["omega"]),a1=py::cast<double>(cfg["a1"]),a2=py::cast<double>(cfg["a2"]),phase=py::cast<double>(cfg["phase"]);
    double drive_strength=py::cast<double>(cfg["drive_strength"]),total=py::cast<double>(cfg["total_time"]);
    std::string chir=py::cast<std::string>(cfg["chirality"]),env=py::cast<std::string>(cfg["envelope"]);
    double tt=t+t_origin; auto A=drive_matrix(tt,omega,a1,a2,phase,chir); double ev=envelope(tt,total,env);
    std::vector<Vec> out(n,{0,0,0});
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for(int i=0;i<n;i++){
        Vec v{0,0,0};
        for(int j=0;j<n;j++){
            int d=std::abs(j-i); d=std::min(d,n-d); if(d<=skip) continue;
            Vec r=sub(X[i],mid[j]); double den=std::pow(dot(r,r)+core*core,1.5);
            v=add(v,mul(crossv(seg[j],r),strength/den));
        }
        Vec q=sub(X[i],C),f{0,0,0};
        for(int r=0;r<3;r++) for(int c=0;c<3;c++) f[r]+=ev*A[r][c]*q[c];
        out[i]=add(v,mul(f,drive_strength));
    }
    return out;
}
static py::array_t<double> evolve(py::array_t<double,py::array::c_style|py::array::forcecast> arr,double duration,double t_origin,py::dict cfg){
    auto b=arr.request(); if(b.ndim!=2||b.shape[1]!=3) throw std::runtime_error("expected Nx3"); int n=(int)b.shape[0]; auto* ptr=(double*)b.ptr; std::vector<Vec>X(n);
    for(int i=0;i<n;i++) X[i]={ptr[3*i],ptr[3*i+1],ptr[3*i+2]};
    #ifdef _OPENMP
    if(cfg.contains("native_threads")) omp_set_num_threads(std::max(1,py::cast<int>(cfg["native_threads"])));
    #endif
    double dt0=py::cast<double>(cfg["dt"]); int steps=std::max(1,(int)std::ceil(duration/dt0)); double dt=duration/steps;
    for(int step=0;step<steps;step++){
        double t=step*dt; auto k1=rhs(X,t,t_origin,cfg); std::vector<Vec>Y(n);
        for(int i=0;i<n;i++)Y[i]=add(X[i],mul(k1[i],0.5*dt)); auto k2=rhs(Y,t+0.5*dt,t_origin,cfg);
        for(int i=0;i<n;i++)Y[i]=add(X[i],mul(k2[i],0.5*dt)); auto k3=rhs(Y,t+0.5*dt,t_origin,cfg);
        for(int i=0;i<n;i++)Y[i]=add(X[i],mul(k3[i],dt)); auto k4=rhs(Y,t+dt,t_origin,cfg);
        for(int i=0;i<n;i++)X[i]=add(X[i],mul(add(add(k1[i],mul(k2[i],2.0)),add(mul(k3[i],2.0),k4[i])),dt/6.0));
    }
    py::array_t<double> out({n,3}); auto ob=out.mutable_unchecked<2>(); for(int i=0;i<n;i++)for(int j=0;j<3;j++)ob(i,j)=X[i][j]; return out;
}
PYBIND11_MODULE(_native,m){m.doc()="SST THPCF v0.2.2 finite-core backend";m.def("evolve",&evolve);}
