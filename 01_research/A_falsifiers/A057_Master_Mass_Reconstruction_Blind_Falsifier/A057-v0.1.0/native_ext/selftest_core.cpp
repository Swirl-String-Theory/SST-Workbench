#include "energy_core.hpp"
#include <cmath>
#include <iostream>
int main(){
    constexpr int N=96; constexpr double pi=3.14159265358979323846;
    std::vector<a057::Point> c; c.reserve(N);
    for(int i=0;i<N;++i){ double t=2*pi*i/N; c.push_back({std::cos(t),std::sin(t),0.0}); }
    auto E=a057::energy_matrix({c,c},1.0);
    const double asym=std::abs(E[0][1]-E[1][0]);
    if(!std::isfinite(E[0][0]) || E[0][0]<=0.0 || asym>1e-14) return 2;
    std::cout << E[0][0] << " " << asym << "\n";
    return 0;
}
