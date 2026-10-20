// Optional independent C++17 reference kernel for 2x2 oscillator susceptibility.
// 11 arguments: xi M0 M1 K00 K01 K11 b0 b1 lambda_bare k, output chi lambda reflect
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
int main(int argc,char**argv){
    if(argc!=11) {std::cerr<<"usage xi M0 M1 K00 K01 K11 b0 b1 lambda_bare k\n";return 2;}
    double z[10];for(int i=0;i<10;i++)z[i]=std::strtod(argv[i+1],nullptr);
    double xi=z[0],a=z[3]+xi*xi*z[1],d=z[5]+xi*xi*z[2],off=z[4];
    double det=a*d-off*off;if(a<=0||det<=0)return 3;
    double chi=(d*z[6]*z[6]-2*off*z[6]*z[7]+a*z[7]*z[7])/det;
    double lambda=z[8]-chi; if(lambda<0)return 4;
    double reflection=lambda==0?0:lambda/(2*z[9]+lambda);
    std::cout<<std::setprecision(17)<<chi<<" "<<lambda<<" "<<reflection<<"\n";
}
