#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace sst_fermat {

struct ProfileEval {
    double beta{};
    double d_beta{};
    double dd_beta{};
};

inline ProfileEval external_profile(double x, double beta0) {
    if (!(x > 0.0)) throw std::invalid_argument("x must be positive");
    return {beta0 / x, -beta0 / (x * x), 2.0 * beta0 / (x * x * x)};
}

inline ProfileEval rankine_profile(double x, double beta0, double a) {
    if (!(x >= 0.0) || !(a > 0.0)) throw std::invalid_argument("invalid x or a");
    if (x < a) {
        const double slope = beta0 / (a * a);
        return {slope * x, slope, 0.0};
    }
    return external_profile(x, beta0);
}

inline ProfileEval rosenhead_profile(double x, double beta0, double a) {
    if (!(x >= 0.0) || !(a > 0.0)) throw std::invalid_argument("invalid x or a");
    const double d = x * x + a * a;
    const double beta = beta0 * x / d;
    const double db = beta0 * (a * a - x * x) / (d * d);
    const double ddb = beta0 * 2.0 * x * (x * x - 3.0 * a * a) / (d * d * d);
    return {beta, db, ddb};
}

inline ProfileEval lamb_oseen_profile(double x, double beta0, double a) {
    if (!(x >= 0.0) || !(a > 0.0)) throw std::invalid_argument("invalid x or a");
    if (x < 1e-6 * a) {
        const double a2 = a * a;
        const double a4 = a2 * a2;
        const double a6 = a4 * a2;
        const double x2 = x * x;
        const double x3 = x2 * x;
        const double x4 = x2 * x2;
        const double x5 = x4 * x;
        return {
            beta0 * (x / (2.0 * a2) - x3 / (8.0 * a4) + x5 / (48.0 * a6)),
            beta0 * (1.0 / (2.0 * a2) - 3.0 * x2 / (8.0 * a4) + 5.0 * x4 / (48.0 * a6)),
            beta0 * (-3.0 * x / (4.0 * a4) + 5.0 * x3 / (12.0 * a6)),
        };
    }
    const double a2 = a * a;
    const double e = std::exp(-x * x / (2.0 * a2));
    const double g = 1.0 - e;
    const double beta = beta0 * g / x;
    const double db = beta0 * (e / a2 - g / (x * x));
    const double ddb = beta0 * (-e * x / (a2 * a2) - e / (a2 * x) + 2.0 * g / (x * x * x));
    return {beta, db, ddb};
}

inline ProfileEval eval_profile(const std::string& profile, double x, double beta0, double a) {
    if (profile == "external") return external_profile(x, beta0);
    if (profile == "rankine") return rankine_profile(x, beta0, a);
    if (profile == "rosenhead") return rosenhead_profile(x, beta0, a);
    if (profile == "lamb_oseen") return lamb_oseen_profile(x, beta0, a);
    throw std::invalid_argument("unknown profile: " + profile);
}

inline double fermat_residual(const ProfileEval& p, double x) {
    return -x * p.beta * p.d_beta - (1.0 - p.beta * p.beta);
}

inline double log_n_prime(const ProfileEval& p) {
    const double d = 1.0 - p.beta * p.beta;
    if (!(d > 0.0)) return std::numeric_limits<double>::quiet_NaN();
    return p.beta * p.d_beta / d;
}

inline double log_n_second(const ProfileEval& p) {
    const double d = 1.0 - p.beta * p.beta;
    if (!(d > 0.0)) return std::numeric_limits<double>::quiet_NaN();
    const double bp2 = p.d_beta * p.d_beta;
    return (((bp2 + p.beta * p.dd_beta) * d) + 2.0 * p.beta * p.beta * bp2) / (d * d);
}

inline double k_hat(const ProfileEval& p, double x) {
    const double s2 = 1.0 - p.beta * p.beta;
    if (!(s2 > 0.0) || !(x > 0.0)) return std::numeric_limits<double>::quiet_NaN();
    return -s2 * (log_n_second(p) + log_n_prime(p) / x);
}

inline double r_f_second_x(const ProfileEval& p, double x) {
    const double s2 = 1.0 - p.beta * p.beta;
    if (!(s2 > 0.0) || !(x > 0.0)) return std::numeric_limits<double>::quiet_NaN();
    const double n = 1.0 / std::sqrt(s2);
    return n * (log_n_prime(p) + x * log_n_second(p));
}

inline std::vector<std::pair<double, double>> split_intervals(
    const std::string& profile, double xmin, double xmax, double a) {
    if (!(xmin > 0.0) || !(xmax > xmin)) throw std::invalid_argument("invalid interval");
    if (profile == "rankine" && a > xmin && a < xmax) {
        const double left = std::nextafter(a, xmin);
        const double right = std::nextafter(a, xmax);
        return {{xmin, left}, {right, xmax}};
    }
    return {{xmin, xmax}};
}

template <typename F>
inline std::vector<double> roots_log_bisection(
    F&& fn,
    const std::vector<std::pair<double, double>>& intervals,
    int samples,
    double tol = 1e-13) {
    std::vector<double> roots;
    samples = std::max(samples, 32);
    for (const auto& [lo0, hi0] : intervals) {
        double lo = lo0;
        double hi = hi0;
        if (!(hi > lo) || !(lo > 0.0)) continue;
        const int n = std::max(16, samples / static_cast<int>(intervals.size()));
        double x_prev = lo;
        double f_prev = fn(x_prev);
        for (int i = 1; i <= n; ++i) {
            const double t = static_cast<double>(i) / static_cast<double>(n);
            const double x = std::exp(std::log(lo) * (1.0 - t) + std::log(hi) * t);
            const double fx = fn(x);
            if (std::isfinite(f_prev) && std::isfinite(fx)) {
                if (std::abs(f_prev) < tol) roots.push_back(x_prev);
                if (f_prev * fx < 0.0) {
                    double a0 = x_prev, b0 = x, fa = f_prev, fb = fx;
                    for (int it = 0; it < 100; ++it) {
                        const double mid = 0.5 * (a0 + b0);
                        const double fm = fn(mid);
                        if (!std::isfinite(fm)) break;
                        if (std::abs(fm) < tol || (b0 - a0) < tol * std::max(1.0, mid)) {
                            a0 = b0 = mid;
                            break;
                        }
                        if (fa * fm <= 0.0) {
                            b0 = mid;
                            fb = fm;
                        } else {
                            a0 = mid;
                            fa = fm;
                        }
                    }
                    roots.push_back(0.5 * (a0 + b0));
                }
            }
            x_prev = x;
            f_prev = fx;
        }
    }
    std::sort(roots.begin(), roots.end());
    std::vector<double> unique;
    for (double r : roots) {
        if (unique.empty() || std::abs(r - unique.back()) > 1e-8 * std::max(1.0, r)) unique.push_back(r);
    }
    return unique;
}

struct Vec3 {
    double x{}, y{}, z{};
};

inline Vec3 operator+(const Vec3& a, const Vec3& b) { return {a.x+b.x, a.y+b.y, a.z+b.z}; }
inline Vec3 operator-(const Vec3& a, const Vec3& b) { return {a.x-b.x, a.y-b.y, a.z-b.z}; }
inline Vec3 operator*(double s, const Vec3& a) { return {s*a.x, s*a.y, s*a.z}; }
inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return {a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x};
}

struct FieldJacobian {
    Vec3 beta{};
    // Row-major J_ij = d beta_i / d x_j.
    std::array<double, 9> jacobian{};
};

inline FieldJacobian biot_savart_point_with_jacobian(
    const std::vector<Vec3>& centerline,
    const Vec3& probe,
    double coefficient,
    double epsilon,
    const std::string& kernel_model = "rosenhead_midpoint") {
    if (centerline.size() < 3) throw std::invalid_argument("centerline needs >=3 points");
    if (!(epsilon > 0.0)) throw std::invalid_argument("epsilon must be positive");
    if (kernel_model != "rosenhead_midpoint") {
        throw std::invalid_argument("unknown kernel_model: " + kernel_model);
    }
    FieldJacobian out{};
    const double eps2 = epsilon * epsilon;
    const std::array<Vec3, 3> basis{{{1.0,0.0,0.0},{0.0,1.0,0.0},{0.0,0.0,1.0}}};
    for (std::size_t i = 0; i < centerline.size(); ++i) {
        const Vec3& a = centerline[i];
        const Vec3& b = centerline[(i + 1) % centerline.size()];
        const Vec3 dl = b - a;
        const Vec3 mid = 0.5 * (a + b);
        const Vec3 r = probe - mid;
        const double q = r.x*r.x + r.y*r.y + r.z*r.z + eps2;
        const double inv3 = 1.0 / (q * std::sqrt(q));
        const double inv5 = inv3 / q;
        const Vec3 c = cross(dl, r);
        out.beta = out.beta + (coefficient * inv3) * c;
        const std::array<double, 3> rv{{r.x, r.y, r.z}};
        for (int j = 0; j < 3; ++j) {
            const Vec3 d_cross = cross(dl, basis[static_cast<std::size_t>(j)]);
            const Vec3 col = coefficient * (inv3 * d_cross - 3.0 * rv[static_cast<std::size_t>(j)] * inv5 * c);
            out.jacobian[0 * 3 + j] += col.x;
            out.jacobian[1 * 3 + j] += col.y;
            out.jacobian[2 * 3 + j] += col.z;
        }
    }
    return out;
}

inline std::vector<FieldJacobian> biot_savart_batch_with_jacobian(
    const std::vector<Vec3>& centerline,
    const std::vector<Vec3>& probes,
    double coefficient,
    double epsilon,
    const std::string& kernel_model = "rosenhead_midpoint") {
    std::vector<FieldJacobian> out;
    out.reserve(probes.size());
    for (const auto& p : probes) {
        out.push_back(biot_savart_point_with_jacobian(centerline, p, coefficient, epsilon, kernel_model));
    }
    return out;
}

inline std::vector<Vec3> biot_savart_batch(
    const std::vector<Vec3>& centerline,
    const std::vector<Vec3>& probes,
    double coefficient,
    double epsilon,
    const std::string& kernel_model = "rosenhead_midpoint") {
    if (centerline.size() < 3) throw std::invalid_argument("centerline needs >=3 points");
    if (!(epsilon > 0.0)) throw std::invalid_argument("epsilon must be positive");
    if (kernel_model != "rosenhead_midpoint") {
        throw std::invalid_argument("unknown kernel_model: " + kernel_model);
    }
    std::vector<Vec3> out(probes.size());
    const double eps2 = epsilon * epsilon;
    for (std::size_t j = 0; j < probes.size(); ++j) {
        Vec3 sum{};
        for (std::size_t i = 0; i < centerline.size(); ++i) {
            const Vec3& a = centerline[i];
            const Vec3& b = centerline[(i + 1) % centerline.size()];
            const Vec3 dl = b - a;
            const Vec3 mid = 0.5 * (a + b);
            const Vec3 r = probes[j] - mid;
            const double q = r.x*r.x + r.y*r.y + r.z*r.z + eps2;
            const double inv3 = 1.0 / (q * std::sqrt(q));
            sum = sum + (coefficient * inv3) * cross(dl, r);
        }
        out[j] = sum;
    }
    return out;
}

}  // namespace sst_fermat
