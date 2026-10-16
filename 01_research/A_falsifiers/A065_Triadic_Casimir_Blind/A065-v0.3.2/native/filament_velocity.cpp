// A065 v0.3.0 independent C++17 double-precision reference for the
// regularized midpoint-segment Biot-Savart velocity. Numerical parity only.
#include <iostream>
#include <iomanip>
#include <vector>
#include <array>
#include <cmath>
int main(){
  int n; double eps, gamma;
  if(!(std::cin>>n>>eps>>gamma)||n<16||n>20000||eps<=0) return 2;
  std::vector<std::array<double,3>> p(n);
  for(int j=0;j<n;++j) if(!(std::cin>>p[j][0]>>p[j][1]>>p[j][2])) return 3;
  const double four_pi=4*std::acos(-1.0);
  std::cout<<std::setprecision(17);
  for(int i=0;i<n;++i){
    std::array<double,3> v{0,0,0};
    for(int j=0;j<n;++j){
      auto& a=p[j];auto& b=p[(j+1)%n];
      double sx=b[0]-a[0],sy=b[1]-a[1],sz=b[2]-a[2];
      double rx=p[i][0]-(a[0]+b[0])/2,ry=p[i][1]-(a[1]+b[1])/2,rz=p[i][2]-(a[2]+b[2])/2;
      double inv=std::pow(rx*rx+ry*ry+rz*rz+eps*eps,-1.5);
      v[0]+=(sy*rz-sz*ry)*inv;
      v[1]+=(sz*rx-sx*rz)*inv;
      v[2]+=(sx*ry-sy*rx)*inv;
    }
    std::cout<<gamma*v[0]/four_pi<<" "<<gamma*v[1]/four_pi<<" "<<gamma*v[2]/four_pi<<"\n";
  }
  return 0;
}
