#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace py = pybind11;

namespace {
constexpr double SST_PI = 3.141592653589793238462643383279502884;
}


py::dict quadrupole_rg2(const std::vector<double>& vertices) {
    if (vertices.empty() || vertices.size() % 3 != 0) {
        throw std::runtime_error("vertices_flat must contain 3*N floats");
    }
    const std::size_t n = vertices.size() / 3;
    double cx = 0.0, cy = 0.0, cz = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        cx += vertices[3*i];
        cy += vertices[3*i + 1];
        cz += vertices[3*i + 2];
    }
    cx /= static_cast<double>(n);
    cy /= static_cast<double>(n);
    cz /= static_cast<double>(n);

    std::array<std::array<double, 3>, 3> Q{};
    double rg2 = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const double x = vertices[3*i] - cx;
        const double y = vertices[3*i + 1] - cy;
        const double z = vertices[3*i + 2] - cz;
        const double v[3] = {x, y, z};
        const double r2 = x*x + y*y + z*z;
        rg2 += r2;
        for (int a = 0; a < 3; ++a) {
            for (int b = 0; b < 3; ++b) {
                Q[a][b] += v[a] * v[b];
            }
            Q[a][a] -= r2 / 3.0;
        }
    }
    const double inv = 1.0 / static_cast<double>(n);
    std::vector<std::vector<double>> q(3, std::vector<double>(3, 0.0));
    for (int a = 0; a < 3; ++a) {
        for (int b = 0; b < 3; ++b) q[a][b] = Q[a][b] * inv;
    }
    py::dict out;
    out["Q"] = q;
    out["Rg2"] = rg2 * inv;
    out["centroid"] = std::vector<double>{cx, cy, cz};
    return out;
}

std::vector<double> biot_savart_velocity(
    const std::vector<double>& vertices,
    const std::vector<double>& samples,
    double gamma,
    double epsilon_bs
) {
    if (vertices.empty() || vertices.size() % 3 != 0 || samples.size() % 3 != 0) {
        throw std::runtime_error("vertices and samples must be flattened 3-vectors");
    }
    if (epsilon_bs <= 0.0) throw std::runtime_error("epsilon_bs must be positive");
    const std::size_t n = vertices.size() / 3;
    const std::size_t m = samples.size() / 3;
    std::vector<double> out(3 * m, 0.0);
    const double coeff = gamma / (4.0 * SST_PI);
    const double eps2 = epsilon_bs * epsilon_bs;
    for (std::size_t si = 0; si < m; ++si) {
        const double sx = samples[3*si];
        const double sy = samples[3*si + 1];
        const double sz = samples[3*si + 2];
        double ux = 0.0, uy = 0.0, uz = 0.0;
        for (std::size_t i = 0; i < n; ++i) {
            const std::size_t j = (i + 1) % n;
            const double x0 = vertices[3*i];
            const double y0 = vertices[3*i + 1];
            const double z0 = vertices[3*i + 2];
            const double x1 = vertices[3*j];
            const double y1 = vertices[3*j + 1];
            const double z1 = vertices[3*j + 2];
            const double dlx = x1 - x0;
            const double dly = y1 - y0;
            const double dlz = z1 - z0;
            const double mx = 0.5 * (x0 + x1);
            const double my = 0.5 * (y0 + y1);
            const double mz = 0.5 * (z0 + z1);
            const double rx = sx - mx;
            const double ry = sy - my;
            const double rz = sz - mz;
            const double denom = std::pow(rx*rx + ry*ry + rz*rz + eps2, 1.5);
            ux += (dly * rz - dlz * ry) / denom;
            uy += (dlz * rx - dlx * rz) / denom;
            uz += (dlx * ry - dly * rx) / denom;
        }
        out[3*si] = coeff * ux;
        out[3*si + 1] = coeff * uy;
        out[3*si + 2] = coeff * uz;
    }
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "SST dark-knot Rayleigh diagnostic kernels";
    m.def("quadrupole_rg2", &quadrupole_rg2, "Traceless quadrupole and gyration radius");
    m.def("biot_savart_velocity", &biot_savart_velocity,
          "Regularized midpoint-segment Biot-Savart velocity at sample points");
}
