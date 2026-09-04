#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

namespace {

constexpr double PI = 3.141592653589793238462643383279502884;

struct Curve {
    std::size_t n{};
    std::vector<double> points;
    std::vector<double> mid;
    std::vector<double> dl;
    std::vector<double> vertex_s;
    std::vector<double> mid_s;
    double total_length{};
};


inline int native_thread_count() {
#ifdef _OPENMP
    int cap = 16;
    if (const char* value = std::getenv("SST_NATIVE_MAX_THREADS")) {
        try {
            cap = std::max(1, std::stoi(value));
        } catch (...) {
            cap = 16;
        }
    }
    return std::max(1, std::min(cap, omp_get_max_threads()));
#else
    return 1;
#endif
}

inline std::size_t idx3(std::size_t i, std::size_t c) {
    return 3 * i + c;
}

Curve make_curve(const py::array_t<double, py::array::c_style | py::array::forcecast>& array) {
    const auto info = array.request();
    if (info.ndim != 2 || info.shape[1] != 3) {
        throw std::invalid_argument("Each curve must have shape (N, 3)");
    }
    if (info.shape[0] < 3) {
        throw std::invalid_argument("Each closed curve needs at least three points");
    }
    Curve out;
    out.n = static_cast<std::size_t>(info.shape[0]);
    const auto* ptr = static_cast<const double*>(info.ptr);
    out.points.assign(ptr, ptr + out.n * 3);
    out.mid.resize(out.n * 3);
    out.dl.resize(out.n * 3);
    out.vertex_s.resize(out.n);
    out.mid_s.resize(out.n);
    std::vector<double> seglen(out.n, 0.0);
    for (std::size_t i = 0; i < out.n; ++i) {
        const std::size_t j = (i + 1) % out.n;
        for (std::size_t c = 0; c < 3; ++c) {
            const double a = out.points[idx3(i, c)];
            const double b = out.points[idx3(j, c)];
            out.mid[idx3(i, c)] = 0.5 * (a + b);
            out.dl[idx3(i, c)] = b - a;
        }
        const double dx = out.dl[idx3(i, 0)];
        const double dy = out.dl[idx3(i, 1)];
        const double dz = out.dl[idx3(i, 2)];
        seglen[i] = std::sqrt(dx * dx + dy * dy + dz * dz);
    }
    double cumulative = 0.0;
    for (std::size_t i = 0; i < out.n; ++i) {
        out.vertex_s[i] = cumulative;
        out.mid_s[i] = cumulative + 0.5 * seglen[i];
        cumulative += seglen[i];
    }
    out.total_length = cumulative;
    return out;
}

std::vector<Curve> make_curves(const py::list& curves) {
    std::vector<Curve> out;
    out.reserve(curves.size());
    for (const py::handle item : curves) {
        out.push_back(make_curve(py::cast<py::array_t<double, py::array::c_style | py::array::forcecast>>(item)));
    }
    if (out.empty()) {
        throw std::invalid_argument("At least one curve is required");
    }
    return out;
}

inline std::size_t cyclic_distance(std::size_t a, std::size_t b, std::size_t n) {
    const std::size_t d = (a > b) ? (a - b) : (b - a);
    return std::min(d, n - d);
}

inline double cyclic_arc_distance(double a, double b, double total_length) {
    const double d = std::abs(a - b);
    return std::min(d, std::max(0.0, total_length - d));
}

inline void add_segment_velocity(
    const double px,
    const double py,
    const double pz,
    const Curve& source,
    const double epsilon2,
    const bool self_curve,
    const std::size_t eval_index,
    const int local_skip,
    double& ux,
    double& uy,
    double& uz
) {
    for (std::size_t k = 0; k < source.n; ++k) {
        if (self_curve && cyclic_distance(eval_index, k, source.n) <= static_cast<std::size_t>(std::max(local_skip, 0))) {
            continue;
        }
        const double dx = px - source.mid[idx3(k, 0)];
        const double dy = py - source.mid[idx3(k, 1)];
        const double dz = pz - source.mid[idx3(k, 2)];
        const double lx = source.dl[idx3(k, 0)];
        const double ly = source.dl[idx3(k, 1)];
        const double lz = source.dl[idx3(k, 2)];
        const double cx = ly * dz - lz * dy;
        const double cy = lz * dx - lx * dz;
        const double cz = lx * dy - ly * dx;
        const double r2 = dx * dx + dy * dy + dz * dz + epsilon2;
        const double inv_r3 = 1.0 / (r2 * std::sqrt(r2));
        ux += cx * inv_r3;
        uy += cy * inv_r3;
        uz += cz * inv_r3;
    }
}

inline void add_segment_velocity_arc_exclusion(
    const double px,
    const double py,
    const double pz,
    const Curve& source,
    const double epsilon2,
    const bool self_curve,
    const double eval_s,
    const double exclusion_arc,
    double& ux,
    double& uy,
    double& uz
) {
    for (std::size_t k = 0; k < source.n; ++k) {
        if (self_curve && cyclic_arc_distance(eval_s, source.mid_s[k], source.total_length) <= std::max(exclusion_arc, 0.0)) {
            continue;
        }
        const double dx = px - source.mid[idx3(k, 0)];
        const double dy = py - source.mid[idx3(k, 1)];
        const double dz = pz - source.mid[idx3(k, 2)];
        const double lx = source.dl[idx3(k, 0)];
        const double ly = source.dl[idx3(k, 1)];
        const double lz = source.dl[idx3(k, 2)];
        const double cx = ly * dz - lz * dy;
        const double cy = lz * dx - lx * dz;
        const double cz = lx * dy - ly * dx;
        const double r2 = dx * dx + dy * dy + dz * dz + epsilon2;
        const double inv_r3 = 1.0 / (r2 * std::sqrt(r2));
        ux += cx * inv_r3;
        uy += cy * inv_r3;
        uz += cz * inv_r3;
    }
}

py::array_t<double> velocity_at_points(
    const py::array_t<double, py::array::c_style | py::array::forcecast>& evaluation_points,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& source_points,
    const double gamma,
    const double epsilon,
    const bool same_curve,
    const int local_skip
) {
    const auto eval_info = evaluation_points.request();
    if (eval_info.ndim != 2 || eval_info.shape[1] != 3) {
        throw std::invalid_argument("evaluation_points must have shape (N, 3)");
    }
    if (epsilon < 0.0) {
        throw std::invalid_argument("epsilon must be non-negative");
    }
    const Curve source = make_curve(source_points);
    const std::size_t n_eval = static_cast<std::size_t>(eval_info.shape[0]);
    if (same_curve && n_eval != source.n) {
        throw std::invalid_argument("same_curve=True requires equal evaluation/source point counts");
    }
    const auto* eval = static_cast<const double*>(eval_info.ptr);
    py::array_t<double> output({static_cast<py::ssize_t>(n_eval), py::ssize_t(3)});
    auto out_info = output.request();
    auto* out = static_cast<double*>(out_info.ptr);
    const double factor = gamma / (4.0 * PI);
    const double epsilon2 = epsilon * epsilon;

    {
        py::gil_scoped_release release;
        #pragma omp parallel for schedule(static) if(n_eval >= 256) num_threads(native_thread_count())
        for (py::ssize_t ip = 0; ip < static_cast<py::ssize_t>(n_eval); ++ip) {
            const std::size_t p = static_cast<std::size_t>(ip);
            double ux = 0.0, uy = 0.0, uz = 0.0;
            add_segment_velocity(
                eval[idx3(p, 0)], eval[idx3(p, 1)], eval[idx3(p, 2)],
                source, epsilon2, same_curve, p, local_skip, ux, uy, uz
            );
            out[idx3(p, 0)] = factor * ux;
            out[idx3(p, 1)] = factor * uy;
            out[idx3(p, 2)] = factor * uz;
        }
    }
    return output;
}

py::list link_velocity_batch(
    const py::list& curve_arrays,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& sign_matrix,
    const double epsilon,
    const int local_skip
) {
    if (epsilon < 0.0) {
        throw std::invalid_argument("epsilon must be non-negative");
    }
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const auto sign_info = sign_matrix.request();
    if (sign_info.ndim != 2 || static_cast<std::size_t>(sign_info.shape[1]) != curves.size()) {
        throw std::invalid_argument("sign_matrix must have shape (S, number_of_curves)");
    }
    const std::size_t sectors = static_cast<std::size_t>(sign_info.shape[0]);
    const std::size_t m = curves.size();
    const auto* signs = static_cast<const double*>(sign_info.ptr);
    const double epsilon2 = epsilon * epsilon;
    const double factor = 1.0 / (4.0 * PI);

    py::list outputs;
    std::vector<py::array_t<double>> arrays;
    std::vector<double*> pointers;
    arrays.reserve(m);
    pointers.reserve(m);
    for (const Curve& curve : curves) {
        arrays.emplace_back(py::array_t<double>({
            static_cast<py::ssize_t>(sectors),
            static_cast<py::ssize_t>(curve.n),
            py::ssize_t(3)
        }));
        pointers.push_back(static_cast<double*>(arrays.back().request().ptr));
    }

    {
        py::gil_scoped_release release;
        for (std::size_t target_index = 0; target_index < m; ++target_index) {
            const Curve& target = curves[target_index];
            double* out = pointers[target_index];
            #pragma omp parallel for schedule(static) if(target.n >= 256) num_threads(native_thread_count())
            for (py::ssize_t ipp = 0; ipp < static_cast<py::ssize_t>(target.n); ++ipp) {
                const std::size_t p = static_cast<std::size_t>(ipp);
                std::vector<std::array<double, 3>> contribution(m, {0.0, 0.0, 0.0});
                const double px = target.points[idx3(p, 0)];
                const double py = target.points[idx3(p, 1)];
                const double pz = target.points[idx3(p, 2)];
                for (std::size_t source_index = 0; source_index < m; ++source_index) {
                    double ux = 0.0, uy = 0.0, uz = 0.0;
                    add_segment_velocity(
                        px, py, pz, curves[source_index], epsilon2,
                        target_index == source_index, p, local_skip, ux, uy, uz
                    );
                    contribution[source_index] = {factor * ux, factor * uy, factor * uz};
                }
                for (std::size_t sector = 0; sector < sectors; ++sector) {
                    double ux = 0.0, uy = 0.0, uz = 0.0;
                    for (std::size_t source_index = 0; source_index < m; ++source_index) {
                        const double sigma = signs[sector * m + source_index];
                        ux += sigma * contribution[source_index][0];
                        uy += sigma * contribution[source_index][1];
                        uz += sigma * contribution[source_index][2];
                    }
                    const std::size_t base = (sector * target.n + p) * 3;
                    out[base + 0] = ux;
                    out[base + 1] = uy;
                    out[base + 2] = uz;
                }
            }
        }
    }

    for (auto& array : arrays) {
        outputs.append(array);
    }
    return outputs;
}

py::list link_velocity_batch_arc_exclusion(
    const py::list& curve_arrays,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& sign_matrix,
    const double epsilon,
    const double exclusion_arc
) {
    if (epsilon < 0.0 || exclusion_arc < 0.0) {
        throw std::invalid_argument("epsilon and exclusion_arc must be non-negative");
    }
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const auto sign_info = sign_matrix.request();
    if (sign_info.ndim != 2 || static_cast<std::size_t>(sign_info.shape[1]) != curves.size()) {
        throw std::invalid_argument("sign_matrix must have shape (S, number_of_curves)");
    }
    const std::size_t sectors = static_cast<std::size_t>(sign_info.shape[0]);
    const std::size_t m = curves.size();
    const auto* signs = static_cast<const double*>(sign_info.ptr);
    const double epsilon2 = epsilon * epsilon;
    const double factor = 1.0 / (4.0 * PI);

    py::list outputs;
    std::vector<py::array_t<double>> arrays;
    std::vector<double*> pointers;
    arrays.reserve(m); pointers.reserve(m);
    for (const Curve& curve : curves) {
        arrays.emplace_back(py::array_t<double>({
            static_cast<py::ssize_t>(sectors),
            static_cast<py::ssize_t>(curve.n),
            py::ssize_t(3)
        }));
        pointers.push_back(static_cast<double*>(arrays.back().request().ptr));
    }

    {
        py::gil_scoped_release release;
        for (std::size_t target_index = 0; target_index < m; ++target_index) {
            const Curve& target = curves[target_index];
            double* out = pointers[target_index];
            #pragma omp parallel for schedule(static) if(target.n >= 256) num_threads(native_thread_count())
            for (py::ssize_t ipp = 0; ipp < static_cast<py::ssize_t>(target.n); ++ipp) {
                const std::size_t p = static_cast<std::size_t>(ipp);
                std::vector<std::array<double, 3>> contribution(m, {0.0, 0.0, 0.0});
                const double px = target.points[idx3(p, 0)];
                const double py = target.points[idx3(p, 1)];
                const double pz = target.points[idx3(p, 2)];
                for (std::size_t source_index = 0; source_index < m; ++source_index) {
                    double ux = 0.0, uy = 0.0, uz = 0.0;
                    const bool same = target_index == source_index;
                    const double eval_s = same ? target.vertex_s[p] : 0.0;
                    add_segment_velocity_arc_exclusion(
                        px, py, pz, curves[source_index], epsilon2, same,
                        eval_s, exclusion_arc, ux, uy, uz
                    );
                    contribution[source_index] = {factor * ux, factor * uy, factor * uz};
                }
                for (std::size_t sector = 0; sector < sectors; ++sector) {
                    double ux = 0.0, uy = 0.0, uz = 0.0;
                    for (std::size_t source_index = 0; source_index < m; ++source_index) {
                        const double sigma = signs[sector * m + source_index];
                        ux += sigma * contribution[source_index][0];
                        uy += sigma * contribution[source_index][1];
                        uz += sigma * contribution[source_index][2];
                    }
                    const std::size_t base = (sector * target.n + p) * 3;
                    out[base + 0] = ux; out[base + 1] = uy; out[base + 2] = uz;
                }
            }
        }
    }
    for (auto& array : arrays) outputs.append(array);
    return outputs;
}

py::array_t<double> gauss_linking_matrix(const py::list& curve_arrays) {
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const std::size_t m = curves.size();
    py::array_t<double> output({static_cast<py::ssize_t>(m), static_cast<py::ssize_t>(m)});
    auto out_info = output.request();
    auto* out = static_cast<double*>(out_info.ptr);
    std::fill(out, out + m * m, 0.0);

    {
        py::gil_scoped_release release;
        for (std::size_t i = 0; i < m; ++i) {
            for (std::size_t j = i + 1; j < m; ++j) {
                const Curve& a = curves[i];
                const Curve& b = curves[j];
                double sum = 0.0;
                #pragma omp parallel for reduction(+:sum) schedule(static) if(a.n >= 256) num_threads(native_thread_count())
                for (py::ssize_t iaa = 0; iaa < static_cast<py::ssize_t>(a.n); ++iaa) {
                    const std::size_t ia = static_cast<std::size_t>(iaa);
                    double local = 0.0;
                    const double ax = a.dl[idx3(ia, 0)];
                    const double ay = a.dl[idx3(ia, 1)];
                    const double az = a.dl[idx3(ia, 2)];
                    for (std::size_t jb = 0; jb < b.n; ++jb) {
                        const double bx = b.dl[idx3(jb, 0)];
                        const double by = b.dl[idx3(jb, 1)];
                        const double bz = b.dl[idx3(jb, 2)];
                        const double cx = ay * bz - az * by;
                        const double cy = az * bx - ax * bz;
                        const double cz = ax * by - ay * bx;
                        const double dx = a.mid[idx3(ia, 0)] - b.mid[idx3(jb, 0)];
                        const double dy = a.mid[idx3(ia, 1)] - b.mid[idx3(jb, 1)];
                        const double dz = a.mid[idx3(ia, 2)] - b.mid[idx3(jb, 2)];
                        const double r2 = dx * dx + dy * dy + dz * dz;
                        const double inv_r3 = 1.0 / (r2 * std::sqrt(r2));
                        local += (cx * dx + cy * dy + cz * dz) * inv_r3;
                    }
                    sum += local;
                }
                const double value = sum / (4.0 * PI);
                out[i * m + j] = value;
                out[j * m + i] = value;
            }
        }
    }
    return output;
}

py::array_t<double> neumann_coupling_matrices(
    const py::list& curve_arrays,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& epsilons,
    const int local_skip
) {
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const auto eps_info = epsilons.request();
    if (eps_info.ndim != 1) {
        throw std::invalid_argument("epsilons must be a one-dimensional array");
    }
    const std::size_t ecount = static_cast<std::size_t>(eps_info.shape[0]);
    const auto* eps_ptr = static_cast<const double*>(eps_info.ptr);
    for (std::size_t e = 0; e < ecount; ++e) {
        if (eps_ptr[e] < 0.0) {
            throw std::invalid_argument("epsilons must be non-negative");
        }
    }
    const std::size_t m = curves.size();
    py::array_t<double> output({
        static_cast<py::ssize_t>(ecount),
        static_cast<py::ssize_t>(m),
        static_cast<py::ssize_t>(m)
    });
    auto out_info = output.request();
    auto* out = static_cast<double*>(out_info.ptr);
    std::fill(out, out + ecount * m * m, 0.0);

    {
        py::gil_scoped_release release;
        for (std::size_t e = 0; e < ecount; ++e) {
            const double epsilon2 = eps_ptr[e] * eps_ptr[e];
            for (std::size_t i = 0; i < m; ++i) {
                for (std::size_t j = i; j < m; ++j) {
                    const Curve& a = curves[i];
                    const Curve& b = curves[j];
                    double sum = 0.0;
                    #pragma omp parallel for reduction(+:sum) schedule(static) if(a.n >= 256) num_threads(native_thread_count())
                    for (py::ssize_t iaa = 0; iaa < static_cast<py::ssize_t>(a.n); ++iaa) {
                        const std::size_t ia = static_cast<std::size_t>(iaa);
                        double local = 0.0;
                        const double ax = a.dl[idx3(ia, 0)];
                        const double ay = a.dl[idx3(ia, 1)];
                        const double az = a.dl[idx3(ia, 2)];
                        for (std::size_t jb = 0; jb < b.n; ++jb) {
                            if (i == j && cyclic_distance(ia, jb, a.n) <= static_cast<std::size_t>(std::max(local_skip, 0))) {
                                continue;
                            }
                            const double bx = b.dl[idx3(jb, 0)];
                            const double by = b.dl[idx3(jb, 1)];
                            const double bz = b.dl[idx3(jb, 2)];
                            const double dot = ax * bx + ay * by + az * bz;
                            const double dx = a.mid[idx3(ia, 0)] - b.mid[idx3(jb, 0)];
                            const double dy = a.mid[idx3(ia, 1)] - b.mid[idx3(jb, 1)];
                            const double dz = a.mid[idx3(ia, 2)] - b.mid[idx3(jb, 2)];
                            const double denom = std::sqrt(dx * dx + dy * dy + dz * dz + epsilon2);
                            local += dot / denom;
                        }
                        sum += local;
                    }
                    const double value = sum / (8.0 * PI);
                    out[(e * m + i) * m + j] = value;
                    out[(e * m + j) * m + i] = value;
                }
            }
        }
    }
    return output;
}

py::array_t<double> neumann_coupling_matrices_arc_exclusion(
    const py::list& curve_arrays,
    const py::array_t<double, py::array::c_style | py::array::forcecast>& epsilons,
    const double exclusion_arc
) {
    if (exclusion_arc < 0.0) throw std::invalid_argument("exclusion_arc must be non-negative");
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const auto eps_info = epsilons.request();
    if (eps_info.ndim != 1) throw std::invalid_argument("epsilons must be a one-dimensional array");
    const std::size_t ecount = static_cast<std::size_t>(eps_info.shape[0]);
    const auto* eps_ptr = static_cast<const double*>(eps_info.ptr);
    for (std::size_t e = 0; e < ecount; ++e) if (eps_ptr[e] < 0.0) throw std::invalid_argument("epsilons must be non-negative");
    const std::size_t m = curves.size();
    py::array_t<double> output({static_cast<py::ssize_t>(ecount), static_cast<py::ssize_t>(m), static_cast<py::ssize_t>(m)});
    auto out_info = output.request();
    auto* out = static_cast<double*>(out_info.ptr);
    std::fill(out, out + ecount * m * m, 0.0);
    {
        py::gil_scoped_release release;
        for (std::size_t e = 0; e < ecount; ++e) {
            const double epsilon2 = eps_ptr[e] * eps_ptr[e];
            for (std::size_t i = 0; i < m; ++i) {
                for (std::size_t j = i; j < m; ++j) {
                    const Curve& a = curves[i]; const Curve& b = curves[j];
                    double sum = 0.0;
                    #pragma omp parallel for reduction(+:sum) schedule(static) if(a.n >= 256) num_threads(native_thread_count())
                    for (py::ssize_t iaa = 0; iaa < static_cast<py::ssize_t>(a.n); ++iaa) {
                        const std::size_t ia = static_cast<std::size_t>(iaa);
                        double local = 0.0;
                        const double ax = a.dl[idx3(ia, 0)], ay = a.dl[idx3(ia, 1)], az = a.dl[idx3(ia, 2)];
                        for (std::size_t jb = 0; jb < b.n; ++jb) {
                            if (i == j && cyclic_arc_distance(a.mid_s[ia], b.mid_s[jb], a.total_length) <= exclusion_arc) continue;
                            const double bx = b.dl[idx3(jb, 0)], by = b.dl[idx3(jb, 1)], bz = b.dl[idx3(jb, 2)];
                            const double dot = ax * bx + ay * by + az * bz;
                            const double dx = a.mid[idx3(ia, 0)] - b.mid[idx3(jb, 0)];
                            const double dy = a.mid[idx3(ia, 1)] - b.mid[idx3(jb, 1)];
                            const double dz = a.mid[idx3(ia, 2)] - b.mid[idx3(jb, 2)];
                            const double denom = std::sqrt(dx * dx + dy * dy + dz * dz + epsilon2);
                            local += dot / denom;
                        }
                        sum += local;
                    }
                    const double value = sum / (8.0 * PI);
                    out[(e * m + i) * m + j] = value;
                    out[(e * m + j) * m + i] = value;
                }
            }
        }
    }
    return output;
}


inline double softplus_stable(const double z) {
    if (z > 0.0) return z + std::log1p(std::exp(-z));
    return std::log1p(std::exp(z));
}

double tube_repulsion_energy(
    const py::list& curve_arrays,
    const double diameter,
    const double softness,
    const double contact_margin,
    const double local_skip_fraction
) {
    if (diameter <= 0.0) throw std::invalid_argument("diameter must be positive");
    if (softness < 0.0) throw std::invalid_argument("softness must be non-negative");
    if (local_skip_fraction < 0.0) throw std::invalid_argument("local_skip_fraction must be non-negative");
    const std::vector<Curve> curves = make_curves(curve_arrays);
    const double threshold = diameter * (1.0 + contact_margin);
    const double softness_abs = std::max(softness * diameter, 1.0e-12);
    double total = 0.0;
    long long count = 0;
    {
        py::gil_scoped_release release;
        for (std::size_t i = 0; i < curves.size(); ++i) {
            const Curve& a = curves[i];
            for (std::size_t j = i; j < curves.size(); ++j) {
                const Curve& b = curves[j];
                const bool self_pair = (i == j);
                const std::size_t skip = self_pair
                    ? std::max<std::size_t>(3, static_cast<std::size_t>(local_skip_fraction * static_cast<double>(a.n)))
                    : 0;
                double pair_total = 0.0;
                long long pair_count = 0;
                #pragma omp parallel for reduction(+:pair_total,pair_count) schedule(static) if(a.n >= 256) num_threads(native_thread_count())
                for (py::ssize_t iaa = 0; iaa < static_cast<py::ssize_t>(a.n); ++iaa) {
                    const std::size_t ia = static_cast<std::size_t>(iaa);
                    double local_total = 0.0;
                    long long local_count = 0;
                    const std::size_t jb_begin = self_pair ? ia + 1 : 0;
                    for (std::size_t jb = jb_begin; jb < b.n; ++jb) {
                        if (self_pair && cyclic_distance(ia, jb, a.n) <= skip) continue;
                        const double dx = a.points[idx3(ia, 0)] - b.points[idx3(jb, 0)];
                        const double dy = a.points[idx3(ia, 1)] - b.points[idx3(jb, 1)];
                        const double dz = a.points[idx3(ia, 2)] - b.points[idx3(jb, 2)];
                        const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);
                        const double z = (threshold - distance) / softness_abs;
                        const double value = softplus_stable(z);
                        local_total += value * value;
                        ++local_count;
                    }
                    pair_total += local_total;
                    pair_count += local_count;
                }
                total += pair_total;
                count += pair_count;
            }
        }
    }
    return total / static_cast<double>(std::max<long long>(count, 1));
}

py::dict build_info() {
    py::dict info;
#ifdef _OPENMP
    info["openmp"] = true;
    info["openmp_max_threads"] = omp_get_max_threads();
    info["native_thread_cap"] = native_thread_count();
#else
    info["openmp"] = false;
    info["openmp_max_threads"] = 1;
    info["native_thread_cap"] = 1;
#endif
#ifdef __VERSION__
    info["compiler"] = std::string(__VERSION__);
#elif defined(_MSC_VER)
    info["compiler"] = std::string("MSVC ") + std::to_string(_MSC_VER);
#else
    info["compiler"] = "unknown";
#endif
    info["cpp_standard"] = 201703;
    info["kernel"] = "midpoint-segment Rosenhead-Moore Biot-Savart";
    info["tube_repulsion_native"] = true;
    info["neumann_symmetric_pair_reuse"] = true;
    return info;
}

} // namespace

PYBIND11_MODULE(_native, m) {
    m.doc() = "Native C++17/OpenMP kernels for SST ideal-link audits.";
    m.def("velocity_at_points", &velocity_at_points,
          py::arg("evaluation_points"), py::arg("source_points"), py::arg("gamma"),
          py::arg("epsilon"), py::arg("same_curve") = false, py::arg("local_skip") = 3);
    m.def("link_velocity_batch", &link_velocity_batch,
          py::arg("curves"), py::arg("sign_matrix"), py::arg("epsilon"), py::arg("local_skip") = 3);
    m.def("link_velocity_batch_arc_exclusion", &link_velocity_batch_arc_exclusion,
          py::arg("curves"), py::arg("sign_matrix"), py::arg("epsilon"), py::arg("exclusion_arc"));
    m.def("gauss_linking_matrix", &gauss_linking_matrix, py::arg("curves"));
    m.def("neumann_coupling_matrices", &neumann_coupling_matrices,
          py::arg("curves"), py::arg("epsilons"), py::arg("local_skip") = 2);
    m.def("neumann_coupling_matrices_arc_exclusion", &neumann_coupling_matrices_arc_exclusion,
          py::arg("curves"), py::arg("epsilons"), py::arg("exclusion_arc"));
    m.def("tube_repulsion_energy", &tube_repulsion_energy,
          py::arg("curves"), py::arg("diameter"), py::arg("softness") = 0.04,
          py::arg("contact_margin") = 0.0, py::arg("local_skip_fraction") = 0.035);
    m.def("build_info", &build_info);
}
