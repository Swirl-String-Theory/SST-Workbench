#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace py = pybind11;
static constexpr double PI = 3.141592653589793238462643383279502884;

struct Vec3 {
    double x, y, z;
};

static inline double dist(const Vec3& a, const Vec3& b) {
    const double dx = a.x - b.x;
    const double dy = a.y - b.y;
    const double dz = a.z - b.z;
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

static bool solve_dense(std::vector<double>& A, std::vector<double>& b, std::vector<double>& x, int N) {
    x.assign(N, 0.0);
    for (int k = 0; k < N; ++k) {
        int piv = k;
        double best = std::abs(A[k*N + k]);
        for (int i = k + 1; i < N; ++i) {
            const double cand = std::abs(A[i*N + k]);
            if (cand > best) { best = cand; piv = i; }
        }
        if (best < 1e-18) return false;
        if (piv != k) {
            for (int j = k; j < N; ++j) std::swap(A[k*N+j], A[piv*N+j]);
            std::swap(b[k], b[piv]);
        }
        const double diag = A[k*N + k];
        for (int i = k + 1; i < N; ++i) {
            const double f = A[i*N + k] / diag;
            A[i*N + k] = 0.0;
            for (int j = k + 1; j < N; ++j) A[i*N + j] -= f * A[k*N + j];
            b[i] -= f * b[k];
        }
    }
    for (int i = N - 1; i >= 0; --i) {
        double s = b[i];
        for (int j = i + 1; j < N; ++j) s -= A[i*N + j] * x[j];
        x[i] = s / A[i*N + i];
    }
    return true;
}

py::dict run_ssdl_cpp(double R, int n_theta, int n_phi) {
    if (R <= 0.0) throw std::runtime_error("R must be positive.");
    if (n_theta < 4 || n_phi < 8) throw std::runtime_error("mesh too small.");

    const int N = n_theta * n_phi;
    std::vector<Vec3> pts(N);
    std::vector<double> areas(N);
    std::vector<double> phi_input(N);

    const double d_theta = PI / static_cast<double>(n_theta);
    const double d_phi = 2.0 * PI / static_cast<double>(n_phi);
    for (int i = 0; i < n_theta; ++i) {
        const double theta = d_theta * (i + 0.5);
        const double st = std::sin(theta);
        const double ct = std::cos(theta);
        for (int j = 0; j < n_phi; ++j) {
            const double phi = d_phi * (j + 0.5);
            const int idx = i * n_phi + j;
            const double cp = std::cos(phi);
            const double sp = std::sin(phi);
            pts[idx] = {R * st * cp, R * st * sp, R * ct};
            areas[idx] = R * R * st * d_theta * d_phi;

            // Monopole + deliberately large tangential contamination.
            // Pi_0 should recover the monopole response despite these modes.
            phi_input[idx] = 1.0 + 0.5 * ct + 0.2 * st * cp + 0.1 * (3.0*ct*ct - 1.0);
        }
    }

    // Single-layer potential collocation: V sigma = Phi.
    std::vector<double> V(N * N);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            if (i == j) {
                // Flat-disk self term for constant element.
                V[i*N + j] = std::sqrt(areas[i] / PI) / 2.0;
            } else {
                V[i*N + j] = areas[j] / (4.0 * PI * dist(pts[i], pts[j]));
            }
        }
    }

    std::vector<double> sigma;
    std::vector<double> b = phi_input;
    if (!solve_dense(V, b, sigma, N)) throw std::runtime_error("BEM solver failed.");

    double total_area = 0.0;
    double sum_phi = 0.0;
    double sum_sigma = 0.0;
    for (int i = 0; i < N; ++i) {
        total_area += areas[i];
        sum_phi += phi_input[i] * areas[i];
        sum_sigma += sigma[i] * areas[i];
    }
    const double phi_0 = sum_phi / total_area;
    const double sigma_0 = sum_sigma / total_area;
    const double R_num = phi_0 / sigma_0;

    py::dict res;
    res["backend"] = "cpp_bem";
    res["R_target"] = R;
    res["R_numerical_projected"] = R_num;
    res["projection_error"] = std::abs(R_num - R) / R;
    res["phi_0_monopole"] = phi_0;
    res["sigma_0_monopole"] = sigma_0;
    res["mesh_n_theta"] = n_theta;
    res["mesh_n_phi"] = n_phi;
    res["interpretation"] = "BEM consistency check for Pi_0 Lambda^{-1} Pi_0; not a constitutive proof.";
    return res;
}

PYBIND11_MODULE(_ssdlbem, m) {
    m.def("run_ssdl_cpp", &run_ssdl_cpp, py::arg("R"), py::arg("n_theta"), py::arg("n_phi"));
}
