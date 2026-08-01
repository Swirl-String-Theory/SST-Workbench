#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

#ifndef M_PI
#define M_PI 3.141592653589793238462643383279502884
#endif

struct SegGeom {
    std::vector<double> mid;
    std::vector<double> tan;
    std::vector<double> ds;
    std::size_t n;
};

static void require_n3(const py::array_t<double, py::array::c_style | py::array::forcecast>& arr,
                       const char* name, std::size_t min_n = 1) {
    if (arr.ndim() != 2 || arr.shape(1) != 3 || static_cast<std::size_t>(arr.shape(0)) < min_n) {
        throw std::runtime_error(std::string(name) + " must have shape (N,3) with N >= " + std::to_string(min_n));
    }
}

static SegGeom make_segments(py::array_t<double, py::array::c_style | py::array::forcecast> points) {
    require_n3(points, "points", 3);
    auto p = points.unchecked<2>();
    const std::size_t n = static_cast<std::size_t>(p.shape(0));
    SegGeom g;
    g.n = n;
    g.mid.assign(n * 3, 0.0);
    g.tan.assign(n * 3, 0.0);
    g.ds.assign(n, 0.0);
    for (std::size_t i = 0; i < n; ++i) {
        const std::size_t j = (i + 1) % n;
        const double dx = p(j, 0) - p(i, 0);
        const double dy = p(j, 1) - p(i, 1);
        const double dz = p(j, 2) - p(i, 2);
        const double len = std::sqrt(dx * dx + dy * dy + dz * dz);
        if (!(len > 0.0)) throw std::runtime_error("Degenerate segment in closed polyline");
        g.ds[i] = len;
        g.mid[i * 3 + 0] = 0.5 * (p(i, 0) + p(j, 0));
        g.mid[i * 3 + 1] = 0.5 * (p(i, 1) + p(j, 1));
        g.mid[i * 3 + 2] = 0.5 * (p(i, 2) + p(j, 2));
        g.tan[i * 3 + 0] = dx / len;
        g.tan[i * 3 + 1] = dy / len;
        g.tan[i * 3 + 2] = dz / len;
    }
    return g;
}

static double polyline_length(py::array_t<double, py::array::c_style | py::array::forcecast> points) {
    auto g = make_segments(points);
    double L = 0.0;
    for (double x : g.ds) L += x;
    return L;
}

static double min_nonadjacent_vertex_distance(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                              int skip) {
    require_n3(points, "points", 4);
    auto p = points.unchecked<2>();
    const std::size_t n = static_cast<std::size_t>(p.shape(0));
    double best = std::numeric_limits<double>::infinity();
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = i + 1; j < n; ++j) {
            const std::size_t sep1 = j - i;
            const std::size_t sep2 = n - sep1;
            const std::size_t sep = sep1 < sep2 ? sep1 : sep2;
            if (sep <= static_cast<std::size_t>(skip)) continue;
            const double dx = p(j, 0) - p(i, 0);
            const double dy = p(j, 1) - p(i, 1);
            const double dz = p(j, 2) - p(i, 2);
            const double d = std::sqrt(dx * dx + dy * dy + dz * dz);
            if (d < best) best = d;
        }
    }
    return best;
}

static double bs_regularized_energy(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                    double a) {
    if (!(a > 0.0)) throw std::runtime_error("a must be positive");
    auto g = make_segments(points);
    double acc = 0.0;
    for (std::size_t i = 0; i < g.n; ++i) {
        const double mix = g.mid[i * 3 + 0], miy = g.mid[i * 3 + 1], miz = g.mid[i * 3 + 2];
        const double tix = g.tan[i * 3 + 0], tiy = g.tan[i * 3 + 1], tiz = g.tan[i * 3 + 2];
        for (std::size_t j = 0; j < g.n; ++j) {
            if (i == j) continue;
            const double rx = g.mid[j * 3 + 0] - mix;
            const double ry = g.mid[j * 3 + 1] - miy;
            const double rz = g.mid[j * 3 + 2] - miz;
            const double dist = std::sqrt(rx * rx + ry * ry + rz * rz + a * a);
            const double dot = tix * g.tan[j * 3 + 0] + tiy * g.tan[j * 3 + 1] + tiz * g.tan[j * 3 + 2];
            acc += (dot / dist) * g.ds[i] * g.ds[j];
        }
    }
    return acc / (8.0 * M_PI);
}

static double bs_cutoff_energy(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                               double a_cutoff) {
    if (!(a_cutoff >= 0.0)) throw std::runtime_error("a_cutoff must be non-negative");
    auto g = make_segments(points);
    double acc = 0.0;
    for (std::size_t i = 0; i < g.n; ++i) {
        const double mix = g.mid[i * 3 + 0], miy = g.mid[i * 3 + 1], miz = g.mid[i * 3 + 2];
        const double tix = g.tan[i * 3 + 0], tiy = g.tan[i * 3 + 1], tiz = g.tan[i * 3 + 2];
        for (std::size_t j = 0; j < g.n; ++j) {
            if (i == j) continue;
            const double rx = g.mid[j * 3 + 0] - mix;
            const double ry = g.mid[j * 3 + 1] - miy;
            const double rz = g.mid[j * 3 + 2] - miz;
            const double dist = std::sqrt(rx * rx + ry * ry + rz * rz);
            if (!(dist > a_cutoff)) continue;
            const double dot = tix * g.tan[j * 3 + 0] + tiy * g.tan[j * 3 + 1] + tiz * g.tan[j * 3 + 2];
            acc += (dot / dist) * g.ds[i] * g.ds[j];
        }
    }
    return acc / (8.0 * M_PI);
}

static py::array_t<double> velocity_grid(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                         py::array_t<double, py::array::c_style | py::array::forcecast> eval_points,
                                         double gamma,
                                         double a) {
    if (!(a > 0.0)) throw std::runtime_error("a must be positive");
    auto g = make_segments(points);
    require_n3(eval_points, "eval_points", 1);
    auto x = eval_points.unchecked<2>();
    const std::size_t m = static_cast<std::size_t>(x.shape(0));
    py::array_t<double> out({static_cast<py::ssize_t>(m), static_cast<py::ssize_t>(3)});
    auto o = out.mutable_unchecked<2>();
    const double coeff = gamma / (4.0 * M_PI);
    for (std::size_t k = 0; k < m; ++k) {
        double vx = 0.0, vy = 0.0, vz = 0.0;
        for (std::size_t i = 0; i < g.n; ++i) {
            const double rx = x(k, 0) - g.mid[i * 3 + 0];
            const double ry = x(k, 1) - g.mid[i * 3 + 1];
            const double rz = x(k, 2) - g.mid[i * 3 + 2];
            const double denom = std::pow(rx * rx + ry * ry + rz * rz + a * a, 1.5);
            const double cx = g.tan[i * 3 + 1] * rz - g.tan[i * 3 + 2] * ry;
            const double cy = g.tan[i * 3 + 2] * rx - g.tan[i * 3 + 0] * rz;
            const double cz = g.tan[i * 3 + 0] * ry - g.tan[i * 3 + 1] * rx;
            const double s = coeff * g.ds[i] / denom;
            vx += s * cx;
            vy += s * cy;
            vz += s * cz;
        }
        o(k, 0) = vx;
        o(k, 1) = vy;
        o(k, 2) = vz;
    }
    return out;
}



static double horn_xi_cavitation(double lambda) {
    if (!(lambda >= 1.0)) throw std::runtime_error("lambda = R/a0 must be >= 1 for an embedded hollow torus");
    return 0.25 * lambda;
}

static double horn_chi_from_xi(double xi) {
    return 4.0 * M_PI * M_PI * xi;
}

static double horn_xi_thin_ring(double lambda, double core_constant) {
    if (!(lambda >= 1.0)) throw std::runtime_error("lambda = R/a0 must be >= 1 for an embedded hollow torus");
    if (!std::isfinite(core_constant)) throw std::runtime_error("core_constant must be finite");
    return 0.5 * lambda * (std::log(8.0 * lambda) - core_constant);
}

static double horn_xi_regularized_filament(double lambda, double epsilon, int quadrature_n) {
    if (!(lambda >= 1.0)) throw std::runtime_error("lambda = R/a0 must be >= 1 for an embedded hollow torus");
    if (!(epsilon > 0.0)) throw std::runtime_error("epsilon must be positive");
    if (quadrature_n < 128) throw std::runtime_error("quadrature_n must be >= 128");
    const double two_pi = 2.0 * M_PI;
    const double dtheta = two_pi / static_cast<double>(quadrature_n);
    double sum = 0.0;
    for (int k = 0; k < quadrature_n; ++k) {
        const double theta = (static_cast<double>(k) + 0.5) * dtheta;
        const double s = std::sin(0.5 * theta);
        const double denom = std::sqrt(4.0 * lambda * lambda * s * s + epsilon * epsilon);
        sum += std::cos(theta) / denom;
    }
    const double integral = sum * dtheta;
    return 0.25 * lambda * lambda * integral;
}

static double horn_chi_K_regularized(double lambda, double epsilon, int quadrature_n) {
    return horn_chi_from_xi(horn_xi_regularized_filament(lambda, epsilon, quadrature_n));
}

static double regularized_neumann_energy_dimensionless(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                                       double epsilon) {
    return bs_regularized_energy(points, epsilon);
}

PYBIND11_MODULE(sst_trefoil_biot, m) {
    m.doc() = "SST ideal trefoil Biot-Savart closure kernels";
    m.def("polyline_length", &polyline_length, py::arg("points"));
    m.def("min_nonadjacent_vertex_distance", &min_nonadjacent_vertex_distance, py::arg("points"), py::arg("skip") = 2);
    m.def("bs_regularized_energy", &bs_regularized_energy, py::arg("points"), py::arg("a"));
    m.def("bs_cutoff_energy", &bs_cutoff_energy, py::arg("points"), py::arg("a_cutoff"));
    m.def("velocity_grid", &velocity_grid, py::arg("points"), py::arg("eval_points"), py::arg("gamma") = 1.0, py::arg("a") = 1e-3);
    m.def("horn_xi_cavitation", &horn_xi_cavitation, py::arg("lambda_"));
    m.def("horn_chi_from_xi", &horn_chi_from_xi, py::arg("xi"));
    m.def("horn_xi_thin_ring", &horn_xi_thin_ring, py::arg("lambda_"), py::arg("core_constant") = 1.75);
    m.def("horn_xi_regularized_filament", &horn_xi_regularized_filament, py::arg("lambda_"), py::arg("epsilon") = 1.0, py::arg("quadrature_n") = 32768);
    m.def("horn_chi_K_regularized", &horn_chi_K_regularized, py::arg("lambda_"), py::arg("epsilon") = 1.0, py::arg("quadrature_n") = 32768);
    m.def("regularized_neumann_energy_dimensionless", &regularized_neumann_energy_dimensionless, py::arg("points"), py::arg("epsilon") = 1.0);
}
