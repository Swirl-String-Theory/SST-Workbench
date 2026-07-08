#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace py = pybind11;
static constexpr double PI = 3.14159265358979323846;

struct Vec3 {
    double x, y, z;
    Vec3 operator-(const Vec3& o) const { return {x-o.x, y-o.y, z-o.z}; }
};
static inline double dist(const Vec3& a, const Vec3& b) {
    return std::sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y) + (a.z-b.z)*(a.z-b.z));
}

bool solve_dense(std::vector<double>& A, std::vector<double>& b, std::vector<double>& x, int N) {
    x.assign(N, 0.0);
    for (int k = 0; k < N; ++k) {
        int piv = k; double best = std::abs(A[k*N + k]);
        for (int i = k+1; i < N; ++i) {
            if (std::abs(A[i*N + k]) > best) { best = std::abs(A[i*N + k]); piv = i; }
        }
        if (best < 1e-16 * (std::abs(A[0]) + 1.0)) return false;
        if (piv != k) {
            for (int j = k; j < N; ++j) std::swap(A[k*N+j], A[piv*N+j]);
            std::swap(b[k], b[piv]);
        }
        double diag = A[k*N + k];
        for (int i = k+1; i < N; ++i) {
            double f = A[i*N + k] / diag;
            A[i*N + k] = 0.0;
            for (int j = k+1; j < N; ++j) A[i*N + j] -= f * A[k*N + j];
            b[i] -= f * b[k];
        }
    }
    for (int i = N-1; i >= 0; --i) {
        double s = b[i];
        for (int j = i+1; j < N; ++j) s -= A[i*N + j] * x[j];
        x[i] = s / A[i*N + i];
    }
    return true;
}

py::dict run_ssdl_cpp(double R, int n_theta, int n_phi) {
    // BEM is scale-invariant in R_num/R; mesh on unit sphere for conditioning.
    const double R_mesh = 1.0;
    int N = n_theta * n_phi;
    std::vector<Vec3> pts(N);
    std::vector<double> areas(N);
    std::vector<double> phi_input(N);

    // 1. Mesh generation (UV Sphere)
    double d_theta = PI / n_theta;
    double d_phi = 2.0 * PI / n_phi;
    for (int i = 0; i < n_theta; ++i) {
        double theta = d_theta * (i + 0.5);
        for (int j = 0; j < n_phi; ++j) {
            double phi = d_phi * (j + 0.5);
            int idx = i * n_phi + j;
            pts[idx] = {R_mesh * std::sin(theta) * std::cos(phi),
                        R_mesh * std::sin(theta) * std::sin(phi),
                        R_mesh * std::cos(theta)};
            areas[idx] = R_mesh * R_mesh * std::sin(theta) * d_theta * d_phi;

            // Perturbated Dirichlet Condition: Monopole (1.0) + Tangential Modes (l=1, l=2)
            phi_input[idx] = 1.0 + 0.5 * std::cos(theta) + 0.2 * std::sin(theta) * std::cos(phi);
        }
    }

    // 2. Collocation Matrix for Single Layer Potential V
    std::vector<double> V(N * N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            if (i == j) {
                V[i*N + j] = std::sqrt(areas[i] / PI) / 2.0; // Analytic self-term flat disc
            } else {
                V[i*N + j] = areas[j] / (4.0 * PI * dist(pts[i], pts[j]));
            }
        }
    }

    // 3. Solve V * sigma = Phi
    std::vector<double> sigma;
    std::vector<double> b = phi_input;
    if (!solve_dense(V, b, sigma, N)) throw std::runtime_error("BEM solver failed.");

    // 4. Projectors (Pi_0)
    double total_area = 0.0;
    double sum_phi = 0.0;
    double sum_sigma = 0.0;
    for (int i = 0; i < N; ++i) {
        total_area += areas[i];
        sum_phi += phi_input[i] * areas[i];
        sum_sigma += sigma[i] * areas[i];
    }
    double phi_0 = sum_phi / total_area;
    double sigma_0 = sum_sigma / total_area;

      // DtN Monopole Inverse R_num = Pi_0[Phi] / Pi_0[Lambda(Phi)]
    // For single layer formulation on sphere, Lambda = sigma.
    double R_unit = phi_0 / sigma_0;
    double R_num = R_unit * R;

    py::dict res;
    res["backend"] = "cpp";
    res["R_target"] = R;
    res["R_numerical_projected"] = R_num;
    res["projection_error"] = std::abs(R_num - R) / R;
    res["phi_0_monopole"] = phi_0;
    res["sigma_0_monopole"] = sigma_0;
    return res;
}

PYBIND11_MODULE(_ssdlbem, m) {
    m.def("run_ssdl_cpp", &run_ssdl_cpp);
}
