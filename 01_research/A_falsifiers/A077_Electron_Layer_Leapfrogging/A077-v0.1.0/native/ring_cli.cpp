// CLI executable for local, independent C++ numerical validation without pybind11.
#include "ring_core.hpp"
#include <iostream>
#include <iomanip>
#include <vector>
int main(){
 try {
  int n,ntheta,steps;double dt;
  if(!(std::cin>>n>>ntheta>>steps>>dt))return 2;
  if(n<1||n>10000||ntheta<16||steps<1)return 2;
  std::vector<double> y(2*n),g(n),a(n);
  for(auto&v:y)std::cin>>v;
  for(auto&v:g)std::cin>>v;
  for(auto&v:a)std::cin>>v;
  auto out=ring_sst::integrate(y,g,a,dt,steps,ntheta);
  std::cout<<std::setprecision(17);
  for(size_t i=0;i<out.size();++i)std::cout<<out[i]<<(i+1==out.size()? '\n':' ');
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 3;}
}
