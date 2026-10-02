#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <vector>

namespace py = pybind11;

constexpr double PI =
    3.141592653589793238462643383279502884;

struct Vec3
{
    double x;
    double y;
    double z;
};

static inline Vec3 add(
    const Vec3& a,
    const Vec3& b)
{
    return {
        a.x + b.x,
        a.y + b.y,
        a.z + b.z
    };
}

static inline Vec3 sub(
    const Vec3& a,
    const Vec3& b)
{
    return {
        a.x - b.x,
        a.y - b.y,
        a.z - b.z
    };
}

static inline Vec3 mul(
    double s,
    const Vec3& a)
{
    return {
        s * a.x,
        s * a.y,
        s * a.z
    };
}

static inline double dot(
    const Vec3& a,
    const Vec3& b)
{
    return
        a.x * b.x
        + a.y * b.y
        + a.z * b.z;
}

static inline Vec3 cross(
    const Vec3& a,
    const Vec3& b)
{
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
}


static std::vector<Vec3> read_points(
    const py::array_t<
        double,
        py::array::c_style |
        py::array::forcecast
    >& arr)
{
    auto buffer = arr.request();

    if (
        buffer.ndim != 2 ||
        buffer.shape[1] != 3
    )
    {
        throw std::runtime_error(
            "Expected array shape (N,3)."
        );
    }

    const auto* ptr =
        static_cast<const double*>(
            buffer.ptr
        );

    const std::size_t n =
        static_cast<std::size_t>(
            buffer.shape[0]
        );

    std::vector<Vec3> out(n);

    for (std::size_t i = 0; i < n; ++i)
    {
        out[i] = {
            ptr[3 * i + 0],
            ptr[3 * i + 1],
            ptr[3 * i + 2]
        };
    }

    return out;
}


static py::array_t<double> to_array(
    const std::vector<Vec3>& values)
{
    const auto n =
        static_cast<py::ssize_t>(
            values.size()
        );

    py::array_t<double> out({
        n,
        static_cast<py::ssize_t>(3)
    });

    auto buffer = out.request();

    auto* ptr =
        static_cast<double*>(
            buffer.ptr
        );

    for (
        std::size_t i = 0;
        i < values.size();
        ++i
    )
    {
        ptr[3 * i + 0] = values[i].x;
        ptr[3 * i + 1] = values[i].y;
        ptr[3 * i + 2] = values[i].z;
    }

    return out;
}


static std::vector<Vec3>
periodic_derivative_q(
    const std::vector<Vec3>& x)
{
    const std::size_t n = x.size();

    if (n < 4)
    {
        throw std::runtime_error(
            "Need at least four points."
        );
    }

    const double dq =
        1.0 / static_cast<double>(n);

    std::vector<Vec3> out(n);

    for (
        std::size_t i = 0;
        i < n;
        ++i
    )
    {
        const std::size_t im =
            (i + n - 1) % n;

        const std::size_t ip =
            (i + 1) % n;

        out[i] =
            mul(
                0.5 / dq,
                sub(x[ip], x[im])
            );
    }

    return out;
}


py::array_t<double>
biot_savart_velocity(
    const py::array_t<
        double,
        py::array::c_style |
        py::array::forcecast
    >& points,
    double gamma,
    double core_a)
{
    const auto x =
        read_points(points);

    const auto dx =
        periodic_derivative_q(x);

    const std::size_t n =
        x.size();

    const double dq =
        1.0 / static_cast<double>(n);

    const double prefactor =
        gamma / (4.0 * PI);

    std::vector<Vec3> out(
        n,
        {0.0, 0.0, 0.0}
    );

    for (
        std::size_t i = 0;
        i < n;
        ++i
    )
    {
        Vec3 accum{
            0.0,
            0.0,
            0.0
        };

        for (
            std::size_t j = 0;
            j < n;
            ++j
        )
        {
            const Vec3 r =
                sub(x[i], x[j]);

            const double D =
                dot(r, r)
                + core_a * core_a;

            const Vec3 numerator =
                cross(dx[j], r);

            const Vec3 term =
                mul(
                    1.0 / std::pow(D, 1.5),
                    numerator
                );

            accum =
                add(accum, term);
        }

        out[i] =
            mul(
                prefactor * dq,
                accum
            );
    }

    return to_array(out);
}


py::array_t<double>
jacobian_action(
    const py::array_t<
        double,
        py::array::c_style |
        py::array::forcecast
    >& points,
    const py::array_t<
        double,
        py::array::c_style |
        py::array::forcecast
    >& perturbation,
    double gamma,
    double core_a)
{
    const auto x =
        read_points(points);

    const auto xi =
        read_points(perturbation);

    if (x.size() != xi.size())
    {
        throw std::runtime_error(
            "points and perturbation "
            "must have same N."
        );
    }

    const auto dx =
        periodic_derivative_q(x);

    const auto dxi =
        periodic_derivative_q(xi);

    const std::size_t n =
        x.size();

    const double dq =
        1.0 / static_cast<double>(n);

    const double prefactor =
        gamma / (4.0 * PI);

    std::vector<Vec3> out(
        n,
        {0.0, 0.0, 0.0}
    );

    for (
        std::size_t i = 0;
        i < n;
        ++i
    )
    {
        Vec3 accum{
            0.0,
            0.0,
            0.0
        };

        for (
            std::size_t j = 0;
            j < n;
            ++j
        )
        {
            const Vec3 r =
                sub(x[i], x[j]);

            const Vec3 dr =
                sub(xi[i], xi[j]);

            const double D =
                dot(r, r)
                + core_a * core_a;

            const Vec3 term_1 =
                mul(
                    1.0 / std::pow(D, 1.5),
                    cross(dxi[j], r)
                );

            const Vec3 term_2 =
                mul(
                    1.0 / std::pow(D, 1.5),
                    cross(dx[j], dr)
                );

            const double r_dot_dr =
                dot(r, dr);

            const Vec3 base_cross =
                cross(dx[j], r);

            const Vec3 term_3 =
                mul(
                    -3.0
                    * r_dot_dr
                    / std::pow(D, 2.5),
                    base_cross
                );

            accum =
                add(
                    accum,
                    add(
                        term_1,
                        add(term_2, term_3)
                    )
                );
        }

        out[i] =
            mul(
                prefactor * dq,
                accum
            );
    }

    return to_array(out);
}


double filament_energy(
    const py::array_t<
        double,
        py::array::c_style |
        py::array::forcecast
    >& points,
    double gamma,
    double core_a,
    double rho_f)
{
    const auto x =
        read_points(points);

    const auto dx =
        periodic_derivative_q(x);

    const std::size_t n =
        x.size();

    const double dq =
        1.0 / static_cast<double>(n);

    double total = 0.0;

    for (
        std::size_t i = 0;
        i < n;
        ++i
    )
    {
        for (
            std::size_t j = 0;
            j < n;
            ++j
        )
        {
            const Vec3 r =
                sub(x[i], x[j]);

            const double denominator =
                std::sqrt(
                    dot(r, r)
                    + core_a * core_a
                );

            total +=
                dot(dx[i], dx[j])
                / denominator;
        }
    }

    return
        rho_f
        * gamma * gamma
        * total
        * dq * dq
        / (8.0 * PI);
}


PYBIND11_MODULE(_native, m)
{
    m.doc() =
        "SST chiral Kelvin finite-core "
        "Biot-Savart kernels";

    m.def(
        "biot_savart_velocity",
        &biot_savart_velocity,
        "Regularized Biot-Savart velocity"
    );

    m.def(
        "jacobian_action",
        &jacobian_action,
        "Analytic Frechet/Jacobian action"
    );

    m.def(
        "filament_energy",
        &filament_energy,
        "Regularized filament energy proxy"
    );
}
