/*
 * SST-71 benchmark: pybind11-accelerated axisymmetric 2D quadrature kernel.
 * Consumes precomputed NumPy arrays from Python; does not evaluate Coulomb or probe.
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <complex>
#include <stdexcept>

namespace py = pybind11;
using complex_t = std::complex<double>;

/*
 * Single partial amplitude: I = phi_factor * sum_{i,j} [ w_r[i] * w_x[j] * r[i]^2
 *   * conj(radial_continuum[i] * angular_factor[j]) * probe_grid[i,j] * psi1s_r[i] ]
 */
complex_t compute_partial_amplitude_axisymmetric_cpp(
    py::array_t<complex_t> radial_continuum,
    py::array_t<complex_t> angular_factor,
    py::array_t<complex_t> probe_grid,
    py::array_t<complex_t> psi1s_r,
    py::array_t<double> r_nodes,
    py::array_t<double> r_weights,
    py::array_t<double> x_weights,
    complex_t phi_factor
) {
    auto r_c = radial_continuum.unchecked<1>();
    auto ang = angular_factor.unchecked<1>();
    auto pr = probe_grid.unchecked<2>();
    auto p1s = psi1s_r.unchecked<1>();
    auto r_n = r_nodes.unchecked<1>();
    auto r_w = r_weights.unchecked<1>();
    auto x_w = x_weights.unchecked<1>();

    py::ssize_t N_r = radial_continuum.shape(0);
    py::ssize_t N_x = angular_factor.shape(0);

    if (psi1s_r.shape(0) != N_r || r_nodes.shape(0) != N_r || r_weights.shape(0) != N_r)
        throw std::invalid_argument("radial arrays must have length N_r");
    if (x_weights.shape(0) != N_x)
        throw std::invalid_argument("x_weights length must equal N_x");
    if (probe_grid.shape(0) != N_r || probe_grid.shape(1) != N_x)
        throw std::invalid_argument("probe_grid must be (N_r, N_x)");

    complex_t accum = 0.0;
    for (py::ssize_t i = 0; i < N_r; ++i) {
        double r = r_n(i);
        double r2 = r * r;
        complex_t rc = r_c(i);
        complex_t ps = p1s(i);
        double wr = r_w(i);
        for (py::ssize_t j = 0; j < N_x; ++j) {
            complex_t conj_RY = std::conj(rc * ang(j));
            accum += wr * x_w(j) * r2 * conj_RY * pr(i, j) * ps;
        }
    }
    return phi_factor * accum;
}

/*
 * Total rate: Gamma = coupling_prefactor_sq * sum_l |I_l|^2
 * For each l, I_l = same 2D quadrature with radial_continuum_by_l[l], angular_by_l[l].
 */
double compute_total_rate_axisymmetric_cpp(
    py::array_t<complex_t> radial_continuum_by_l,
    py::array_t<complex_t> angular_by_l,
    py::array_t<complex_t> probe_grid,
    py::array_t<complex_t> psi1s_r,
    py::array_t<double> r_nodes,
    py::array_t<double> r_weights,
    py::array_t<double> x_weights,
    double coupling_prefactor_sq,
    complex_t phi_factor
) {
    auto r_cl = radial_continuum_by_l.unchecked<2>();
    auto ang_l = angular_by_l.unchecked<2>();
    auto pr = probe_grid.unchecked<2>();
    auto p1s = psi1s_r.unchecked<1>();
    auto r_n = r_nodes.unchecked<1>();
    auto r_w = r_weights.unchecked<1>();
    auto x_w = x_weights.unchecked<1>();

    py::ssize_t N_l = radial_continuum_by_l.shape(0);
    py::ssize_t N_r = radial_continuum_by_l.shape(1);
    py::ssize_t N_x = angular_by_l.shape(1);

    if (angular_by_l.shape(0) != N_l)
        throw std::invalid_argument("angular_by_l first dim must equal N_l");
    if (angular_by_l.shape(1) != N_x)
        throw std::invalid_argument("angular_by_l second dim must equal N_x");
    if (psi1s_r.shape(0) != N_r || r_nodes.shape(0) != N_r || r_weights.shape(0) != N_r)
        throw std::invalid_argument("radial arrays length must equal N_r");
    if (x_weights.shape(0) != N_x)
        throw std::invalid_argument("x_weights length must equal N_x");
    if (probe_grid.shape(0) != N_r || probe_grid.shape(1) != N_x)
        throw std::invalid_argument("probe_grid must be (N_r, N_x)");

    double total = 0.0;
    for (py::ssize_t l = 0; l < N_l; ++l) {
        complex_t I_l = 0.0;
        for (py::ssize_t i = 0; i < N_r; ++i) {
            double r = r_n(i);
            double r2 = r * r;
            complex_t rc = r_cl(l, i);
            complex_t ps = p1s(i);
            double wr = r_w(i);
            for (py::ssize_t j = 0; j < N_x; ++j) {
                complex_t conj_RY = std::conj(rc * ang_l(l, j));
                I_l += wr * x_w(j) * r2 * conj_RY * pr(i, j) * ps;
            }
        }
        complex_t I_scaled = phi_factor * I_l;
        total += std::norm(I_scaled);
    }
    return coupling_prefactor_sq * total;
}

/*
 * 3D (r, theta, phi) total rate for broken axisymmetry: Gamma = coupling_prefactor_sq * sum_{lm} |I_lm|^2
 * I_lm = sum_{i,j,k} w_r[i]*w_theta[j]*w_phi[k] * r[i]^2 * sin(theta[j])
 *        * conj(radial[lm,i]*angular[lm,j,k]) * probe[i,j,k] * psi1s[i]
 */
double compute_total_rate_3d_cpp(
    py::array_t<complex_t> radial_continuum_by_lm,
    py::array_t<complex_t> angular_by_lm,
    py::array_t<complex_t> probe_grid,
    py::array_t<complex_t> psi1s_r,
    py::array_t<double> r_nodes,
    py::array_t<double> r_weights,
    py::array_t<double> theta_nodes,
    py::array_t<double> theta_weights,
    py::array_t<double> phi_weights,
    double coupling_prefactor_sq
) {
    auto r_clm = radial_continuum_by_lm.unchecked<2>();
    auto ang_lm = angular_by_lm.unchecked<3>();
    auto pr = probe_grid.unchecked<3>();
    auto p1s = psi1s_r.unchecked<1>();
    auto r_n = r_nodes.unchecked<1>();
    auto r_w = r_weights.unchecked<1>();
    auto th_n = theta_nodes.unchecked<1>();
    auto th_w = theta_weights.unchecked<1>();
    auto phi_w = phi_weights.unchecked<1>();

    py::ssize_t N_lm = radial_continuum_by_lm.shape(0);
    py::ssize_t N_r = radial_continuum_by_lm.shape(1);
    py::ssize_t N_theta = angular_by_lm.shape(1);
    py::ssize_t N_phi = angular_by_lm.shape(2);

    if (angular_by_lm.shape(0) != N_lm)
        throw std::invalid_argument("angular_by_lm first dim must equal N_lm");
    if (psi1s_r.shape(0) != N_r || r_nodes.shape(0) != N_r || r_weights.shape(0) != N_r)
        throw std::invalid_argument("radial arrays must have length N_r");
    if (theta_nodes.shape(0) != N_theta || theta_weights.shape(0) != N_theta)
        throw std::invalid_argument("theta arrays must have length N_theta");
    if (phi_weights.shape(0) != N_phi)
        throw std::invalid_argument("phi_weights must have length N_phi");
    if (probe_grid.shape(0) != N_r || probe_grid.shape(1) != N_theta || probe_grid.shape(2) != N_phi)
        throw std::invalid_argument("probe_grid must be (N_r, N_theta, N_phi)");

    double total = 0.0;
    for (py::ssize_t lm = 0; lm < N_lm; ++lm) {
        complex_t I_lm = 0.0;
        for (py::ssize_t i = 0; i < N_r; ++i) {
            double r = r_n(i);
            double r2 = r * r;
            complex_t rc = r_clm(lm, i);
            complex_t ps = p1s(i);
            double wr = r_w(i);
            for (py::ssize_t j = 0; j < N_theta; ++j) {
                double sin_th = std::sin(th_n(j));
                double jac = r2 * sin_th * wr * th_w(j);
                for (py::ssize_t k = 0; k < N_phi; ++k) {
                    complex_t conj_RY = std::conj(rc * ang_lm(lm, j, k));
                    I_lm += jac * phi_w(k) * conj_RY * pr(i, j, k) * ps;
                }
            }
        }
        total += std::norm(I_lm);
    }
    return coupling_prefactor_sq * total;
}

PYBIND11_MODULE(sst_benchmark_core, m) {
    m.doc() = "SST-71 axisymmetric 2D and general 3D quadrature kernels (pybind11).";

    m.def(
        "compute_partial_amplitude_axisymmetric_cpp",
        &compute_partial_amplitude_axisymmetric_cpp,
        py::arg("radial_continuum"),
        py::arg("angular_factor"),
        py::arg("probe_grid"),
        py::arg("psi1s_r"),
        py::arg("r_nodes"),
        py::arg("r_weights"),
        py::arg("x_weights"),
        py::arg("phi_factor"),
        "Compute I = phi_factor * sum_{i,j} w_r[i]*w_x[j]*r[i]^2 * conj(radial[i]*angular[j]) * probe[i,j] * psi1s[i]. "
        "Arrays: radial_continuum (N_r), angular_factor (N_x), probe_grid (N_r, N_x), psi1s_r (N_r), r_nodes (N_r), r_weights (N_r), x_weights (N_x)."
    );

    m.def(
        "compute_total_rate_axisymmetric_cpp",
        &compute_total_rate_axisymmetric_cpp,
        py::arg("radial_continuum_by_l"),
        py::arg("angular_by_l"),
        py::arg("probe_grid"),
        py::arg("psi1s_r"),
        py::arg("r_nodes"),
        py::arg("r_weights"),
        py::arg("x_weights"),
        py::arg("coupling_prefactor_sq"),
        py::arg("phi_factor"),
        "Compute Gamma = coupling_prefactor_sq * sum_l |I_l|^2 with I_l from 2D quadrature. "
        "radial_continuum_by_l (N_l, N_r), angular_by_l (N_l, N_x), probe_grid (N_r, N_x), psi1s_r (N_r), r_nodes (N_r), r_weights (N_r), x_weights (N_x)."
    );

    m.def(
        "compute_total_rate_3d_cpp",
        &compute_total_rate_3d_cpp,
        py::arg("radial_continuum_by_lm"),
        py::arg("angular_by_lm"),
        py::arg("probe_grid"),
        py::arg("psi1s_r"),
        py::arg("r_nodes"),
        py::arg("r_weights"),
        py::arg("theta_nodes"),
        py::arg("theta_weights"),
        py::arg("phi_weights"),
        py::arg("coupling_prefactor_sq"),
        "Compute Gamma for 3D (broken axisymmetry): Gamma = C^2 * sum_lm |I_lm|^2. "
        "radial_continuum_by_lm (N_lm, N_r), angular_by_lm (N_lm, N_theta, N_phi), probe_grid (N_r, N_theta, N_phi), psi1s_r (N_r), r/theta/phi nodes and weights."
    );
}
