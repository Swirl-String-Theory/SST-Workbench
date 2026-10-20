// Native parity for radial closed forms only: NOT PKLSA, PDE, or pressure certification.
#include <cmath>
#include <iostream>
#include <iomanip>
#include <string>
int main(){
    std::ios::sync_with_stdio(false);
    std::cout<<std::setprecision(17);
    std::string profile;double g,z,r;
    const double pi=std::acos(-1.);
    while(std::cin>>profile>>g>>z>>r){
        if(g<=0||z<=0||r<=0||(profile!="gaussian"&&profile!="rankine"))return 3;
        const double a=g/std::sqrt((profile=="gaussian"?2.:1.)*pi*z);
        const double q=r/a;
        const double f=profile=="gaussian"?-std::expm1(-q*q):std::fmin(q*q,1.);
        const double v=g*f/(2*pi*r);
        const double vr=g*r/(2*pi*(r*r+a*a));
        std::cout<<a<<' '<<v<<' '<<vr<<'\n';
    }
    return 0;
}
