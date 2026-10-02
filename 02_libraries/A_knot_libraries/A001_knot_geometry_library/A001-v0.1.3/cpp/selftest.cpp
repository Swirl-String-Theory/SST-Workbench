#include "kernels.hpp"
#include <iostream>
#include <cmath>
int main(){
    std::vector<sstknot::V3> c;
    const int n=128; const double pi=3.14159265358979323846;
    for(int i=0;i<n;i++){double t=2*pi*i/n;c.push_back({std::cos(t),std::sin(t),0.0});}
    double d=sstknot::min_nonlocal_distance(c,8);
    double w=sstknot::writhe_midpoint(c);
    std::cout<<"circle_nonlocal="<<d<<"\n"<<"circle_writhe="<<w<<"\n";
    return (std::isfinite(d)&&std::abs(w)<1e-10)?0:1;
}
