#include <cmath>
#include <iostream>
#include <vector>
#include "../cpp/fermat_kernel.hpp"

int main() {
    using namespace sst_fermat;
    std::vector<Vec3> circle;
    const int n=256;
    for(int i=0;i<n;++i){
        double t=2.0*M_PI*i/n;
        circle.push_back({std::cos(t),std::sin(t),0.0});
    }
    std::vector<Vec3> probes={{1.0,0.0,-0.0035}};
    auto q=biot_savart_field_jacobian_batch(circle,probes,0.003648676278574026/2.0,0.0019);
    if(q.size()!=1) return 2;
    const double h=1e-7;
    for(int j=0;j<3;++j){
        auto plus=probes, minus=probes;
        if(j==0){plus[0].x+=h; minus[0].x-=h;}
        if(j==1){plus[0].y+=h; minus[0].y-=h;}
        if(j==2){plus[0].z+=h; minus[0].z-=h;}
        auto bp=biot_savart_batch(circle,plus,0.003648676278574026/2.0,0.0019);
        auto bm=biot_savart_batch(circle,minus,0.003648676278574026/2.0,0.0019);
        double fd[3]={(bp[0].x-bm[0].x)/(2*h),(bp[0].y-bm[0].y)/(2*h),(bp[0].z-bm[0].z)/(2*h)};
        for(int i=0;i<3;++i){
            if(std::abs(fd[i]-q[0].jacobian[i][j])>1e-5){
                std::cerr<<"jac mismatch "<<i<<","<<j<<" "<<fd[i]<<" "<<q[0].jacobian[i][j]<<"\n";
                return 3;
            }
        }
    }
    std::cout << "ok\n";
    return 0;
}
