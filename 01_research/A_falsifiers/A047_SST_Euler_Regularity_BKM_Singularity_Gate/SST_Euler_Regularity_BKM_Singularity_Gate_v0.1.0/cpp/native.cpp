#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <stdexcept>
#include <algorithm>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

static inline double wrap_periodic(double x, double L) {
    return x - L * std::round(x / L);
}

py::array_t<double> trefoil_vorticity_seed(
    int N, double Lbox, double R, double r, double sigma, int M, double circulation_sign)
{
    if (N < 8 || M < 16 || sigma <= 0.0 || Lbox <= 0.0) throw std::runtime_error("invalid seed parameters");
    auto out = py::array_t<double>({3, N, N, N});
    auto a = out.mutable_unchecked<4>();
    for (ssize_t c=0;c<3;c++) for(int i=0;i<N;i++) for(int j=0;j<N;j++) for(int k=0;k<N;k++) a(c,i,j,k)=0.0;

    struct P { double x,y,z,tx,ty,tz; };
    std::vector<P> pts; pts.reserve(M);
    for (int m=0;m<M;m++) {
        const double t = 2.0*PI*m/M;
        const double c2=std::cos(2*t), s2=std::sin(2*t), c3=std::cos(3*t), s3=std::sin(3*t);
        const double rr = R + r*c3;
        const double x = rr*c2;
        const double y = rr*s2;
        const double z = r*s3;
        const double drr = -3*r*s3;
        double tx = drr*c2 - 2*rr*s2;
        double ty = drr*s2 + 2*rr*c2;
        double tz = 3*r*c3;
        const double n = std::sqrt(tx*tx+ty*ty+tz*tz);
        tx/=n; ty/=n; tz/=n;
        pts.push_back({x,y,z,tx,ty,tz});
    }

    const double dx=Lbox/N, x0=-0.5*Lbox;
    const double inv2s2=1.0/(2.0*sigma*sigma);
    for(int i=0;i<N;i++) {
        const double x=x0+(i+0.5)*dx;
        for(int j=0;j<N;j++) {
            const double y=x0+(j+0.5)*dx;
            for(int k=0;k<N;k++) {
                const double z=x0+(k+0.5)*dx;
                double wx=0,wy=0,wz=0,wsum=0;
                for (const auto &p: pts) {
                    const double ddx=wrap_periodic(x-p.x,Lbox);
                    const double ddy=wrap_periodic(y-p.y,Lbox);
                    const double ddz=wrap_periodic(z-p.z,Lbox);
                    const double d2=ddx*ddx+ddy*ddy+ddz*ddz;
                    if (d2 > 18.0*sigma*sigma) continue;
                    const double w=std::exp(-d2*inv2s2);
                    wx += w*p.tx; wy += w*p.ty; wz += w*p.tz; wsum += w;
                }
                // Superposed tangent Gaussian tube. Fourier projection in Python enforces div(omega)=0.
                if (wsum>0) {
                    a(0,i,j,k)=circulation_sign*wx;
                    a(1,i,j,k)=circulation_sign*wy;
                    a(2,i,j,k)=circulation_sign*wz;
                }
            }
        }
    }
    return out;
}

py::dict vector_stats(py::array_t<double, py::array::c_style | py::array::forcecast> v) {
    auto b=v.unchecked<4>();
    if (b.shape(0)!=3) throw std::runtime_error("expected shape (3,N,N,N)");
    long double s2=0.0; double mx=0.0;
    size_t count=1;
    for(ssize_t i=0;i<b.shape(1);i++) for(ssize_t j=0;j<b.shape(2);j++) for(ssize_t k=0;k<b.shape(3);k++) {
        const double q=std::sqrt(b(0,i,j,k)*b(0,i,j,k)+b(1,i,j,k)*b(1,i,j,k)+b(2,i,j,k)*b(2,i,j,k));
        s2 += (long double)q*q; mx=std::max(mx,q); count++;
    }
    py::dict d; d["rms"]=std::sqrt((double)(s2/(count-1))); d["max"]=mx; return d;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Native kernels for SST Euler Regularity / BKM Gate";
    m.def("trefoil_vorticity_seed", &trefoil_vorticity_seed,
          py::arg("N"), py::arg("Lbox"), py::arg("R"), py::arg("r"), py::arg("sigma"), py::arg("M")=192, py::arg("circulation_sign")=1.0);
    m.def("vector_stats", &vector_stats);
}
