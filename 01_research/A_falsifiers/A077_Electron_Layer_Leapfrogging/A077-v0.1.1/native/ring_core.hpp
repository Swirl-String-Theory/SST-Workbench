#pragma once
#include <vector>
#include <stdexcept>
#include <cmath>
namespace ring_sst {
static constexpr double pi=3.1415926535897932384626433832795;
inline std::vector<double> derivative(const std::vector<double>& y,
    const std::vector<double>& g,const std::vector<double>& vol,
    int ntheta=96,double k=0.25) {
 if(y.size()!=2*g.size()||g.size()!=vol.size()||ntheta<16||ntheta%2)
   throw std::runtime_error("invalid input shape or quadrature");
 std::vector<double> out(y.size(),0.0);
 for (size_t i=0;i<g.size();++i){
  double ri=y[2*i],zi=y[2*i+1];
  if(ri<=0||vol[i]<=0)throw std::runtime_error("invalid ring/core");
  double ai=std::sqrt(vol[i]/ri);
  if(8*ri<=ai)throw std::runtime_error("outside thin-core domain");
  out[2*i+1]+=g[i]*(std::log(8*ri/ai)-k)/(4*pi*ri);
  for(size_t j=0;j<g.size();++j){
   if(i==j)continue;
   double rj=y[2*j],zj=y[2*j+1],aj=std::sqrt(vol[j]/rj);
   double dz=zi-zj,sr=0,sz=0;
   for(int h=0;h<ntheta;++h){
    double c=std::cos(2*pi*h/ntheta);
    double d2=ri*ri+rj*rj-2*ri*rj*c+dz*dz+aj*aj;
    double w=1.0/(d2*std::sqrt(d2));
    sr+=c*dz*w;sz+=(rj-ri*c)*w;
   }
   double fac=g[j]*rj/(2*ntheta);
   out[2*i]+=fac*sr;out[2*i+1]+=fac*sz;
  }
 }
 return out;
}
inline std::vector<double> integrate(std::vector<double> y,
 const std::vector<double>& g, const std::vector<double>& a,
 double dt,int steps,int ntheta=96,double k=0.25){
 if(a.size()!=g.size()||y.size()!=2*g.size()||dt<=0||steps<1)
  throw std::runtime_error("bad initial data");
 std::vector<double> vol(a.size());
 for(size_t j=0;j<a.size();++j)vol[j]=a[j]*a[j]*y[2*j];
 std::vector<double> out;out.reserve((steps+1)*y.size());
 for(int it=0;it<=steps;++it){
  out.insert(out.end(),y.begin(),y.end());
  if(it==steps)break;
  auto k1=derivative(y,g,vol,ntheta,k);
  auto temp=y;
  for(size_t z=0;z<y.size();++z)temp[z]=y[z]+dt*k1[z]/2;
  auto k2=derivative(temp,g,vol,ntheta,k);
  for(size_t z=0;z<y.size();++z)temp[z]=y[z]+dt*k2[z]/2;
  auto k3=derivative(temp,g,vol,ntheta,k);
  for(size_t z=0;z<y.size();++z)temp[z]=y[z]+dt*k3[z];
  auto k4=derivative(temp,g,vol,ntheta,k);
  for(size_t z=0;z<y.size();++z){
   y[z]+=dt*(k1[z]+2*k2[z]+2*k3[z]+k4[z])/6;
   if(!std::isfinite(y[z]) || (z%2==0&&y[z]<=0))throw std::runtime_error("nonfinite/negative radius");
  }
 }
 return out;
}
}
