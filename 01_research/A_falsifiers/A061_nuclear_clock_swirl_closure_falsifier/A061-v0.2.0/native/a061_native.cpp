// A061 FP64 reference parity lane. Not physical certification.
#include <cmath>
#include <iomanip>
#include <iostream>
int main(){
  double x;
  std::cout<<std::setprecision(17);
  while(std::cin>>x){
    if(x<0 || !std::isfinite(x)) return 2;
    const double v=x*std::exp(-x);
    std::cout<<std::sqrt(std::fmax(0.0,1.0-v*v))<<'\n';
  }
  return 0;
}
