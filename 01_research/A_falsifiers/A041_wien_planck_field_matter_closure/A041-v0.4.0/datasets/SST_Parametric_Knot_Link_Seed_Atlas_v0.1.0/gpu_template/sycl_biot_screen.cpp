#include <sycl/sycl.hpp>
#include <cmath>
#include <iostream>
#include <vector>
struct V3{double x,y,z;};
int main(){
  sycl::queue q{sycl::default_selector_v};
  std::cout << "device=" << q.get_device().get_info<sycl::info::device::name>() << "\n";
  constexpr int N=256; constexpr double core2=0.05*0.05; constexpr double inv4pi=0.079577471545947667884;
  std::vector<V3> x(N),u(N);
  for(int i=0;i<N;i++){double t=2.0*3.14159265358979323846*i/N; x[i]={std::cos(t),std::sin(t),0.0};}
  {sycl::buffer<V3> bx(x.data(),sycl::range<1>(N)), bu(u.data(),sycl::range<1>(N));
   q.submit([&](sycl::handler& h){auto X=bx.get_access<sycl::access::mode::read>(h); auto U=bu.get_access<sycl::access::mode::write>(h);
     h.parallel_for(sycl::range<1>(N),[=](sycl::id<1> id){int i=id[0]; double ux=0,uy=0,uz=0; V3 xi=X[i];
       for(int j=0;j<N;j++){int k=(j+1)%N; V3 a=X[j],b=X[k]; double dlx=b.x-a.x,dly=b.y-a.y,dlz=b.z-a.z; double mx=.5*(a.x+b.x),my=.5*(a.y+b.y),mz=.5*(a.z+b.z); double rx=xi.x-mx,ry=xi.y-my,rz=xi.z-mz; double r2=rx*rx+ry*ry+rz*rz+core2; double fac=inv4pi/(r2*sycl::sqrt(r2)); ux+=(dly*rz-dlz*ry)*fac; uy+=(dlz*rx-dlx*rz)*fac; uz+=(dlx*ry-dly*rx)*fac;} U[i]={ux,uy,uz};});}).wait();}
  double m=0; for(auto v:u)m+=std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z); std::cout<<"mean_speed="<<m/N<<"\n"; return 0;
}
