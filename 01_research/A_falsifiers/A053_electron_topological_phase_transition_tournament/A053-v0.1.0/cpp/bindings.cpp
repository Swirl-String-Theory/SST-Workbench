#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <complex>
#include <cmath>
namespace py=pybind11;
double circular_order(const std::vector<double>& p){
    std::complex<double> z{0,0}; if(p.empty()) return NAN;
    for(double x:p) z += std::complex<double>(std::cos(x),std::sin(x));
    return std::abs(z)/static_cast<double>(p.size());
}
PYBIND11_MODULE(a053_native,m){m.def("circular_order",&circular_order);}
