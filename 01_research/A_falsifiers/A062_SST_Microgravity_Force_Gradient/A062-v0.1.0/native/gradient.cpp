// Strict C++ FP64 midpoint quadrature for A062 Gaussian Euler-Poisson candidate.
// Independent loop structure compared with NumPy, accepts r a n {x|z}.
#include <cmath>
#include <iostream>
#include <iomanip>
#include <cstdlib>
#include <string>
int main(int argc, char** argv) {
    if(argc!=5) { std::cerr << "Usage: gradient R a even_N x|z\n"; return 2; }
    const double r=std::atof(argv[1]), a=std::atof(argv[2]);
    const int n=std::atoi(argv[3]); const std::string axis=argv[4];
    if(r<=0||a<=0||n<12||n%2||!(axis=="x"||axis=="z")) return 2;
    const double rho=7.0e-7, vmax=1.09384563e6;
    const double pi=3.14159265358979323846264338328;
    const double omega=std::sqrt(std::exp(1.0))*vmax/a;
    const double extent=5.5, h=2.0*extent*a/n;
    const double px=(axis=="x")?r:0, pz=(axis=="z")?r:0;
    double sum=0.0;
    for(int i=0;i<n;i++) {
        const double x=(i+0.5)*h-extent*a;
        for(int j=0;j<n;j++) {
            const double y=(j+0.5)*h-extent*a;
            for(int k=0;k<n;k++) {
                const double z=(k+0.5)*h-extent*a;
                const double rho2=x*x+y*y+z*z;
                const double s=2*rho*omega*omega*std::exp(-rho2/(a*a))*(1-(x*x+y*y)/(a*a));
                const double dx=px-x,dy=-y,dz=pz-z;
                const double rsq=dx*dx+dy*dy+dz*dz;
                const double axial=(axis=="x")?dx:dz;
                sum+=s*axial/std::pow(rsq,1.5);
            }
        }
    }
    const double vol=(4.0*pi/3.0)*a*a*a;
    const double f=-vol*(h*h*h)/(4*pi)*sum;
    std::cout<<std::setprecision(17)<<f<<"\n";
    return 0;
}
