#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>
#include <array>
#include <algorithm>

namespace py = pybind11;

static double polyline_length(py::array_t<double, py::array::c_style | py::array::forcecast> pts) {
    auto b = pts.unchecked<2>();
    if (b.shape(1) != 3 || b.shape(0) < 3) throw std::runtime_error("Expected Nx3 points");
    const py::ssize_t n = b.shape(0);
    double L = 0.0;
    for (py::ssize_t i=0; i<n; ++i) {
        const py::ssize_t j = (i+1)%n;
        double dx=b(j,0)-b(i,0), dy=b(j,1)-b(i,1), dz=b(j,2)-b(i,2);
        L += std::sqrt(dx*dx+dy*dy+dz*dz);
    }
    return L;
}

static double min_nonlocal_distance(
    py::array_t<double, py::array::c_style | py::array::forcecast> pts,
    int exclude_neighbors
) {
    auto b = pts.unchecked<2>();
    if (b.shape(1) != 3 || b.shape(0) < 8) throw std::runtime_error("Expected Nx3 points");
    const py::ssize_t n = b.shape(0);
    double d2min = std::numeric_limits<double>::infinity();
    for (py::ssize_t i=0; i<n; ++i) {
        for (py::ssize_t j=i+1; j<n; ++j) {
            py::ssize_t sep = j-i;
            py::ssize_t cyc = std::min(sep, n-sep);
            if (cyc <= exclude_neighbors) continue;
            double dx=b(j,0)-b(i,0), dy=b(j,1)-b(i,1), dz=b(j,2)-b(i,2);
            double d2=dx*dx+dy*dy+dz*dz;
            if (d2 < d2min) d2min = d2;
        }
    }
    return std::sqrt(d2min);
}

static py::dict curvature_stats(
    py::array_t<double, py::array::c_style | py::array::forcecast> pts
) {
    auto b = pts.unchecked<2>();
    if (b.shape(1) != 3 || b.shape(0) < 8) throw std::runtime_error("Expected Nx3 points");
    const py::ssize_t n = b.shape(0);
    std::vector<double> kappas;
    kappas.reserve(n);
    for (py::ssize_t i=0; i<n; ++i) {
        py::ssize_t im=(i+n-1)%n, ip=(i+1)%n;
        std::array<double,3> a{b(i,0)-b(im,0), b(i,1)-b(im,1), b(i,2)-b(im,2)};
        std::array<double,3> c{b(ip,0)-b(i,0), b(ip,1)-b(i,1), b(ip,2)-b(i,2)};
        double la=std::sqrt(a[0]*a[0]+a[1]*a[1]+a[2]*a[2]);
        double lc=std::sqrt(c[0]*c[0]+c[1]*c[1]+c[2]*c[2]);
        if (la<=0 || lc<=0) { kappas.push_back(0.0); continue; }
        double tx0=a[0]/la, tx1=a[1]/la, tx2=a[2]/la;
        double ty0=c[0]/lc, ty1=c[1]/lc, ty2=c[2]/lc;
        double ds=0.5*(la+lc);
        double dx=ty0-tx0, dy=ty1-tx1, dz=ty2-tx2;
        kappas.push_back(std::sqrt(dx*dx+dy*dy+dz*dz)/ds);
    }
    double sum=0.0, sum2=0.0, mx=0.0;
    for (double k: kappas) { sum+=k; sum2+=k*k; if(k>mx)mx=k; }
    double mean=sum/kappas.size();
    double rms=std::sqrt(sum2/kappas.size());
    py::dict d;
    d["mean"]=mean; d["rms"]=rms; d["max"]=mx;
    return d;
}

static double lab_action_uniform_g(double T, double m, double g, int n) {
    if (T <= 0 || m <= 0 || g <= 0 || n < 5) throw std::runtime_error("invalid parameters");
    if ((n % 2)==0) ++n;
    const double dt = (2.0*T)/(n-1);
    auto L = [=](double t) {
        double z = 0.5*g*(T*T-t*t);
        double v = -g*t;
        return 0.5*m*v*v - m*g*z;
    };
    double s = 0.5*(L(-T)+L(T));
    for (int i=1;i<n-1;++i) s += L(-T+i*dt);
    return s*dt;
}

PYBIND11_MODULE(sst_qgi_native, m) {
    m.doc() = "Native kernels for SST QGI falsifier";
    m.def("polyline_length", &polyline_length);
    m.def("min_nonlocal_distance", &min_nonlocal_distance, py::arg("points"), py::arg("exclude_neighbors")=4);
    m.def("curvature_stats", &curvature_stats);
    m.def("lab_action_uniform_g", &lab_action_uniform_g);
}
