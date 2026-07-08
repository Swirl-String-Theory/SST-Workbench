#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
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




namespace sst {

enum class HornTorusKernel {
    THIN_RING_ASYMPTOTIC,
    REGULARIZED_CIRCULAR_FILAMENT
};

enum class EnergyMassMode {
    KINETIC_ONLY,
    KINETIC_PLUS_CAVITY,
    VACUUM_SUBTRACTED,
    TARGET_RENORMALIZED
};

static std::string energy_mass_mode_name(EnergyMassMode mode) {
    switch (mode) {
        case EnergyMassMode::KINETIC_ONLY: return "kinetic_only";
        case EnergyMassMode::KINETIC_PLUS_CAVITY: return "kinetic_plus_cavity";
        case EnergyMassMode::VACUUM_SUBTRACTED: return "vacuum_subtracted";
        case EnergyMassMode::TARGET_RENORMALIZED: return "target_renormalized";
    }
    return "unknown";
}

struct HornTorusParams {
    double rho_sat = 1.0;       // kg m^-3; used only for dimensional E_loop reporting
    double Gamma0 = 1.0;        // m^2 s^-1; used only for dimensional E_loop reporting
    double a0 = 1.0;            // m; resolved hollow-core radius
    double lambda_ = 1.0;       // R/a0, dimensionless. Named lambda_ because lambda is a C++ keyword.
    double epsilon = 1.0;       // a_soft/a0, dimensionless
    int quadrature_n = 32768;   // e.g. 4096..65536
    double core_constant = 1.75;// thin-ring constant, diagnostic only
    EnergyMassMode mass_mode = EnergyMassMode::KINETIC_PLUS_CAVITY;
};

struct HornTorusEnergyResult {
    double lambda_ = 1.0;
    double epsilon = 1.0;
    double R = 1.0;
    double v0 = 1.0;

    double Xi_filament = 0.0;
    double Xi_cavitation = 0.0;
    double Xi_renormalization = 0.0;
    double Xi_total = 0.0; // strict hollow total = Xi_filament + Xi_cavitation
    double Xi_mass = 0.0;  // selected mass-energy value after mode/subtraction

    double chi_K = 0.0;
    double chi_cavitation = 0.0;
    double chi_renormalization = 0.0;
    double chi_E_hollow_total = 0.0;
    double chi_E = 0.0;
    double E_loop = 0.0;
    double target_residual = 0.0; // (selected chi_E - 2*pi)/(2*pi)
    std::string mass_mode = "kinetic_plus_cavity";
};

class HornTorusEnergy {
public:
    static void validate_positive(double x, const char* name) {
        if (!(x > 0.0) || !std::isfinite(x)) {
            throw std::domain_error(std::string(name) + " must be finite and positive");
        }
    }

    static void validate_lambda(double lambda) {
        if (!(lambda >= 1.0) || !std::isfinite(lambda)) {
            throw std::domain_error("lambda_=R/a0 must be finite and >= 1 for an embedded hollow torus");
        }
    }

    static double v0_from_gamma_a0(double Gamma0, double a0) {
        validate_positive(Gamma0, "Gamma0");
        validate_positive(a0, "a0");
        return Gamma0 / (2.0 * M_PI * a0);
    }

    static double p_vac_from_variational_a0(double rho_sat, double Gamma0, double a0) {
        validate_positive(rho_sat, "rho_sat");
        validate_positive(Gamma0, "Gamma0");
        validate_positive(a0, "a0");
        return rho_sat * Gamma0 * Gamma0 / (8.0 * M_PI * M_PI * a0 * a0);
    }

    static double xi_cavitation(double lambda) {
        validate_lambda(lambda);
        return 0.25 * lambda;
    }

    static double chi_from_xi(double xi) {
        return 4.0 * M_PI * M_PI * xi;
    }

    static std::pair<double, double> mass_xi_components(double xi_fil, double xi_cav, EnergyMassMode mode) {
        const double xi_hollow = xi_fil + xi_cav;
        if (mode == EnergyMassMode::KINETIC_ONLY) {
            return std::make_pair(0.0, xi_fil);
        }
        if (mode == EnergyMassMode::KINETIC_PLUS_CAVITY) {
            return std::make_pair(0.0, xi_hollow);
        }
        if (mode == EnergyMassMode::VACUUM_SUBTRACTED) {
            return std::make_pair(-xi_cav, xi_fil);
        }
        if (mode == EnergyMassMode::TARGET_RENORMALIZED) {
            return std::make_pair(1.0 / (2.0 * M_PI) - xi_hollow, 1.0 / (2.0 * M_PI));
        }
        throw std::domain_error("unsupported EnergyMassMode");
    }

    static double xi_thin_ring(double lambda, double core_constant) {
        validate_lambda(lambda);
        if (!std::isfinite(core_constant)) {
            throw std::domain_error("core_constant must be finite");
        }
        return 0.5 * lambda * (std::log(8.0 * lambda) - core_constant);
    }

    static double xi_regularized_circular_filament(double lambda, double epsilon, int quadrature_n) {
        validate_lambda(lambda);
        validate_positive(epsilon, "epsilon");
        if (quadrature_n < 128) throw std::domain_error("quadrature_n must be >= 128");
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

    static HornTorusEnergyResult evaluate(const HornTorusParams& params, HornTorusKernel kernel) {
        validate_positive(params.rho_sat, "rho_sat");
        validate_positive(params.Gamma0, "Gamma0");
        validate_positive(params.a0, "a0");
        validate_lambda(params.lambda_);
        validate_positive(params.epsilon, "epsilon");
        if (params.quadrature_n < 128) throw std::domain_error("quadrature_n must be >= 128");

        double xi_fil = 0.0;
        if (kernel == HornTorusKernel::THIN_RING_ASYMPTOTIC) {
            xi_fil = xi_thin_ring(params.lambda_, params.core_constant);
        } else {
            xi_fil = xi_regularized_circular_filament(params.lambda_, params.epsilon, params.quadrature_n);
        }

        const double xi_cav = xi_cavitation(params.lambda_);
        const double xi_total = xi_fil + xi_cav;
        const auto mass_pair = mass_xi_components(xi_fil, xi_cav, params.mass_mode);
        const double xi_ren = mass_pair.first;
        const double xi_mass = mass_pair.second;

        HornTorusEnergyResult r;
        r.lambda_ = params.lambda_;
        r.epsilon = params.epsilon;
        r.R = params.lambda_ * params.a0;
        r.v0 = v0_from_gamma_a0(params.Gamma0, params.a0);
        r.Xi_filament = xi_fil;
        r.Xi_cavitation = xi_cav;
        r.Xi_renormalization = xi_ren;
        r.Xi_total = xi_total;
        r.Xi_mass = xi_mass;
        r.chi_K = chi_from_xi(xi_fil);
        r.chi_cavitation = chi_from_xi(xi_cav);
        r.chi_renormalization = chi_from_xi(xi_ren);
        r.chi_E_hollow_total = chi_from_xi(xi_total);
        r.chi_E = chi_from_xi(xi_mass);
        r.E_loop = xi_mass * params.rho_sat * params.Gamma0 * params.Gamma0 * params.a0;
        r.target_residual = (r.chi_E - 2.0 * M_PI) / (2.0 * M_PI);
        r.mass_mode = energy_mass_mode_name(params.mass_mode);
        return r;
    }
};

static std::vector<HornTorusEnergyResult> scan_lambda(double lambda_min,
                                                      double lambda_max,
                                                      int lambda_count,
                                                      HornTorusParams base,
                                                      HornTorusKernel kernel) {
    HornTorusEnergy::validate_lambda(lambda_min);
    HornTorusEnergy::validate_lambda(lambda_max);
    if (lambda_max < lambda_min) throw std::domain_error("lambda_max must be >= lambda_min");
    if (lambda_count < 2) throw std::domain_error("lambda_count must be >= 2");
    std::vector<HornTorusEnergyResult> out;
    out.reserve(static_cast<std::size_t>(lambda_count));
    for (int i = 0; i < lambda_count; ++i) {
        const double t = static_cast<double>(i) / static_cast<double>(lambda_count - 1);
        base.lambda_ = lambda_min + t * (lambda_max - lambda_min);
        out.push_back(HornTorusEnergy::evaluate(base, kernel));
    }
    return out;
}

static HornTorusEnergyResult minimize_lambda(double lambda_min,
                                             double lambda_max,
                                             HornTorusParams base,
                                             HornTorusKernel kernel,
                                             int iterations = 80) {
    HornTorusEnergy::validate_lambda(lambda_min);
    HornTorusEnergy::validate_lambda(lambda_max);
    if (lambda_max < lambda_min) throw std::domain_error("lambda_max must be >= lambda_min");
    if (iterations < 8) throw std::domain_error("iterations must be >= 8");

    const double gr = (std::sqrt(5.0) - 1.0) / 2.0;
    double lo = lambda_min;
    double hi = lambda_max;
    double c = hi - gr * (hi - lo);
    double d = lo + gr * (hi - lo);

    auto f = [&](double lam) -> double {
        HornTorusParams p = base;
        p.lambda_ = lam;
        return HornTorusEnergy::evaluate(p, kernel).chi_E;
    };

    double fc = f(c);
    double fd = f(d);
    for (int it = 0; it < iterations; ++it) {
        if (fc < fd) {
            hi = d;
            d = c;
            fd = fc;
            c = hi - gr * (hi - lo);
            fc = f(c);
        } else {
            lo = c;
            c = d;
            fc = fd;
            d = lo + gr * (hi - lo);
            fd = f(d);
        }
    }
    base.lambda_ = 0.5 * (lo + hi);
    return HornTorusEnergy::evaluate(base, kernel);
}

} // namespace sst

static double horn_xi_cavitation(double lambda) {
    return sst::HornTorusEnergy::xi_cavitation(lambda);
}

static double horn_chi_from_xi(double xi) {
    return sst::HornTorusEnergy::chi_from_xi(xi);
}

static double horn_xi_thin_ring(double lambda, double core_constant) {
    return sst::HornTorusEnergy::xi_thin_ring(lambda, core_constant);
}

static double horn_xi_regularized_filament(double lambda, double epsilon, int quadrature_n) {
    return sst::HornTorusEnergy::xi_regularized_circular_filament(lambda, epsilon, quadrature_n);
}

static double horn_chi_K_regularized(double lambda, double epsilon, int quadrature_n) {
    return sst::HornTorusEnergy::chi_from_xi(
        sst::HornTorusEnergy::xi_regularized_circular_filament(lambda, epsilon, quadrature_n));
}

static double regularized_neumann_energy_dimensionless(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                                       double epsilon) {
    return bs_regularized_energy(points, epsilon);
}

static double regularized_neumann_energy_dimensionless_scaled(py::array_t<double, py::array::c_style | py::array::forcecast> points,
                                                              double a0,
                                                              double epsilon) {
    if (!(a0 > 0.0)) throw std::runtime_error("a0 must be positive");
    if (!(epsilon > 0.0)) throw std::runtime_error("epsilon must be positive");
    return bs_regularized_energy(points, epsilon * a0) / a0;
}

PYBIND11_MODULE(sst_trefoil_biot, m) {
    m.doc() = "SST ideal trefoil Biot-Savart and horn-torus chiE kernels";
    m.def("polyline_length", &polyline_length, py::arg("points"));
    m.def("min_nonadjacent_vertex_distance", &min_nonadjacent_vertex_distance, py::arg("points"), py::arg("skip") = 2);
    m.def("bs_regularized_energy", &bs_regularized_energy, py::arg("points"), py::arg("a"));
    m.def("bs_cutoff_energy", &bs_cutoff_energy, py::arg("points"), py::arg("a_cutoff"));
    m.def("velocity_grid", &velocity_grid, py::arg("points"), py::arg("eval_points"), py::arg("gamma") = 1.0, py::arg("a") = 1e-3);

    py::enum_<sst::HornTorusKernel>(m, "HornTorusKernel")
        .value("THIN_RING_ASYMPTOTIC", sst::HornTorusKernel::THIN_RING_ASYMPTOTIC)
        .value("REGULARIZED_CIRCULAR_FILAMENT", sst::HornTorusKernel::REGULARIZED_CIRCULAR_FILAMENT)
        .export_values();

    py::enum_<sst::EnergyMassMode>(m, "EnergyMassMode")
        .value("KINETIC_ONLY", sst::EnergyMassMode::KINETIC_ONLY)
        .value("KINETIC_PLUS_CAVITY", sst::EnergyMassMode::KINETIC_PLUS_CAVITY)
        .value("VACUUM_SUBTRACTED", sst::EnergyMassMode::VACUUM_SUBTRACTED)
        .value("TARGET_RENORMALIZED", sst::EnergyMassMode::TARGET_RENORMALIZED)
        .export_values();

    py::class_<sst::HornTorusParams>(m, "HornTorusParams")
        .def(py::init<>())
        .def_readwrite("rho_sat", &sst::HornTorusParams::rho_sat)
        .def_readwrite("Gamma0", &sst::HornTorusParams::Gamma0)
        .def_readwrite("a0", &sst::HornTorusParams::a0)
        .def_readwrite("lambda_", &sst::HornTorusParams::lambda_)
        .def_readwrite("epsilon", &sst::HornTorusParams::epsilon)
        .def_readwrite("quadrature_n", &sst::HornTorusParams::quadrature_n)
        .def_readwrite("core_constant", &sst::HornTorusParams::core_constant)
        .def_readwrite("mass_mode", &sst::HornTorusParams::mass_mode);

    py::class_<sst::HornTorusEnergyResult>(m, "HornTorusEnergyResult")
        .def_readonly("lambda_", &sst::HornTorusEnergyResult::lambda_)
        .def_readonly("epsilon", &sst::HornTorusEnergyResult::epsilon)
        .def_readonly("R", &sst::HornTorusEnergyResult::R)
        .def_readonly("v0", &sst::HornTorusEnergyResult::v0)
        .def_readonly("Xi_filament", &sst::HornTorusEnergyResult::Xi_filament)
        .def_readonly("Xi_cavitation", &sst::HornTorusEnergyResult::Xi_cavitation)
        .def_readonly("Xi_renormalization", &sst::HornTorusEnergyResult::Xi_renormalization)
        .def_readonly("Xi_total", &sst::HornTorusEnergyResult::Xi_total)
        .def_readonly("Xi_mass", &sst::HornTorusEnergyResult::Xi_mass)
        .def_readonly("chi_K", &sst::HornTorusEnergyResult::chi_K)
        .def_readonly("chi_cavitation", &sst::HornTorusEnergyResult::chi_cavitation)
        .def_readonly("chi_renormalization", &sst::HornTorusEnergyResult::chi_renormalization)
        .def_readonly("chi_E_hollow_total", &sst::HornTorusEnergyResult::chi_E_hollow_total)
        .def_readonly("chi_E", &sst::HornTorusEnergyResult::chi_E)
        .def_readonly("E_loop", &sst::HornTorusEnergyResult::E_loop)
        .def_readonly("target_residual", &sst::HornTorusEnergyResult::target_residual)
        .def_readonly("mass_mode", &sst::HornTorusEnergyResult::mass_mode);

    py::class_<sst::HornTorusEnergy>(m, "HornTorusEnergy")
        .def_static("v0_from_gamma_a0", &sst::HornTorusEnergy::v0_from_gamma_a0, py::arg("Gamma0"), py::arg("a0"))
        .def_static("p_vac_from_variational_a0", &sst::HornTorusEnergy::p_vac_from_variational_a0,
                    py::arg("rho_sat"), py::arg("Gamma0"), py::arg("a0"))
        .def_static("xi_cavitation", &sst::HornTorusEnergy::xi_cavitation, py::arg("lambda_"))
        .def_static("xi_thin_ring", &sst::HornTorusEnergy::xi_thin_ring,
                    py::arg("lambda_"), py::arg("core_constant") = 1.75)
        .def_static("xi_regularized_circular_filament", &sst::HornTorusEnergy::xi_regularized_circular_filament,
                    py::arg("lambda_"), py::arg("epsilon") = 1.0, py::arg("quadrature_n") = 32768)
        .def_static("evaluate", &sst::HornTorusEnergy::evaluate, py::arg("params"), py::arg("kernel"));

    m.def("horn_torus_energy", &sst::HornTorusEnergy::evaluate, py::arg("params"), py::arg("kernel"));
    m.def("scan_lambda", &sst::scan_lambda, py::arg("lambda_min"), py::arg("lambda_max"), py::arg("lambda_count"),
          py::arg("base"), py::arg("kernel"));
    m.def("minimize_lambda", &sst::minimize_lambda, py::arg("lambda_min"), py::arg("lambda_max"),
          py::arg("base"), py::arg("kernel"), py::arg("iterations") = 80);

    // Backward-compatible scalar wrappers used by the Python fallback module.
    m.def("horn_xi_cavitation", &horn_xi_cavitation, py::arg("lambda_"));
    m.def("horn_chi_from_xi", &horn_chi_from_xi, py::arg("xi"));
    m.def("horn_xi_thin_ring", &horn_xi_thin_ring, py::arg("lambda_"), py::arg("core_constant") = 1.75);
    m.def("horn_xi_regularized_filament", &horn_xi_regularized_filament, py::arg("lambda_"), py::arg("epsilon") = 1.0, py::arg("quadrature_n") = 32768);
    m.def("horn_chi_K_regularized", &horn_chi_K_regularized, py::arg("lambda_"), py::arg("epsilon") = 1.0, py::arg("quadrature_n") = 32768);
    m.def("regularized_neumann_energy_dimensionless", &regularized_neumann_energy_dimensionless, py::arg("points"), py::arg("epsilon") = 1.0);
    m.def("regularized_neumann_energy_dimensionless_scaled", &regularized_neumann_energy_dimensionless_scaled,
          py::arg("points"), py::arg("a0") = 1.0, py::arg("epsilon") = 1.0);
}
