#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/complex.h>
#include <cmath>
#include <complex>
#include <stdexcept>
namespace py = pybind11;

py::array_t<double> filament_field(py::array_t<double, py::array::c_style | py::array::forcecast> eval_points,
                                   py::array_t<double, py::array::c_style | py::array::forcecast> curve_points,
                                   double core) {
    auto x = eval_points.unchecked<2>(); auto p = curve_points.unchecked<2>();
    if (x.shape(1)!=3 || p.shape(1)!=3) throw std::runtime_error("arrays must have shape (N,3)");
    const py::ssize_t nx=x.shape(0), np=p.shape(0); py::array_t<double> out({nx, py::ssize_t(3)}); auto o=out.mutable_unchecked<2>();
    const double c2=core*core; const double f=1.0/(4.0*3.1415926535897932384626433832795);
    for(py::ssize_t a=0;a<nx;++a){ double sx=0,sy=0,sz=0;
        for(py::ssize_t j=0;j<np;++j){ py::ssize_t k=(j+1)%np;
            double dlx=p(k,0)-p(j,0), dly=p(k,1)-p(j,1), dlz=p(k,2)-p(j,2);
            double mx=0.5*(p(k,0)+p(j,0)), my=0.5*(p(k,1)+p(j,1)), mz=0.5*(p(k,2)+p(j,2));
            double rx=x(a,0)-mx, ry=x(a,1)-my, rz=x(a,2)-mz; double den=std::pow(rx*rx+ry*ry+rz*rz+c2,1.5);
            sx+=(dly*rz-dlz*ry)/den; sy+=(dlz*rx-dlx*rz)/den; sz+=(dlx*ry-dly*rx)/den;
        }
        o(a,0)=f*sx; o(a,1)=f*sy; o(a,2)=f*sz;
    } return out;
}

std::complex<double> periodic_mode(py::array_t<double, py::array::c_style | py::array::forcecast> real_part,
                                   py::array_t<double, py::array::c_style | py::array::forcecast> imag_part,
                                   int mode) {
    auto a=real_part.unchecked<1>(); auto b=imag_part.unchecked<1>();
    if(a.shape(0)!=b.shape(0)) throw std::runtime_error("arrays must have same length");
    const py::ssize_t n=a.shape(0); std::complex<double> s(0.0,0.0); const double twopi=2.0*3.1415926535897932384626433832795;
    for(py::ssize_t j=0;j<n;++j){ double ph=-twopi*double(mode)*double(j)/double(n); std::complex<double> z(a(j),b(j)); s += z*std::complex<double>(std::cos(ph),std::sin(ph)); }
    return s/double(n);
}

PYBIND11_MODULE(_native,m){
    m.doc()="C++17 acceleration kernels for the dimensionless blind covariance, memory, modal and return analysis";
    m.def("filament_field",&filament_field,py::arg("eval_points"),py::arg("curve_points"),py::arg("core"));
    m.def("periodic_mode",&periodic_mode,py::arg("real_part"),py::arg("imag_part"),py::arg("mode"));
}
