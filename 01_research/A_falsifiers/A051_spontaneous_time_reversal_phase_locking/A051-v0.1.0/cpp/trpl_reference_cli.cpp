#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>

int main(int argc, char** argv) {
    double phi = argc > 1 ? std::atof(argv[1]) : 1.3;
    double p   = argc > 2 ? std::atof(argv[2]) : 0.1;
    double k   = argc > 3 ? std::atof(argv[3]) : 1.0;
    double dt  = argc > 4 ? std::atof(argv[4]) : 0.005;
    long steps = argc > 5 ? std::atol(argv[5]) : 2000;
    double a = k * std::sin(2.0 * phi);
    for (long i = 0; i < steps; ++i) {
        const double phin = phi + dt*p + 0.5*dt*dt*a;
        const double an = k * std::sin(2.0 * phin);
        const double pn = p + 0.5*dt*(a + an);
        phi = phin; p = pn; a = an;
    }
    const double H = 0.5*p*p + 0.5*k*std::cos(2.0*phi);
    std::cout << std::setprecision(17) << phi << " " << p << " " << H << "\n";
    return 0;
}
