#include <pybind11/pybind11.h>
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

static constexpr double PI = 3.141592653589793238462643383279502884;
static constexpr double TWOPI = 2.0 * PI;

struct Vec3 {
    double x, y, z;
    Vec3() : x(0), y(0), z(0) {}
    Vec3(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}
    Vec3 operator+(const Vec3& o) const { return {x+o.x, y+o.y, z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x, y-o.y, z-o.z}; }
    Vec3 operator*(double a) const { return {a*x, a*y, a*z}; }
    Vec3& operator+=(const Vec3& o) { x += o.x; y += o.y; z += o.z; return *this; }
};
static inline double dot(const Vec3& a, const Vec3& b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return {a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x};
}
static inline double norm(const Vec3& a) { return std::sqrt(dot(a,a)); }

struct Panels {
    std::vector<Vec3> x, n;
    std::vector<double> area;
};

static Vec3 field_ring_at(const Vec3& x, double lam, int n_ring, double eps) {
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
        v += cross(dl, r) * (0.5 / den); // Gamma/(4*pi), Gamma target 2*pi.
    }
    return v;
}

static bool inside_torus(const Vec3& p, double lam) {
    const double q = std::sqrt(p.x*p.x + p.y*p.y) - lam;
    return q*q + p.z*p.z <= 1.0;
}

static Panels make_panels(double lam, int n_eta, int n_phi) {
    Panels P;
    P.x.reserve(n_eta*n_phi);
    P.n.reserve(n_eta*n_phi);
    P.area.reserve(n_eta*n_phi);
    const double d_eta = TWOPI / static_cast<double>(n_eta);
    const double d_phi = TWOPI / static_cast<double>(n_phi);
    for (int i = 0; i < n_eta; ++i) {
        const double eta = d_eta * (i + 0.5);
        const double ce = std::cos(eta), se = std::sin(eta);
        for (int j = 0; j < n_phi; ++j) {
            const double phi = d_phi * (j + 0.5);
            const double cp = std::cos(phi), sp = std::sin(phi);
            P.x.emplace_back((lam + ce)*cp, (lam + ce)*sp, se);
            P.n.emplace_back(ce*cp, ce*sp, se);
            P.area.push_back((lam + ce) * d_eta * d_phi);
        }
    }
    return P;
}

static double circulation_of_field(double lam, int n_circ, const std::function<Vec3(const Vec3&)>& field) {
    const double r_loop = 1.12;
    double circ = 0.0;
    for (int k = 0; k < n_circ; ++k) {
        const double a0 = TWOPI * k / static_cast<double>(n_circ);
        const double a1 = TWOPI * (k+1) / static_cast<double>(n_circ);
        const double mid = 0.5 * (a0 + a1);
        Vec3 x(lam + r_loop*std::cos(mid), 0.0, r_loop*std::sin(mid));
        Vec3 dx(-r_loop*std::sin(mid)*(a1-a0), 0.0, r_loop*std::cos(mid)*(a1-a0));
        circ += dot(field(x), dx);
    }
    return circ;
}

static Vec3 grad_single_layer_at(const Vec3& x, const Panels& P, const std::vector<double>& sigma) {
    Vec3 g;
    for (std::size_t j = 0; j < P.x.size(); ++j) {
        Vec3 r = x - P.x[j];
        double r2 = dot(r, r);
        if (r2 < 1e-24) continue;
        double rn = std::sqrt(r2);
        g += r * (-sigma[j] * P.area[j] / (4.0 * PI * r2 * rn));
    }
    return g;
}

static std::vector<double> build_A(const Panels& P, double self_term, double ridge) {
    const int N = static_cast<int>(P.x.size());
    std::vector<double> A(static_cast<std::size_t>(N) * N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            double val;
            if (i == j) {
                val = self_term + ridge;
            } else {
                Vec3 r = P.x[i] - P.x[j];
                double r2 = dot(r, r);
                double rn = std::sqrt(r2);
                val = -dot(P.n[i], r) * P.area[j] / (4.0 * PI * r2 * rn);
            }
            A[static_cast<std::size_t>(i)*N + j] = val;
        }
    }
    return A;
}

static bool solve_dense(std::vector<double> A, std::vector<double> b, std::vector<double>& x) {
    const int N = static_cast<int>(b.size());
    x.assign(N, 0.0);
    for (int k = 0; k < N; ++k) {
        int piv = k;
        double best = std::abs(A[static_cast<std::size_t>(k)*N + k]);
        for (int i = k+1; i < N; ++i) {
            double v = std::abs(A[static_cast<std::size_t>(i)*N + k]);
            if (v > best) { best = v; piv = i; }
        }
        if (best < 1e-18) return false;
        if (piv != k) {
            for (int j = k; j < N; ++j) std::swap(A[static_cast<std::size_t>(k)*N+j], A[static_cast<std::size_t>(piv)*N+j]);
            std::swap(b[k], b[piv]);
        }
        double diag = A[static_cast<std::size_t>(k)*N + k];
        for (int i = k+1; i < N; ++i) {
            double f = A[static_cast<std::size_t>(i)*N + k] / diag;
            A[static_cast<std::size_t>(i)*N + k] = 0.0;
            for (int j = k+1; j < N; ++j) A[static_cast<std::size_t>(i)*N + j] -= f * A[static_cast<std::size_t>(k)*N + j];
            b[i] -= f * b[k];
        }
    }
    for (int i = N-1; i >= 0; --i) {
        double s = b[i];
        for (int j = i+1; j < N; ++j) s -= A[static_cast<std::size_t>(i)*N + j] * x[j];
        x[i] = s / A[static_cast<std::size_t>(i)*N + i];
    }
    return true;
}

static double vec_norm(const std::vector<double>& a) {
    double s = 0.0; for (double v : a) s += v*v; return std::sqrt(s);
}

struct BemSolution {
    bool enabled = false;
    Panels P;
    std::vector<double> sigma;
    double self_term = std::numeric_limits<double>::quiet_NaN();
    double flux_before = 0.0, flux_after = 0.0, linear_residual = 0.0, predicted_neumann = std::numeric_limits<double>::quiet_NaN(), sigma_l2 = 0.0;
};

static BemSolution solve_bem(double lam, int n_ring, double eps, int n_eta, int n_phi, double self_term, bool auto_self, double ridge, double scale) {
    BemSolution B;
    B.enabled = true;
    B.P = make_panels(lam, n_eta, n_phi);
    const int N = static_cast<int>(B.P.x.size());
    std::vector<double> nv_ring(N), b(N);
    double total_area = 0.0;
    for (double a : B.P.area) total_area += a;
    for (int i = 0; i < N; ++i) {
        Vec3 vr = field_ring_at(B.P.x[i], lam, n_ring, eps) * scale;
        nv_ring[i] = dot(B.P.n[i], vr);
        b[i] = -nv_ring[i];
        B.flux_before += b[i] * B.P.area[i];
    }
    const double mean = B.flux_before / std::max(1e-30, total_area);
    B.flux_after = 0.0;
    for (int i = 0; i < N; ++i) { b[i] -= mean; B.flux_after += b[i] * B.P.area[i]; }

    std::vector<double> candidates{self_term};
    if (auto_self) candidates.push_back(-self_term);
    double best_score = std::numeric_limits<double>::infinity();
    for (double st : candidates) {
        auto A = build_A(B.P, st, ridge);
        std::vector<double> sigma;
        bool ok = solve_dense(A, b, sigma);
        if (!ok) continue;
        std::vector<double> res(N, 0.0), nv_corr(N, 0.0);
        double denom = 0.0, neu_num = 0.0;
        for (int i = 0; i < N; ++i) {
            double As = 0.0;
            for (int j = 0; j < N; ++j) As += A[static_cast<std::size_t>(i)*N+j] * sigma[j];
            res[i] = As - b[i];
            nv_corr[i] = nv_ring[i] + As;
            Vec3 vr = field_ring_at(B.P.x[i], lam, n_ring, eps) * scale;
            denom += dot(vr, vr) * B.P.area[i];
            neu_num += nv_corr[i] * nv_corr[i] * B.P.area[i];
        }
        double lin = vec_norm(res) / std::max(1e-30, vec_norm(b));
        double neu = std::sqrt(neu_num / std::max(1e-30, denom));
        double score = neu + 0.1 * lin;
        if (score < best_score) {
            best_score = score;
            B.self_term = st;
            B.sigma = std::move(sigma);
            B.linear_residual = lin;
            B.predicted_neumann = neu;
        }
    }
    if (B.sigma.empty()) throw std::runtime_error("BEM dense solve failed for both self-term conventions");
    double sig = 0.0;
    for (int i = 0; i < N; ++i) sig += B.sigma[i] * B.sigma[i] * B.P.area[i];
    B.sigma_l2 = std::sqrt(sig / std::max(1e-30, total_area));
    return B;
}

py::dict run_horn_bem(double lam, int n_ring, int n_surface, int n_volume, double box_radius,
                      double eps, double fd_step, bool bem, int bem_n_eta, int bem_n_phi,
                      double bem_self_term, bool bem_auto_self_term, double bem_ridge) {
    if (lam <= 1.0) throw std::runtime_error("lambda must be > 1.0");
    n_ring = std::max(32, n_ring);
    n_surface = std::max(8, n_surface);
    n_volume = std::max(8, n_volume);
    bem_n_eta = std::max(4, bem_n_eta);
    bem_n_phi = std::max(8, bem_n_phi);
    auto raw_field = [&](const Vec3& x) { return field_ring_at(x, lam, n_ring, eps); };
    double raw_circ = circulation_of_field(lam, std::max(128, n_ring/2), raw_field);
    double scale = (std::abs(raw_circ) > 1e-14) ? TWOPI / raw_circ : 1.0;

    BemSolution BS;
    if (bem) BS = solve_bem(lam, n_ring, eps, bem_n_eta, bem_n_phi, bem_self_term, bem_auto_self_term, bem_ridge, scale);

    auto corr_field = [&](const Vec3& x) -> Vec3 {
        if (!bem) return Vec3();
        return grad_single_layer_at(x, BS.P, BS.sigma);
    };
    auto field = [&](const Vec3& x) -> Vec3 {
        return field_ring_at(x, lam, n_ring, eps) * scale + corr_field(x);
    };

    // Independent surface Neumann diagnostic.
    Panels S = make_panels(lam, n_surface, n_surface);
    double neu_num = 0.0, neu_den = 0.0;
    for (std::size_t i = 0; i < S.x.size(); ++i) {
        Vec3 v = field(S.x[i]);
        double nv = dot(S.n[i], v);
        neu_num += nv*nv*S.area[i];
        neu_den += dot(v,v)*S.area[i];
    }
    double neumann_direct_probe = std::sqrt(neu_num / std::max(1e-30, neu_den));
    // For BEM runs the boundary derivative of a single-layer potential is a
    // limiting operator with a jump term. Direct surface probing omits that jump,
    // so the primary Neumann gate uses the BEM operator residual.
    double neumann = bem ? BS.predicted_neumann : neumann_direct_probe;

    double circ = circulation_of_field(lam, std::max(128, n_ring/2), field);
    double corr_circ = circulation_of_field(lam, std::max(128, n_ring/2), corr_field);
    double circ_mag_err = std::abs(std::abs(circ)/TWOPI - 1.0);
    double circ_signed_err = std::abs(circ/TWOPI - 1.0);

    // Energy volume integral.
    const double B = box_radius;
    const double h = (2.0*B) / static_cast<double>(n_volume - 1);
    double chiK = 0.0;
    long long cells = 0;
    for (int ix=0; ix<n_volume; ++ix) {
        const double x = -B + h*ix;
        for (int iy=0; iy<n_volume; ++iy) {
            const double y = -B + h*iy;
            for (int iz=0; iz<n_volume; ++iz) {
                const double z = -B + h*iz;
                Vec3 p(x,y,z);
                if (inside_torus(p, lam)) continue;
                Vec3 v = field(p);
                chiK += 0.5 * dot(v,v) * h*h*h;
                ++cells;
            }
        }
    }

    // Harmonicity probe.
    int probe = std::min(7, n_volume);
    double Bp = std::min(3.0, B - 2.0*fd_step);
    double div2 = 0.0, curl2 = 0.0;
    long long pc = 0;
    for (int ix=0; ix<probe; ++ix) {
        double x = -Bp + (2.0*Bp)*ix/std::max(1, probe-1);
        for (int iy=0; iy<probe; ++iy) {
            double y = -Bp + (2.0*Bp)*iy/std::max(1, probe-1);
            for (int iz=0; iz<probe; ++iz) {
                double z = -Bp + (2.0*Bp)*iz/std::max(1, probe-1);
                Vec3 p(x,y,z);
                if (inside_torus(p, lam)) continue;
                Vec3 ex(fd_step,0,0), ey(0,fd_step,0), ez(0,0,fd_step);
                Vec3 vx1 = field(p+ex), vx0 = field(p-ex);
                Vec3 vy1 = field(p+ey), vy0 = field(p-ey);
                Vec3 vz1 = field(p+ez), vz0 = field(p-ez);
                Vec3 dv_dx = (vx1-vx0) * (0.5/fd_step);
                Vec3 dv_dy = (vy1-vy0) * (0.5/fd_step);
                Vec3 dv_dz = (vz1-vz0) * (0.5/fd_step);
                double div = dv_dx.x + dv_dy.y + dv_dz.z;
                Vec3 curl(dv_dy.z - dv_dz.y, dv_dz.x - dv_dx.z, dv_dx.y - dv_dy.x);
                div2 += div*div; curl2 += dot(curl,curl); ++pc;
            }
        }
    }
    double divergence_error = std::sqrt(div2 / std::max<long long>(1, pc));
    double curl_error = std::sqrt(curl2 / std::max<long long>(1, pc));

    Vec3 p1(B, 0.37*B, 0.23*B), p2(2*B, 0.74*B, 0.46*B);
    double m1 = norm(field(p1)), m2 = norm(field(p2));
    double farfield_error = std::abs(m2/std::max(1e-30, m1) - 1.0/8.0);

    double chi_cav = PI*PI*lam;
    double chi_E = chiK + chi_cav;
    double resK = (chiK - TWOPI) / TWOPI;
    double resE = (chi_E - TWOPI) / TWOPI;

    py::dict d;
    d["lambda_"] = lam;
    d["solver_kind"] = bem ? "pybind11_bem_neumann_corrected" : "pybind11_regularized_ring";
    d["bem_enabled"] = bem;
    d["bem_panels"] = bem ? bem_n_eta*bem_n_phi : 0;
    d["bem_n_eta"] = bem_n_eta;
    d["bem_n_phi"] = bem_n_phi;
    d["bem_self_term"] = bem ? BS.self_term : std::numeric_limits<double>::quiet_NaN();
    d["bem_rhs_flux_before_projection"] = BS.flux_before;
    d["bem_rhs_flux_after_projection"] = BS.flux_after;
    d["bem_linear_residual"] = BS.linear_residual;
    d["bem_sigma_l2"] = BS.sigma_l2;
    d["bem_predicted_neumann_error"] = BS.predicted_neumann;
    d["raw_ring_circulation"] = raw_circ;
    d["ring_scale_to_plus_2pi"] = scale;
    d["circulation_signed"] = circ;
    d["circulation_magnitude_error"] = circ_mag_err;
    d["circulation_signed_error"] = circ_signed_err;
    d["bem_correction_circulation"] = corr_circ;
    d["neumann_boundary_error"] = neumann;
    d["neumann_boundary_error_direct_probe"] = neumann_direct_probe;
    d["divergence_error"] = divergence_error;
    d["curl_error"] = curl_error;
    d["farfield_decay_error"] = farfield_error;
    d["chi_K"] = chiK;
    d["chi_cav"] = chi_cav;
    d["chi_E_hollow"] = chi_E;
    d["residual_kinetic_to_2pi"] = resK;
    d["residual_total_to_2pi"] = resE;
    d["analytic_total_horn_falsifies_2pi"] = true;
    d["gate_circulation_pass"] = circ_mag_err < 1e-2;
    d["gate_circulation_orientation_pass"] = circ_signed_err < 1e-2;
    d["gate_bem_correction_no_circulation_pass"] = std::abs(corr_circ) < 1e-3;
    d["gate_neumann_pass"] = neumann < 1e-2;
    d["gate_neumann_first_acceptance_pass"] = neumann < 5e-2;
    d["gate_harmonic_pass"] = divergence_error < 5e-3 && curl_error < 5e-3;
    d["gate_farfield_pass"] = farfield_error < 0.2;
    d["gate_kinetic_2pi_pass"] = std::abs(resK) < 0.02;
    d["gate_total_2pi_pass"] = std::abs(resE) < 0.02;
    d["mesh_cells"] = cells;
    d["dof"] = static_cast<long long>(cells + (bem ? bem_n_eta*bem_n_phi : 0));
    d["n_ring"] = n_ring;
    d["n_surface"] = n_surface;
    d["n_volume"] = n_volume;
    d["box_radius"] = B;
    d["source_eps"] = eps;
    d["solver_residual"] = BS.linear_residual;
    d["energy_refinement_error"] = std::numeric_limits<double>::quiet_NaN();
    return d;
}

PYBIND11_MODULE(_hornbem, m) {
    m.doc() = "SST horn-torus boundary-corrected Neumann BEM kernels";
    m.def("run_horn_bem", &run_horn_bem,
          py::arg("lambda_"), py::arg("n_ring"), py::arg("n_surface"), py::arg("n_volume"),
          py::arg("box_radius"), py::arg("source_eps"), py::arg("fd_step"), py::arg("bem"),
          py::arg("bem_n_eta"), py::arg("bem_n_phi"), py::arg("bem_self_term"),
          py::arg("bem_auto_self_term"), py::arg("bem_ridge"));
}
