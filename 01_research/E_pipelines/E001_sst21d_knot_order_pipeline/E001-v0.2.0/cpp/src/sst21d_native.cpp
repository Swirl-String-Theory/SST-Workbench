#include "sst21d_native.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace {
struct V { double x,y,z; };
V get(const double* p, std::size_t i) { return {p[3*i],p[3*i+1],p[3*i+2]}; }
V add(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
V mul(V a,double s){return {a.x*s,a.y*s,a.z*s};}
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
double norm2(V a){return dot(a,a);}
double norm(V a){return std::sqrt(norm2(a));}
int cyclic_sep(std::size_t i,std::size_t j,std::size_t n){
  const auto d = static_cast<int>(i>j?i-j:j-i);
  return std::min(d, static_cast<int>(n)-d);
}

double segdist(V p1,V q1,V p2,V q2){
  const double eps=1e-15;
  V d1=sub(q1,p1), d2=sub(q2,p2), r=sub(p1,p2);
  double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r), s=0.0,t=0.0;
  if(a<=eps && e<=eps) return norm(r);
  if(a<=eps){ s=0.0; t=std::clamp(f/e,0.0,1.0); }
  else {
    double c=dot(d1,r);
    if(e<=eps){ t=0.0; s=std::clamp(-c/a,0.0,1.0); }
    else {
      double b=dot(d1,d2), denom=a*e-b*b;
      if(std::abs(denom)>eps) s=std::clamp((b*f-c*e)/denom,0.0,1.0);
      t=(b*s+f)/e;
      if(t<0.0){t=0.0;s=std::clamp(-c/a,0.0,1.0);} else if(t>1.0){t=1.0;s=std::clamp((b-c)/a,0.0,1.0);}
    }
  }
  return norm(sub(add(p1,mul(d1,s)),add(p2,mul(d2,t))));
}
}

extern "C" {
int sst21d_native_version(){return 1;}

double sst21d_sampled_dcsd(const double* xyz,std::size_t n,int neighbor_skip){
  if(!xyz || n<4) return std::numeric_limits<double>::quiet_NaN();
  auto dist=[&](std::size_t i,std::size_t j){return norm(sub(get(xyz,i%n),get(xyz,j%n)));};
  double best=std::numeric_limits<double>::infinity();
  for(std::size_t i=0;i<n;i++){
    for(std::size_t j=i+1;j<n;j++){
      if(cyclic_sep(i,j,n)<=neighbor_skip) continue;
      const double d=dist(i,j);
      const double dim=dist((i+n-1)%n,j), dip=dist((i+1)%n,j);
      const double djm=dist(i,(j+n-1)%n), djp=dist(i,(j+1)%n);
      if(d<=dim && d<=dip && d<=djm && d<=djp) best=std::min(best,d);
    }
  }
  return std::isfinite(best)?best:std::numeric_limits<double>::quiet_NaN();
}

double sst21d_inter_component_min_segment_distance(const double* a,std::size_t na,const double* b,std::size_t nb){
  if(!a || !b || na<2 || nb<2) return std::numeric_limits<double>::quiet_NaN();
  double best=std::numeric_limits<double>::infinity();
  for(std::size_t i=0;i<na;i++){
    V p=get(a,i),q=get(a,(i+1)%na);
    for(std::size_t j=0;j<nb;j++) best=std::min(best,segdist(p,q,get(b,j),get(b,(j+1)%nb)));
  }
  return best;
}

void sst21d_writhe_acn_midpoint(const double* xyz,std::size_t n,int neighbor_skip,double* writhe,double* acn){
  double wr=0.0, av=0.0;
  if(xyz && n>=4){
    for(std::size_t i=0;i<n;i++){
      V p=get(xyz,i), q=get(xyz,(i+1)%n), di=sub(q,p), mi=mul(add(p,q),0.5);
      for(std::size_t j=i+1;j<n;j++){
        if(cyclic_sep(i,j,n)<=neighbor_skip) continue;
        V r=get(xyz,j), s=get(xyz,(j+1)%n), dj=sub(s,r), mj=mul(add(r,s),0.5);
        V d=sub(mi,mj); double dn=norm(d); if(dn<1e-14) continue;
        double val=dot(d,cross(di,dj))/(dn*dn*dn);
        wr += 2.0*val; av += 2.0*std::abs(val);
      }
    }
  }
  const double factor=1.0/(4.0*3.14159265358979323846);
  if(writhe) *writhe=wr*factor;
  if(acn) *acn=av*factor;
}

void sst21d_linking_acn_midpoint(const double* a,std::size_t na,const double* b,std::size_t nb,double* linking,double* acn){
  double lk=0.0,av=0.0;
  if(a&&b&&na>=2&&nb>=2){
    for(std::size_t i=0;i<na;i++){
      V p=get(a,i),q=get(a,(i+1)%na),di=sub(q,p),mi=mul(add(p,q),0.5);
      for(std::size_t j=0;j<nb;j++){
        V r=get(b,j),s=get(b,(j+1)%nb),dj=sub(s,r),mj=mul(add(r,s),0.5);
        V d=sub(mi,mj); double dn=norm(d); if(dn<1e-14) continue;
        double val=dot(d,cross(di,dj))/(dn*dn*dn);
        lk+=val; av+=std::abs(val);
      }
    }
  }
  const double factor=1.0/(4.0*3.14159265358979323846);
  if(linking) *linking=lk*factor;
  if(acn) *acn=av*factor;
}
}
