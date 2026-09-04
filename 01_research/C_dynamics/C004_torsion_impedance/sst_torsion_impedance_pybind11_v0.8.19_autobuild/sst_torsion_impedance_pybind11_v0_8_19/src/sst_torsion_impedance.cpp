#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef BUILD_PYBIND11_MODULE
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;
#endif

namespace sst_rt {

constexpr double pi = 3.141592653589793238462643383279502884;
constexpr double c = 299792458.0;
constexpr double vchar = 1.09384563e6;
constexpr double r_c = 1.40897017e-15;
constexpr double rho_f = 7.0e-7;
constexpr double rho_core = 3.8934358266918687e18;
constexpr double m_e = 9.1093837015e-31;
constexpr double electron_rest_energy_j = m_e * c * c;

struct Options {
    double length_scale_m = r_c;
    double core_radius_m = r_c;
    double density_kg_m3 = rho_f;
    double c_T_m_s = c;
    double rest_energy_j = electron_rest_energy_j;
    double impedance_scale = 1.0;
    double finite_difference_velocity_m_s = 1.0;
};

struct Result {
    std::vector<double> tensor_kg;
    std::vector<double> tensor_fd_kg;
    std::vector<double> eigenvalues_kg;
    std::vector<double> eigenvectors_rowmajor;
    double length_m = 0.0;
    double length_over_r_c = 0.0;
    double lambda_iso_kg = 0.0;
    double target_lambda_iso_kg = 0.0;
    double chi_T = 0.0;
    double isotropy_residual = 0.0;
    double fd_max_abs_error_kg = 0.0;
    double required_impedance_scale_for_chi_one = 0.0;
    double required_density_for_chi_one_kg_m3 = 0.0;
};

inline std::size_t midx(std::size_t i, std::size_t j) { return 3 * i + j; }

inline void validate(const Options& o) {
    if (!(o.length_scale_m > 0.0)) throw std::invalid_argument("length_scale_m must be positive");
    if (!(o.core_radius_m > 0.0)) throw std::invalid_argument("core_radius_m must be positive");
    if (!(o.density_kg_m3 > 0.0)) throw std::invalid_argument("density_kg_m3 must be positive");
    if (!(o.c_T_m_s > 0.0)) throw std::invalid_argument("c_T_m_s must be positive");
    if (!(o.rest_energy_j > 0.0)) throw std::invalid_argument("rest_energy_j must be positive");
    if (!(o.impedance_scale > 0.0)) throw std::invalid_argument("impedance_scale must be positive");
    if (!(o.finite_difference_velocity_m_s > 0.0)) throw std::invalid_argument("finite_difference_velocity_m_s must be positive");
}

inline std::array<double,3> p_at(const std::vector<double>& p, std::size_t i, double scale) {
    return {p[3*i + 0] * scale, p[3*i + 1] * scale, p[3*i + 2] * scale};
}

inline std::array<double,3> sub3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}

inline double dot3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
}

inline double norm3(const std::array<double,3>& a) {
    return std::sqrt(dot3(a, a));
}

std::vector<double> identity3() {
    std::vector<double> I(9, 0.0);
    I[0] = I[4] = I[8] = 1.0;
    return I;
}

void jacobi_eigen_3x3(const std::vector<double>& A_in,
                      std::vector<double>& evals,
                      std::vector<double>& evecs) {
    if (A_in.size() != 9) throw std::invalid_argument("jacobi_eigen_3x3 expects 9 entries");
    std::vector<double> A = A_in;
    evecs = identity3();

    for (int sweep = 0; sweep < 80; ++sweep) {
        int p = 0;
        int q = 1;
        double max_off = std::abs(A[midx(0,1)]);
        for (int i = 0; i < 3; ++i) {
            for (int j = i + 1; j < 3; ++j) {
                const double v = std::abs(A[midx(i,j)]);
                if (v > max_off) {
                    max_off = v;
                    p = i;
                    q = j;
                }
            }
        }
        const double scale = std::max({std::abs(A[0]), std::abs(A[4]), std::abs(A[8]), 1.0});
        if (max_off <= 1e-15 * scale) break;

        const double app = A[midx(p,p)];
        const double aqq = A[midx(q,q)];
        const double apq = A[midx(p,q)];
        if (apq == 0.0) continue;
        const double tau = (aqq - app) / (2.0 * apq);
        const double t = ((tau >= 0.0) ? 1.0 : -1.0) / (std::abs(tau) + std::sqrt(1.0 + tau*tau));
        const double cs = 1.0 / std::sqrt(1.0 + t*t);
        const double sn = t * cs;

        for (int k = 0; k < 3; ++k) {
            if (k == p || k == q) continue;
            const double akp = A[midx(k,p)];
            const double akq = A[midx(k,q)];
            const double new_kp = cs*akp - sn*akq;
            const double new_kq = sn*akp + cs*akq;
            A[midx(k,p)] = A[midx(p,k)] = new_kp;
            A[midx(k,q)] = A[midx(q,k)] = new_kq;
        }

        A[midx(p,p)] = cs*cs*app - 2.0*sn*cs*apq + sn*sn*aqq;
        A[midx(q,q)] = sn*sn*app + 2.0*sn*cs*apq + cs*cs*aqq;
        A[midx(p,q)] = A[midx(q,p)] = 0.0;

        for (int k = 0; k < 3; ++k) {
            const double vip = evecs[midx(k,p)];
            const double viq = evecs[midx(k,q)];
            evecs[midx(k,p)] = cs*vip - sn*viq;
            evecs[midx(k,q)] = sn*vip + cs*viq;
        }
    }

    std::array<int,3> order = {0,1,2};
    std::sort(order.begin(), order.end(), [&](int a, int b){ return A[midx(a,a)] < A[midx(b,b)]; });
    evals.assign(3, 0.0);
    std::vector<double> sorted_vecs(9, 0.0);
    for (int col = 0; col < 3; ++col) {
        const int src = order[static_cast<std::size_t>(col)];
        evals[static_cast<std::size_t>(col)] = A[midx(src,src)];
        for (int row = 0; row < 3; ++row) {
            sorted_vecs[midx(row,col)] = evecs[midx(row,src)];
        }
    }
    evecs.swap(sorted_vecs);
}

Options canonical_medium_options() {
    Options o;
    o.density_kg_m3 = rho_f;
    return o;
}

Options canonical_core_density_options() {
    Options o;
    o.density_kg_m3 = rho_core;
    return o;
}

std::vector<double> generate_trefoil(std::size_t n, double major_radius = 2.0, double minor_radius = 0.75) {
    if (n < 8) throw std::invalid_argument("generate_trefoil requires n >= 8");
    std::vector<double> p(3*n, 0.0);
    for (std::size_t k = 0; k < n; ++k) {
        const double t = 2.0 * pi * static_cast<double>(k) / static_cast<double>(n);
        p[3*k + 0] = (major_radius + minor_radius * std::cos(3.0*t)) * std::cos(2.0*t);
        p[3*k + 1] = (major_radius + minor_radius * std::cos(3.0*t)) * std::sin(2.0*t);
        p[3*k + 2] = minor_radius * std::sin(3.0*t);
    }
    return p;
}

std::vector<double> generate_figure_eight(std::size_t n, double scale = 1.0) {
    if (n < 8) throw std::invalid_argument("generate_figure_eight requires n >= 8");
    std::vector<double> p(3*n, 0.0);
    for (std::size_t k = 0; k < n; ++k) {
        const double t = 2.0 * pi * static_cast<double>(k) / static_cast<double>(n);
        p[3*k + 0] = scale * (2.0 + std::cos(2.0*t)) * std::cos(3.0*t);
        p[3*k + 1] = scale * (2.0 + std::cos(2.0*t)) * std::sin(3.0*t);
        p[3*k + 2] = scale * std::sin(4.0*t);
    }
    return p;
}

double polyline_length(const std::vector<double>& points, const Options& o) {
    if (points.size() < 9 || points.size() % 3 != 0) throw std::invalid_argument("points must be flat [x,y,z,...], N>=3");
    const std::size_t n = points.size() / 3;
    double L = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const auto a = p_at(points, i, o.length_scale_m);
        const auto b = p_at(points, (i + 1) % n, o.length_scale_m);
        L += norm3(sub3(b, a));
    }
    return L;
}

std::vector<double> torsion_tensor_quadrature(const std::vector<double>& points, const Options& o) {
    validate(o);
    if (points.size() < 9 || points.size() % 3 != 0) throw std::invalid_argument("points must be flat [x,y,z,...], N>=3");
    const std::size_t n = points.size() / 3;
    const double area = pi * o.core_radius_m * o.core_radius_m;
    const double pref = o.impedance_scale * o.density_kg_m3 * area;
    std::vector<double> M(9, 0.0);

    for (std::size_t i = 0; i < n; ++i) {
        const auto a = p_at(points, i, o.length_scale_m);
        const auto b = p_at(points, (i + 1) % n, o.length_scale_m);
        const auto d = sub3(b, a);
        const double ds = norm3(d);
        if (ds <= 0.0) continue;
        const std::array<double,3> t = {d[0]/ds, d[1]/ds, d[2]/ds};
        const double w = pref * ds;
        for (std::size_t r = 0; r < 3; ++r) {
            for (std::size_t col = 0; col < 3; ++col) {
                M[midx(r,col)] += w * ((r == col ? 1.0 : 0.0) - t[r]*t[col]);
            }
        }
    }
    return M;
}

double torsion_energy_increment(const std::vector<double>& points,
                                const std::array<double,3>& u,
                                const Options& o) {
    validate(o);
    if (points.size() < 9 || points.size() % 3 != 0) throw std::invalid_argument("points must be flat [x,y,z,...], N>=3");
    const std::size_t n = points.size() / 3;
    const double area = pi * o.core_radius_m * o.core_radius_m;
    const double pref = 0.5 * o.impedance_scale * o.density_kg_m3 * area;
    double dE = 0.0;

    for (std::size_t i = 0; i < n; ++i) {
        const auto a = p_at(points, i, o.length_scale_m);
        const auto b = p_at(points, (i + 1) % n, o.length_scale_m);
        const auto d = sub3(b, a);
        const double ds = norm3(d);
        if (ds <= 0.0) continue;
        const std::array<double,3> t = {d[0]/ds, d[1]/ds, d[2]/ds};
        const double u_dot_t = dot3(u, t);
        const double u2 = dot3(u, u);
        dE += pref * ds * std::max(0.0, u2 - u_dot_t*u_dot_t);
    }
    return dE;
}

std::vector<double> torsion_tensor_finite_difference(const std::vector<double>& points, const Options& o) {
    validate(o);
    const double h = o.finite_difference_velocity_m_s;
    std::vector<double> M(9, 0.0);
    const std::array<double,3> zero{0.0, 0.0, 0.0};
    const double E0 = torsion_energy_increment(points, zero, o);

    auto u1 = [h](int i, double si) {
        std::array<double,3> u{0.0, 0.0, 0.0};
        u[static_cast<std::size_t>(i)] = si * h;
        return u;
    };
    auto u2 = [h](int i, double si, int j, double sj) {
        std::array<double,3> u{0.0, 0.0, 0.0};
        u[static_cast<std::size_t>(i)] = si * h;
        u[static_cast<std::size_t>(j)] = sj * h;
        return u;
    };

    for (int i = 0; i < 3; ++i) {
        M[midx(i,i)] = (torsion_energy_increment(points, u1(i,+1), o)
                     + torsion_energy_increment(points, u1(i,-1), o)
                     - 2.0*E0) / (h*h);
        for (int j = i + 1; j < 3; ++j) {
            const double hij = (torsion_energy_increment(points, u2(i,+1,j,+1), o)
                              - torsion_energy_increment(points, u2(i,+1,j,-1), o)
                              - torsion_energy_increment(points, u2(i,-1,j,+1), o)
                              + torsion_energy_increment(points, u2(i,-1,j,-1), o)) / (4.0*h*h);
            M[midx(i,j)] = M[midx(j,i)] = hij;
        }
    }
    return M;
}

Result audit_points(const std::vector<double>& points, const Options& o) {
    validate(o);
    Result r;
    r.tensor_kg = torsion_tensor_quadrature(points, o);
    r.tensor_fd_kg = torsion_tensor_finite_difference(points, o);
    r.length_m = polyline_length(points, o);
    r.length_over_r_c = r.length_m / r_c;
    r.lambda_iso_kg = (r.tensor_kg[0] + r.tensor_kg[4] + r.tensor_kg[8]) / 3.0;
    r.target_lambda_iso_kg = 2.0 * o.rest_energy_j / (o.c_T_m_s * o.c_T_m_s);
    r.chi_T = r.lambda_iso_kg / r.target_lambda_iso_kg;

    jacobi_eigen_3x3(r.tensor_kg, r.eigenvalues_kg, r.eigenvectors_rowmajor);
    if (r.lambda_iso_kg > 0.0 && r.eigenvalues_kg.size() == 3) {
        r.isotropy_residual = (r.eigenvalues_kg[2] - r.eigenvalues_kg[0]) / r.lambda_iso_kg;
    }
    for (std::size_t i = 0; i < 9; ++i) {
        r.fd_max_abs_error_kg = std::max(r.fd_max_abs_error_kg, std::abs(r.tensor_kg[i] - r.tensor_fd_kg[i]));
    }
    if (r.chi_T > 0.0) {
        r.required_impedance_scale_for_chi_one = o.impedance_scale / r.chi_T;
        r.required_density_for_chi_one_kg_m3 = o.density_kg_m3 / r.chi_T;
    } else {
        r.required_impedance_scale_for_chi_one = std::numeric_limits<double>::infinity();
        r.required_density_for_chi_one_kg_m3 = std::numeric_limits<double>::infinity();
    }
    return r;
}

Result audit_trefoil(std::size_t n, Options o) {
    return audit_points(generate_trefoil(n), o);
}

Result audit_figure_eight(std::size_t n, Options o) {
    return audit_points(generate_figure_eight(n), o);
}

#ifdef BUILD_PYBIND11_MODULE
std::vector<double> numpy_to_flat_points(py::array_t<double, py::array::c_style | py::array::forcecast> arr) {
    py::buffer_info info = arr.request();
    if (info.ndim != 2 || info.shape[1] != 3 || info.shape[0] < 3) {
        throw std::invalid_argument("points array must have shape (N,3), N>=3");
    }
    const double* data = static_cast<const double*>(info.ptr);
    return std::vector<double>(data, data + static_cast<std::size_t>(info.shape[0] * 3));
}

py::dict result_to_dict(const Result& r) {
    py::dict d;
    d["tensor_kg"] = r.tensor_kg;
    d["tensor_fd_kg"] = r.tensor_fd_kg;
    d["eigenvalues_kg"] = r.eigenvalues_kg;
    d["eigenvectors_rowmajor"] = r.eigenvectors_rowmajor;
    d["length_m"] = r.length_m;
    d["length_over_r_c"] = r.length_over_r_c;
    d["lambda_iso_kg"] = r.lambda_iso_kg;
    d["target_lambda_iso_kg"] = r.target_lambda_iso_kg;
    d["chi_T"] = r.chi_T;
    d["isotropy_residual"] = r.isotropy_residual;
    d["fd_max_abs_error_kg"] = r.fd_max_abs_error_kg;
    d["required_impedance_scale_for_chi_one"] = r.required_impedance_scale_for_chi_one;
    d["required_density_for_chi_one_kg_m3"] = r.required_density_for_chi_one_kg_m3;
    return d;
}

PYBIND11_MODULE(sst_torsion_impedance, m) {
    m.doc() = "Standalone SST research-track core--torsion impedance audit";

    py::class_<Options>(m, "Options")
        .def(py::init<>())
        .def_readwrite("length_scale_m", &Options::length_scale_m)
        .def_readwrite("core_radius_m", &Options::core_radius_m)
        .def_readwrite("density_kg_m3", &Options::density_kg_m3)
        .def_readwrite("c_T_m_s", &Options::c_T_m_s)
        .def_readwrite("rest_energy_j", &Options::rest_energy_j)
        .def_readwrite("impedance_scale", &Options::impedance_scale)
        .def_readwrite("finite_difference_velocity_m_s", &Options::finite_difference_velocity_m_s);

    m.attr("C") = c;
    m.attr("VCHAR") = vchar;
    m.attr("R_C") = r_c;
    m.attr("RHO_F") = rho_f;
    m.attr("RHO_CORE") = rho_core;
    m.attr("M_E") = m_e;
    m.attr("ELECTRON_REST_ENERGY_J") = electron_rest_energy_j;

    m.def("canonical_medium_options", &canonical_medium_options);
    m.def("canonical_core_density_options", &canonical_core_density_options);
    m.def("generate_trefoil", &generate_trefoil, py::arg("n"), py::arg("major_radius")=2.0, py::arg("minor_radius")=0.75);
    m.def("generate_figure_eight", &generate_figure_eight, py::arg("n"), py::arg("scale")=1.0);
    m.def("audit_flat_points", [](const std::vector<double>& flat, const Options& o){ return result_to_dict(audit_points(flat, o)); });
    m.def("audit_points", [](py::array_t<double, py::array::c_style | py::array::forcecast> pts, const Options& o){
        return result_to_dict(audit_points(numpy_to_flat_points(pts), o));
    });
    m.def("audit_trefoil", [](std::size_t n, const Options& o){ return result_to_dict(audit_trefoil(n, o)); });
    m.def("audit_figure_eight", [](std::size_t n, const Options& o){ return result_to_dict(audit_figure_eight(n, o)); });
}
#endif

} // namespace sst_rt

#ifndef BUILD_PYBIND11_MODULE
int main() {
    using namespace sst_rt;
    const auto med = canonical_medium_options();
    const auto core = canonical_core_density_options();
    const auto rt = audit_trefoil(2048, med);
    const auto rc = audit_trefoil(2048, core);
    std::cout.setf(std::ios::scientific);
    std::cout.precision(12);
    std::cout << "{\n";
    std::cout << "  \"analytic_trefoil_rho_f_chi_T\": " << rt.chi_T << ",\n";
    std::cout << "  \"analytic_trefoil_rho_f_isotropy_residual\": " << rt.isotropy_residual << ",\n";
    std::cout << "  \"analytic_trefoil_rho_core_chi_T\": " << rc.chi_T << ",\n";
    std::cout << "  \"fd_max_abs_error_kg\": " << rt.fd_max_abs_error_kg << "\n";
    std::cout << "}\n";
    return 0;
}
#endif
