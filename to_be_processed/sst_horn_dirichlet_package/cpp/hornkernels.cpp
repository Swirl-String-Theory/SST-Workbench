#include <pybind11/pybind11.h>
#include <cmath>
#include <map>
#include <string>
#include <vector>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;
static constexpr double TWOPI = 2.0 * PI;

struct Vec3 {
    double x, y, z;
    Vec3() : x(0), y(0), z(0) {}
    Vec3(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}
    Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator*(double a) const { return {a * x, a * y, a * z}; }
};

static inline double dot(const Vec3& a, const Vec3& b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return {a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x};
}
static inline double norm(const Vec3& a) { return std::sqrt(dot(a,a)); }

static Vec3 field_at(const Vec3& x, double lam, int n_ring, double eps) {
    Vec3 v;
    const double dphi = TWOPI / static_cast<double>(n_ring);
    for (int k = 0; k < n_ring; ++k) {
        const double ph = dphi * (k + 0.5);
        const double cp = std::cos(ph), sp = std::sin(ph);
        Vec3 X(lam * cp, lam * sp, 0.0);
        Vec3 dl(-lam * sp * dphi, lam * cp * dphi, 0.0);
        Vec3 r = x - X;
        const double rr = dot(r, r) + eps * eps;
        const double den = rr * std::sqrt(rr);
        Vec3 c = cross(dl, r);
        // Gamma/(4*pi), with normalized circulation Gamma=2*pi => 1/2.
        v = v + c * (0.5 / den);
    }
    return v;
}

static bool inside_torus(const Vec3& p, double lam) {
    const double q = std::sqrt(p.x*p.x + p.y*p.y) - lam;
    return q*q + p.z*p.z <= 1.0;
}

py::dict compute_metrics(double lam, int n_ring, int n_surface, int n_volume,
                         double box_radius, double eps, double fd_step) {
    if (lam <= 1.0) throw std::runtime_error("lambda must be > 1.0");
    n_ring = std::max(32, n_ring);
    n_surface = std::max(8, n_surface);
    n_volume = std::max(8, n_volume);

    // Surface Neumann RMS on torus boundary.
    double neumann2 = 0.0;
    long long sc = 0;
    for (int i = 0; i < n_surface; ++i) {
        const double th = TWOPI * (i + 0.5) / n_surface;
        const double ct = std::cos(th), st = std::sin(th);
        for (int j = 0; j < n_surface; ++j) {
            const double ph = TWOPI * (j + 0.5) / n_surface;
            const double cp = std::cos(ph), sp = std::sin(ph);
            Vec3 x((lam + ct) * cp, (lam + ct) * sp, st);
            Vec3 n(ct * cp, ct * sp, st);
            Vec3 v = field_at(x, lam, n_ring, eps);
            const double nv = dot(n, v);
            neumann2 += nv * nv;
            ++sc;
        }
    }
    const double neumann = std::sqrt(neumann2 / std::max<long long>(1, sc));

    // Circulation around an exterior meridian loop.
    const double r_loop = 1.12;
    int n_circ = std::max(96, n_ring / 2);
    double circ = 0.0;
    for (int k = 0; k < n_circ; ++k) {
        const double a0 = TWOPI * k / n_circ;
        const double a1 = TWOPI * (k + 1) / n_circ;
        const double mid = 0.5 * (a0 + a1);
        Vec3 x(lam + r_loop * std::cos(mid), 0.0, r_loop * std::sin(mid));
        Vec3 dx(-r_loop * std::sin(mid) * (a1 - a0), 0.0, r_loop * std::cos(mid) * (a1 - a0));
        Vec3 v = field_at(x, lam, n_ring, eps);
        circ += dot(v, dx);
    }
    const double circulation_error = std::abs(std::abs(circ) / TWOPI - 1.0);

    // Finite-box kinetic energy integral excluding torus interior.
    const double B = box_radius;
    const double h = (2.0 * B) / static_cast<double>(n_volume - 1);
    double chiK = 0.0;
    long long count = 0;
    for (int ix = 0; ix < n_volume; ++ix) {
        const double x = -B + h * ix;
        for (int iy = 0; iy < n_volume; ++iy) {
            const double y = -B + h * iy;
            for (int iz = 0; iz < n_volume; ++iz) {
                const double z = -B + h * iz;
                Vec3 p(x,y,z);
                if (inside_torus(p, lam)) continue;
                Vec3 v = field_at(p, lam, n_ring, eps);
                chiK += 0.5 * dot(v,v) * h*h*h;
                ++count;
            }
        }
    }

    // Finite-difference div/curl residual on sparse grid.
    int probe = std::min(9, n_volume);
    const double Bp = std::min(3.0, B - fd_step);
    double div2 = 0.0, curl2 = 0.0;
    long long pc = 0;
    for (int ix = 0; ix < probe; ++ix) {
        const double x = -Bp + (2.0 * Bp) * ix / std::max(1, probe - 1);
        for (int iy = 0; iy < probe; ++iy) {
            const double y = -Bp + (2.0 * Bp) * iy / std::max(1, probe - 1);
            for (int iz = 0; iz < probe; ++iz) {
                const double z = -Bp + (2.0 * Bp) * iz / std::max(1, probe - 1);
                Vec3 p(x,y,z);
                if (inside_torus(p, lam)) continue;
                Vec3 ex(fd_step,0,0), ey(0,fd_step,0), ez(0,0,fd_step);
                if (inside_torus(p+ex,lam) || inside_torus(p-ex,lam) || inside_torus(p+ey,lam) || inside_torus(p-ey,lam) || inside_torus(p+ez,lam) || inside_torus(p-ez,lam)) continue;
                Vec3 vx_p = field_at(p+ex, lam, n_ring, eps), vx_m = field_at(p-ex, lam, n_ring, eps);
                Vec3 vy_p = field_at(p+ey, lam, n_ring, eps), vy_m = field_at(p-ey, lam, n_ring, eps);
                Vec3 vz_p = field_at(p+ez, lam, n_ring, eps), vz_m = field_at(p-ez, lam, n_ring, eps);
                Vec3 dVdx = (vx_p - vx_m) * (1.0/(2.0*fd_step));
                Vec3 dVdy = (vy_p - vy_m) * (1.0/(2.0*fd_step));
                Vec3 dVdz = (vz_p - vz_m) * (1.0/(2.0*fd_step));
                const double div = dVdx.x + dVdy.y + dVdz.z;
                Vec3 curl(dVdy.z - dVdz.y, dVdz.x - dVdx.z, dVdx.y - dVdy.x);
                div2 += div * div;
                curl2 += dot(curl, curl);
                ++pc;
            }
        }
    }
    const double divergence_error = std::sqrt(div2 / std::max<long long>(1, pc));
    const double curl_error = std::sqrt(curl2 / std::max<long long>(1, pc));

    // Far-field decay proxy: angular scatter of r^3 |v|.
    std::vector<Vec3> dirs = {Vec3(1,0,0.2), Vec3(0,1,0.2), Vec3(0.7,0.5,0.4), Vec3(-0.4,0.8,0.3)};
    std::vector<double> vals;
    for (double rr : {0.65 * B, 0.85 * B}) {
        for (Vec3 d : dirs) {
            const double dn = norm(d);
            d = d * (1.0 / dn);
            Vec3 v = field_at(d * rr, lam, n_ring, eps);
            vals.push_back(rr * rr * rr * norm(v));
        }
    }
    double mean = 0.0;
    for (double v : vals) mean += v;
    mean /= std::max<size_t>(1, vals.size());
    double var = 0.0;
    for (double v : vals) var += (v - mean) * (v - mean);
    var /= std::max<size_t>(1, vals.size());
    const double farfield = mean > 0.0 ? std::sqrt(var) / mean : 1e9;

    py::dict d;
    d["chi_K"] = chiK;
    d["circulation"] = circ;
    d["circulation_error"] = circulation_error;
    d["neumann_boundary_error"] = neumann;
    d["divergence_error"] = divergence_error;
    d["curl_error"] = curl_error;
    d["farfield_decay_error"] = farfield;
    d["mesh_cells"] = n_volume * n_volume * n_volume;
    d["dof"] = n_volume * n_volume * n_volume;
    d["solver_residual"] = 0.0;
    d["energy_refinement_error"] = std::numeric_limits<double>::quiet_NaN();
    d["solver_kind"] = std::string("pybind11_regularized_ring");
    return d;
}

PYBIND11_MODULE(_hornkernels, m) {
    m.doc() = "SST horn-torus Dirichlet audit C++ backend";
    m.def("compute_metrics", &compute_metrics,
          py::arg("lam"), py::arg("n_ring")=192, py::arg("n_surface")=40,
          py::arg("n_volume")=22, py::arg("box_radius")=6.0,
          py::arg("eps")=0.08, py::arg("fd_step")=0.025);
}
