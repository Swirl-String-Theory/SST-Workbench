#include <pybind11/pybind11.h>
#include <cmath>
#include <stdexcept>
#include <string>
namespace py = pybind11;
static inline double f_profile(const std::string &name, double x, double p1, double p2) {
    const double EPS = 1e-15;
    if (name == "uniform_boundary") return 1.0;
    if (name == "solid_body_boundary") { double p = p1 > 0 ? p1 : 1.0; return std::pow(x, p); }
    if (name == "smooth_matched_poly") { double a0 = p1 > 0 ? p1 : 2.0; return x*(a0+(3.0-2.0*a0)*x*x+(a0-2.0)*x*x*x*x); }
    if (name == "regularized_inv_r_boundary") { double eps = p1 > 0 ? p1 : 0.05; return std::sqrt(1.0+eps*eps)/std::sqrt(x*x+eps*eps); }
    if (name == "lamb_oseen_boundary") { double sigma = p1 > 0 ? p1 : 0.35; double raw = (x < 1e-10) ? x/(sigma*sigma) : (1.0-std::exp(-std::pow(x/sigma,2.0)))/x; double raw1=1.0-std::exp(-std::pow(1.0/sigma,2.0)); return raw/raw1; }
    if (name == "nlse_tanh_density_phase" || name == "nlse_pade_density_phase") return 1.0/std::max(x, EPS);
    if (name == "gaussian_core_max") { double sigma = p1 > 0 ? p1 : 0.35; return std::exp(-std::pow(x/sigma,2.0)); }
    if (name == "gaussian_shell") { double r0 = p1 > 0 ? p1 : 0.75; double sigma = p2 > 0 ? p2 : 0.12; return std::exp(-0.5*std::pow((x-r0)/sigma,2.0)); }
    throw std::runtime_error("unknown profile: " + name);
}
static inline double rho_profile(const std::string &name, double x, double p1, double p2) {
    if (name == "nlse_tanh_density_phase") { double xi = p1 > 0 ? p1 : 0.35; double t=std::tanh(x/xi); return t*t; }
    if (name == "nlse_pade_density_phase") { double xi = p1 > 0 ? p1 : 0.35; return (x*x)/(x*x+xi*xi); }
    return 1.0;
}
py::dict integrate_profile_cpp(const std::string &name, double p1, double p2, int n) {
    double denom=0.0, numer=0.0;
    for(int i=0;i<n;++i){ double x=(static_cast<double>(i)+0.5)/static_cast<double>(n); double f=f_profile(name,x,p1,p2); double rho=rho_profile(name,x,p1,p2); double w=rho*x*x*x; denom+=w; numer+=w*f*f; }
    denom/=static_cast<double>(n); numer/=static_cast<double>(n); double c2=numer/denom; double c=std::sqrt(c2);
    double f1=f_profile(name,1.0,p1,p2); double h=1e-5; double fp1=(f_profile(name,1.0+h,p1,p2)-f_profile(name,1.0-h,p1,p2))/(2.0*h); double slope=fp1/f1;
    double f0; try { f0=f_profile(name,0.0,p1,p2); } catch (...) { f0=INFINITY; } double rho0=rho_profile(name,0.0,p1,p2);
    py::dict d; d["name"]=name; d["c_over_v"]=c; d["c2_over_v2"]=c2; d["gamma_ratio"]=f1; d["slope_boundary"]=slope; d["axis_f0"]=f0; d["axis_rho0"]=rho0; d["denom"]=denom; d["numer"]=numer;
    d["axis_velocity_regular"]=std::isfinite(f0)&&std::abs(f0)<1e-6; d["density_core_regular"]=std::isfinite(rho0)&&rho0<=1e-6; d["boundary_circulation_match"]=std::abs(f1-1.0)<1e-6; d["exterior_slope_match"]=std::isfinite(slope)&&std::abs(slope+1.0)<0.15; d["finite_weighted_energy"]=std::isfinite(numer)&&numer>0.0; return d;
}
PYBIND11_MODULE(sst_chi_phase_v5, m) { m.doc()="SST chi-phase v5 profile-zoo stiffness extractor"; m.def("integrate_profile_cpp", &integrate_profile_cpp, py::arg("name"), py::arg("p1")=0.0, py::arg("p2")=0.0, py::arg("n")=400000); }
