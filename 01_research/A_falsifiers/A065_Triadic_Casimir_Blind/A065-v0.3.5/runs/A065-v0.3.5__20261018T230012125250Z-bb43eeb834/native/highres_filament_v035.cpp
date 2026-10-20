// A065 v0.3.5 -- fast independent C++17 FP64 realization of the FIXED
// reduced regularized midpoint-segment Biot-Savart + RK4 ODE.
// CPU OpenMP optional, no GPU/physical-Euler certification.
// stdin: N epsilon gamma T steps, followed by N 3D vertices.
// stdout: N end-state 3D vertices. stderr: machine status only.
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <vector>
#include <limits>
#ifdef _OPENMP
#include <omp.h>
#endif
using V=std::array<double,3>;
using P=std::vector<V>;
static P stage(const P& y,const P& k,double dt){
    P r(y.size());
    for(size_t i=0;i<y.size();++i)
        for(int d=0;d<3;++d)r[i][d]=y[i][d]+dt*k[i][d];
    return r;
}
static P velo(const P& y,double eps,double gamma){
    const size_t n=y.size();
    P mids(n), segments(n),u(n);
    for(size_t j=0;j<n;++j){
        const V &a=y[j], &b=y[(j+1)%n];
        for(int d=0;d<3;++d){mids[j][d]=(a[d]+b[d])*.5;segments[j][d]=b[d]-a[d];}
    }
    const double eps2=eps*eps, scale=gamma/(4.*std::acos(-1.));
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for(long long ii=0;ii<(long long)n;++ii){
        const V &x=y[(size_t)ii];
        double a0=0.,a1=0.,a2=0.;
        for(size_t j=0;j<n;++j){
            const auto& m=mids[j];const auto& s=segments[j];
            const double r0=x[0]-m[0],r1=x[1]-m[1],r2=x[2]-m[2];
            const double q=r0*r0+r1*r1+r2*r2+eps2;
            const double inv=1.0/(q*std::sqrt(q));
            a0+=(s[1]*r2-s[2]*r1)*inv;
            a1+=(s[2]*r0-s[0]*r2)*inv;
            a2+=(s[0]*r1-s[1]*r0)*inv;
        }
        u[(size_t)ii]={a0*scale,a1*scale,a2*scale};
    }
    return u;
}
int main(){
    int n=0,steps=0;double eps=0.,gamma=0.,T=0.;
    if(!(std::cin>>n>>eps>>gamma>>T>>steps) || n<20 || n>10000 || steps<1 || steps>64 ||
        !std::isfinite(eps) || eps<=0 || !std::isfinite(gamma) ||
        !std::isfinite(T) || T<0.)return 2;
    P y((size_t)n);
    for(auto& v:y){
        if(!(std::cin>>v[0]>>v[1]>>v[2]))return 3;
        for(double x:v)if(!std::isfinite(x))return 4;
    }
    const double dt=T/steps;
    for(int step_id=0;step_id<steps;++step_id){
        P k1=velo(y,eps,gamma);
        P k2=velo(stage(y,k1,dt/2),eps,gamma);
        P k3=velo(stage(y,k2,dt/2),eps,gamma);
        P k4=velo(stage(y,k3,dt),eps,gamma);
        for(size_t i=0;i<y.size();++i){
            for(int d=0;d<3;++d){
                y[i][d]+=dt*(k1[i][d]+2*k2[i][d]+2*k3[i][d]+k4[i][d])/6.;
                if(!std::isfinite(y[i][d]))return 5;
            }
        }
    }
    std::cout<<std::setprecision(17);
    for(auto& v:y)std::cout<<v[0]<<' '<<v[1]<<' '<<v[2]<<'\n';
    return 0;
}
