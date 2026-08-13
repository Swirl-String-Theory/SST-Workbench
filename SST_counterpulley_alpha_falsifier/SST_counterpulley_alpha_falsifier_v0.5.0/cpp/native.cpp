#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>
#include <string>

namespace py = pybind11;
using namespace pybind11::literals;

using Arr = py::array_t<double, py::array::c_style | py::array::forcecast>;

static void require_nx3(const Arr& a, const char* name) {
    if (a.ndim() != 2 || a.shape(1) != 3 || a.shape(0) < 3) {
        throw std::runtime_error(std::string(name) + " must have shape (N,3), N>=3");
    }
}

static inline double dot3(double ax,double ay,double az,double bx,double by,double bz){
    return ax*bx + ay*by + az*bz;
}

// Regularized filament Hamiltonian cross term:
// H_ab = Gamma_a Gamma_b /(8 pi) int int (dxa . dxb)/sqrt(|xa-xb|^2 + eps^2)
// Curves are represented by closed polygon segments and midpoint quadrature.
double interaction_hamiltonian(const Arr& curve_a, const Arr& curve_b,
                               double gamma_a, double gamma_b, double eps) {
    require_nx3(curve_a, "curve_a");
    require_nx3(curve_b, "curve_b");
    if (!(eps > 0.0)) throw std::runtime_error("eps must be > 0");
    auto a = curve_a.unchecked<2>();
    auto b = curve_b.unchecked<2>();
    const ssize_t na = a.shape(0), nb = b.shape(0);
    long double sum = 0.0L;
    py::gil_scoped_release release;
    for (ssize_t i=0;i<na;++i) {
        const ssize_t i2=(i+1)%na;
        const double adx=a(i2,0)-a(i,0), ady=a(i2,1)-a(i,1), adz=a(i2,2)-a(i,2);
        const double amx=0.5*(a(i2,0)+a(i,0)), amy=0.5*(a(i2,1)+a(i,1)), amz=0.5*(a(i2,2)+a(i,2));
        for (ssize_t j=0;j<nb;++j) {
            const ssize_t j2=(j+1)%nb;
            const double bdx=b(j2,0)-b(j,0), bdy=b(j2,1)-b(j,1), bdz=b(j2,2)-b(j,2);
            const double bmx=0.5*(b(j2,0)+b(j,0)), bmy=0.5*(b(j2,1)+b(j,1)), bmz=0.5*(b(j2,2)+b(j,2));
            const double rx=amx-bmx, ry=amy-bmy, rz=amz-bmz;
            const double den=std::sqrt(rx*rx+ry*ry+rz*rz+eps*eps);
            sum += static_cast<long double>(dot3(adx,ady,adz,bdx,bdy,bdz)/den);
        }
    }
    constexpr double pi=3.141592653589793238462643383279502884;
    return gamma_a*gamma_b*static_cast<double>(sum)/(8.0*pi);
}

Arr induced_velocity(const Arr& targets, const Arr& filament, double gamma, double eps) {
    require_nx3(targets, "targets");
    require_nx3(filament, "filament");
    if (!(eps > 0.0)) throw std::runtime_error("eps must be > 0");
    auto x=targets.unchecked<2>();
    auto q=filament.unchecked<2>();
    const ssize_t nt=x.shape(0), nf=q.shape(0);
    Arr out({nt, static_cast<ssize_t>(3)});
    auto u=out.mutable_unchecked<2>();
    constexpr double pi=3.141592653589793238462643383279502884;
    const double pref=gamma/(4.0*pi);
    {
        py::gil_scoped_release release;
        for (ssize_t i=0;i<nt;++i) {
            long double ux=0.0L,uy=0.0L,uz=0.0L;
            for (ssize_t j=0;j<nf;++j) {
                const ssize_t j2=(j+1)%nf;
                const double dlx=q(j2,0)-q(j,0), dly=q(j2,1)-q(j,1), dlz=q(j2,2)-q(j,2);
                const double mx=0.5*(q(j2,0)+q(j,0)), my=0.5*(q(j2,1)+q(j,1)), mz=0.5*(q(j2,2)+q(j,2));
                const double rx=x(i,0)-mx, ry=x(i,1)-my, rz=x(i,2)-mz;
                const double r2=rx*rx+ry*ry+rz*rz+eps*eps;
                const double den=r2*std::sqrt(r2);
                // dl x r
                ux += (dly*rz-dlz*ry)/den;
                uy += (dlz*rx-dlx*rz)/den;
                uz += (dlx*ry-dly*rx)/den;
            }
            u(i,0)=pref*static_cast<double>(ux);
            u(i,1)=pref*static_cast<double>(uy);
            u(i,2)=pref*static_cast<double>(uz);
        }
    }
    return out;
}



Arr pair_rhs(const Arr& plus, const Arr& minus, double gamma_plus, double gamma_minus, double eps) {
    require_nx3(plus, "plus");
    require_nx3(minus, "minus");
    if (plus.shape(0) != minus.shape(0)) throw std::runtime_error("plus and minus must have same N");
    Arr vpp = induced_velocity(plus, plus, gamma_plus, eps);
    Arr vpm = induced_velocity(plus, minus, gamma_minus, eps);
    Arr vmm = induced_velocity(minus, minus, gamma_minus, eps);
    Arr vmp = induced_velocity(minus, plus, gamma_plus, eps);
    const ssize_t n = plus.shape(0);
    Arr out({2*n, static_cast<ssize_t>(3)});
    auto a=vpp.unchecked<2>(); auto b=vpm.unchecked<2>();
    auto c=vmm.unchecked<2>(); auto d=vmp.unchecked<2>();
    auto o=out.mutable_unchecked<2>();
    for (ssize_t i=0;i<n;++i) for (ssize_t k=0;k<3;++k) {
        o(i,k)=a(i,k)+b(i,k);
        o(n+i,k)=c(i,k)+d(i,k);
    }
    return out;
}

double gauss_linking(const Arr& curve_a, const Arr& curve_b) {
    require_nx3(curve_a, "curve_a");
    require_nx3(curve_b, "curve_b");
    auto a=curve_a.unchecked<2>();
    auto b=curve_b.unchecked<2>();
    const ssize_t na=a.shape(0), nb=b.shape(0);
    long double sum=0.0L;
    py::gil_scoped_release release;
    for (ssize_t i=0;i<na;++i) {
        const ssize_t i2=(i+1)%na;
        const double adx=a(i2,0)-a(i,0), ady=a(i2,1)-a(i,1), adz=a(i2,2)-a(i,2);
        const double amx=0.5*(a(i2,0)+a(i,0)), amy=0.5*(a(i2,1)+a(i,1)), amz=0.5*(a(i2,2)+a(i,2));
        for (ssize_t j=0;j<nb;++j) {
            const ssize_t j2=(j+1)%nb;
            const double bdx=b(j2,0)-b(j,0), bdy=b(j2,1)-b(j,1), bdz=b(j2,2)-b(j,2);
            const double bmx=0.5*(b(j2,0)+b(j,0)), bmy=0.5*(b(j2,1)+b(j,1)), bmz=0.5*(b(j2,2)+b(j,2));
            const double rx=amx-bmx, ry=amy-bmy, rz=amz-bmz;
            const double r2=rx*rx+ry*ry+rz*rz;
            if (r2 <= 1e-30) continue;
            const double cx=ady*bdz-adz*bdy;
            const double cy=adz*bdx-adx*bdz;
            const double cz=adx*bdy-ady*bdx;
            sum += static_cast<long double>((cx*rx+cy*ry+cz*rz)/(r2*std::sqrt(r2)));
        }
    }
    constexpr double pi=3.141592653589793238462643383279502884;
    return static_cast<double>(sum)/(4.0*pi);
}

double writhe_midpoint(const Arr& curve) {
    require_nx3(curve, "curve");
    auto c=curve.unchecked<2>();
    const ssize_t n=c.shape(0);
    long double sum=0.0L;
    py::gil_scoped_release release;
    for (ssize_t i=0;i<n;++i) {
        const ssize_t i2=(i+1)%n;
        const double adx=c(i2,0)-c(i,0), ady=c(i2,1)-c(i,1), adz=c(i2,2)-c(i,2);
        const double amx=0.5*(c(i2,0)+c(i,0)), amy=0.5*(c(i2,1)+c(i,1)), amz=0.5*(c(i2,2)+c(i,2));
        for (ssize_t j=0;j<n;++j) {
            if (j==i || j==(i+n-1)%n || j==(i+1)%n) continue;
            const ssize_t j2=(j+1)%n;
            const double bdx=c(j2,0)-c(j,0), bdy=c(j2,1)-c(j,1), bdz=c(j2,2)-c(j,2);
            const double bmx=0.5*(c(j2,0)+c(j,0)), bmy=0.5*(c(j2,1)+c(j,1)), bmz=0.5*(c(j2,2)+c(j,2));
            const double rx=amx-bmx, ry=amy-bmy, rz=amz-bmz;
            const double r2=rx*rx+ry*ry+rz*rz;
            if (r2 <= 1e-30) continue;
            const double cx=ady*bdz-adz*bdy;
            const double cy=adz*bdx-adx*bdz;
            const double cz=adx*bdy-ady*bdx;
            sum += static_cast<long double>((cx*rx+cy*ry+cz*rz)/(r2*std::sqrt(r2)));
        }
    }
    constexpr double pi=3.141592653589793238462643383279502884;
    return static_cast<double>(sum)/(4.0*pi);
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "C++ kernels for the SST counter-pulley alpha falsifier.";
    m.def("interaction_hamiltonian", &interaction_hamiltonian,
          py::arg("curve_a"), py::arg("curve_b"), py::arg("gamma_a"), py::arg("gamma_b"), py::arg("eps"));
    m.def("induced_velocity", &induced_velocity,
          py::arg("targets"), py::arg("filament"), py::arg("gamma"), py::arg("eps"));
    m.def("pair_rhs", &pair_rhs, py::arg("plus"), py::arg("minus"), py::arg("gamma_plus"), py::arg("gamma_minus"), py::arg("eps"));
    m.def("gauss_linking", &gauss_linking, py::arg("curve_a"), py::arg("curve_b"));
    m.def("writhe_midpoint", &writhe_midpoint, py::arg("curve"));
    m.def("backend_info", [](){ return py::dict("name"_a="cpp", "kernel"_a="midpoint_regularized_biot_savart_pair_dynamics_plus_gauss_topology"); });
}
