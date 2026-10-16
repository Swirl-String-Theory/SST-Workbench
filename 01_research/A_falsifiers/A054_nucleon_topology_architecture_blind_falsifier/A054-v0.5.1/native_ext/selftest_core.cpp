#include <iostream>
#include "energy_core.hpp"
int main(){std::vector<std::vector<a054::Point>> c(1);for(int i=0;i<64;++i){double t=2*3.14159265358979323846*i/64.0;c[0].push_back({std::cos(t),std::sin(t),0.0});}auto E=a054::energy_matrix(c,1.0);std::cout<<E[0][0]<<"\n";return (std::isfinite(E[0][0])?0:1);}
