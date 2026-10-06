#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
namespace py=pybind11;

py::tuple integrate(double phi0,double p0,double kappa,double dt,py::ssize_t steps){
    py::array_t<double> phi(steps+1), p(steps+1);
    auto ph=phi.mutable_unchecked<1>(); auto pp=p.mutable_unchecked<1>();
    ph(0)=phi0; pp(0)=p0; double a=kappa*std::sin(2.0*phi0);
    for(py::ssize_t i=0;i<steps;i++){
        double pnphi=ph(i)+dt*pp(i)+0.5*dt*dt*a;
        double an=kappa*std::sin(2.0*pnphi);
        double pnext=pp(i)+0.5*dt*(a+an);
        ph(i+1)=pnphi; pp(i+1)=pnext; a=an;
    }
    return py::make_tuple(phi,p);
}
PYBIND11_MODULE(sst_trpl_native,m){m.def("integrate",&integrate);}
