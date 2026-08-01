#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "fermat_kernel.hpp"

namespace py = pybind11;
using namespace sst_fermat;

static py::dict profile_eval_dict(const ProfileEval& p, double x) {
    py::dict d;
    d["x"] = x;
    d["beta"] = p.beta;
    d["d_beta"] = p.d_beta;
    d["dd_beta"] = p.dd_beta;
    d["fermat_residual"] = fermat_residual(p, x);
    const double s2 = 1.0 - p.beta * p.beta;
    d["clock_valid"] = s2 > 0.0;
    if (s2 > 0.0) {
        d["S"] = std::sqrt(s2);
        d["n"] = 1.0 / std::sqrt(s2);
        d["R_F_over_rc"] = x / std::sqrt(s2);
        d["K_hat"] = k_hat(p, x);
        d["R_F_second_x"] = r_f_second_x(p, x);
    } else {
        d["S"] = py::none();
        d["n"] = py::none();
        d["R_F_over_rc"] = py::none();
        d["K_hat"] = py::none();
        d["R_F_second_x"] = py::none();
    }
    return d;
}

static py::dict analyze_profile_native(
    const std::string& profile,
    double beta0,
    double a,
    double xmin,
    double xmax,
    int samples) {
    const auto intervals = split_intervals(profile, xmin, xmax, a);
    auto critical = roots_log_bisection(
        [&](double x) {
            const auto p = eval_profile(profile, x, beta0, a);
            if (std::abs(p.beta) >= 1.0) return std::numeric_limits<double>::quiet_NaN();
            return fermat_residual(p, x);
        }, intervals, samples);
    auto horizons = roots_log_bisection(
        [&](double x) {
            const auto p = eval_profile(profile, x, beta0, a);
            return std::abs(p.beta) - 1.0;
        }, intervals, samples);

    py::list crit_list;
    for (double x : critical) crit_list.append(profile_eval_dict(eval_profile(profile, x, beta0, a), x));
    py::list hor_list;
    for (double x : horizons) {
        py::dict h;
        h["x"] = x;
        h["beta_abs"] = std::abs(eval_profile(profile, x, beta0, a).beta);
        hor_list.append(h);
    }
    py::dict out;
    out["profile"] = profile;
    out["beta0"] = beta0;
    out["a_core_over_rc"] = a;
    out["x_min"] = xmin;
    out["x_max"] = xmax;
    out["samples"] = samples;
    out["critical_roots"] = crit_list;
    out["horizon_roots"] = hor_list;
    return out;
}

static void convert_inputs(
    const std::vector<std::array<double, 3>>& centerline,
    const std::vector<std::array<double, 3>>& probes,
    std::vector<Vec3>& c,
    std::vector<Vec3>& p) {
    c.reserve(centerline.size());
    p.reserve(probes.size());
    for (const auto& v : centerline) c.push_back({v[0], v[1], v[2]});
    for (const auto& v : probes) p.push_back({v[0], v[1], v[2]});
}

static std::vector<std::array<double, 3>> biot_wrapper(
    const std::vector<std::array<double, 3>>& centerline,
    const std::vector<std::array<double, 3>>& probes,
    double coefficient,
    double epsilon,
    const std::string& kernel_model) {
    std::vector<Vec3> c, p;
    convert_inputs(centerline, probes, c, p);
    const auto u = biot_savart_batch(c, p, coefficient, epsilon, kernel_model);
    std::vector<std::array<double, 3>> out;
    out.reserve(u.size());
    for (const auto& v : u) out.push_back({v.x, v.y, v.z});
    return out;
}

static py::tuple biot_jacobian_wrapper(
    const std::vector<std::array<double, 3>>& centerline,
    const std::vector<std::array<double, 3>>& probes,
    double coefficient,
    double epsilon,
    const std::string& kernel_model) {
    std::vector<Vec3> c, p;
    convert_inputs(centerline, probes, c, p);
    const auto values = biot_savart_batch_with_jacobian(c, p, coefficient, epsilon, kernel_model);
    py::list betas;
    py::list jacobians;
    for (const auto& item : values) {
        betas.append(std::array<double,3>{{item.beta.x,item.beta.y,item.beta.z}});
        py::list rows;
        for (int i = 0; i < 3; ++i) {
            rows.append(std::array<double,3>{{
                item.jacobian[static_cast<std::size_t>(i*3+0)],
                item.jacobian[static_cast<std::size_t>(i*3+1)],
                item.jacobian[static_cast<std::size_t>(i*3+2)]
            }});
        }
        jacobians.append(rows);
    }
    return py::make_tuple(betas, jacobians);
}

PYBIND11_MODULE(_fermat_native, m) {
    m.doc() = "Standalone SST Fermat research kernels: radial profiles, regularized Biot-Savart, and analytic field Jacobians.";
    m.def("eval_profile", [](const std::string& profile, double x, double beta0, double a) {
        return profile_eval_dict(eval_profile(profile, x, beta0, a), x);
    });
    m.def("analyze_profile", &analyze_profile_native,
          py::arg("profile"), py::arg("beta0"), py::arg("a_core_over_rc"),
          py::arg("x_min"), py::arg("x_max"), py::arg("samples") = 4000);
    m.def("biot_savart_batch", &biot_wrapper,
          py::arg("centerline"), py::arg("probes"), py::arg("coefficient"), py::arg("epsilon"),
          py::arg("kernel_model") = "rosenhead_midpoint");
    m.def("biot_savart_batch_with_jacobian", &biot_jacobian_wrapper,
          py::arg("centerline"), py::arg("probes"), py::arg("coefficient"), py::arg("epsilon"),
          py::arg("kernel_model") = "rosenhead_midpoint");
}
