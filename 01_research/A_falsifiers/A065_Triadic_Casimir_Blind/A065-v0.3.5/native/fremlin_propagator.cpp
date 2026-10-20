// Independently implemented C++17 filament trajectory integrator.
// Input: n epsilon gamma final_time steps, followed by N triples.
// Output: N final positions. This is a reduced filament ODE, not an Euler PDE solver.
#include <array>
#include <vector>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <cstdlib>
using V=std::array<double,3>;
using P=std::vector<V>;
static V add(V a,V b,double s){return V{a[0]+s*b[0],a[1]+s*b[1],a[2]+s*b[2]};}
static P plus(const P& a,const P& b,double s){P out(a.size());for(size_t i=0;i<a.size();++i)out[i]=add(a[i],b[i],s);return out;}
static P velocity(const P& y,double eps,double gam){
  const size_t n=y.size();P u(n,V{0.,0.,0.});const double coef=gam/(4.*std::acos(-1.));
  for(size_t i=0;i<n;++i){const V &x=y[i]; V acc{0.,0.,0.};
    for(size_t j=0;j<n;++j){const V &a=y[j],&b=y[(j+1)%n];
      V dr{x[0]-(a[0]+b[0])/2.,x[1]-(a[1]+b[1])/2.,x[2]-(a[2]+b[2])/2.};
      V ds{b[0]-a[0],b[1]-a[1],b[2]-a[2]};
      double q=std::pow(dr[0]*dr[0]+dr[1]*dr[1]+dr[2]*dr[2]+eps*eps,-1.5);
      acc[0]+=(ds[1]*dr[2]-ds[2]*dr[1])*q;
      acc[1]+=(ds[2]*dr[0]-ds[0]*dr[2])*q;
      acc[2]+=(ds[0]*dr[1]-ds[1]*dr[0])*q;
    }
    for(int d=0;d<3;++d)u[i][d]=coef*acc[d];
  }return u;
}
int main(){int n,steps;double eps,gamma,T;
  if(!(std::cin>>n>>eps>>gamma>>T>>steps)||n<20||n>10000||steps<1||steps>100000||!(eps>0)||!(T>0))return 2;
  P y(n); for(auto& v:y)if(!(std::cin>>v[0]>>v[1]>>v[2]))return 3;
  double dt=T/steps;
  for(int k=0;k<steps;++k){auto k1=velocity(y,eps,gamma);auto k2=velocity(plus(y,k1,dt/2),eps,gamma);
    auto k3=velocity(plus(y,k2,dt/2),eps,gamma);auto k4=velocity(plus(y,k3,dt),eps,gamma);
    for(int i=0;i<n;++i)for(int d=0;d<3;++d)y[i][d]+=dt*(k1[i][d]+2*k2[i][d]+2*k3[i][d]+k4[i][d])/6.;
  }
  std::cout<<std::setprecision(17);
  for(const auto& v:y)std::cout<<v[0]<<' '<<v[1]<<' '<<v[2]<<'\n';
  return 0;
}
