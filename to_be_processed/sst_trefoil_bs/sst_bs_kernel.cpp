/*
 * sst_bs_kernel.cpp
 * =================
 * pybind11 C++ kernel for Swirl-String Theory vortex-filament calculations.
 *
 * Exports
 * -------
 * biot_savart_integral(pts, a)
 *   Rosenhead-regularised Biot-Savart self-integral
 *     I(K, a) = sum_{i != j} (dl_i . dl_j) / |r_ij|_reg
 *   where  |r_ij|_reg = sqrt(|r_i - r_j|^2 + a^2).
 *   Multiply by rho_f * Gamma^2 / (4 pi) to get self-energy E_BS.
 *
 * writhe(pts)
 *   Gauss self-linking (writhe) integral via O(N^2) panel sum.
 *     Wr(K) = (1/4pi) sum_{i,j} (r_ij x T_i) . T_j / |r_ij|^3
 *   For the ideal trefoil Wr ≈ 3 (equal to the self-linking number).
 *
 * Build (see build.py)
 * --------------------
 *   g++ -O3 -march=native -fopenmp -shared -std=c++17 -fPIC \
 *       $(python3 -m pybind11 --includes) \
 *       sst_bs_kernel.cpp \
 *       -o sst_bs_kernel$(python3-config --extension-suffix)
 *
 *   OpenMP is optional: if -fopenmp is absent the code still compiles and
 *   runs single-threaded (the #pragma omp lines are silently ignored).
 *
 * Coordinate convention
 * ---------------------
 *   pts   : (N, 3) float64 ndarray, closed polygon (last point != first point;
 *           the code wraps i->i+1 modulo N automatically).
 *   Tangents are computed via central differences (no dt factor — cancels in
 *   both the normalised BS integral and the writhe).
 *
 * Physics
 * -------
 *   The SST Biot-Savart energy for a thin vortex filament of circulation Gamma
 *   in a superfluid-like substrate of density rho_f:
 *
 *     E_BS(a) = (rho_f * Gamma^2) / (4 pi) * I(K, a)
 *
 *   Asymptotic fit for small a:
 *     I(K, a) = A_K * L_K * ln(L_K / a) + B_K * L_K  + O(a^2/L_K^2)
 *
 *   Slender-body limit: A_K -> 1/(4pi) for any smooth closed curve.
 *   B_K encodes knot topology / geometry.
 *
 * Author: Omar Iskandarani / Claude (Anthropic), July 2026.
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <stdexcept>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

/* ── helper: central-difference tangents ─────────────────────────────── */
static void compute_tangents(
    const py::detail::unchecked_reference<double, 2>& r,
    ssize_t N,
    std::vector<double>& tx,
    std::vector<double>& ty,
    std::vector<double>& tz
) {
    tx.resize(N); ty.resize(N); tz.resize(N);
    for (ssize_t i = 0; i < N; ++i) {
        ssize_t ip = (i + 1) % N;
        ssize_t im = (i - 1 + N) % N;
        tx[i] = 0.5 * (r(ip, 0) - r(im, 0));
        ty[i] = 0.5 * (r(ip, 1) - r(im, 1));
        tz[i] = 0.5 * (r(ip, 2) - r(im, 2));
    }
}

/* ── Biot-Savart self-integral ────────────────────────────────────────── */
double biot_savart_integral(py::array_t<double> pts_arr, double a) {
    if (a <= 0.0)
        throw std::invalid_argument("tube radius a must be > 0");

    auto r = pts_arr.unchecked<2>();
    const ssize_t N = r.shape(0);
    if (N < 4)
        throw std::invalid_argument("need at least 4 points");

    std::vector<double> tx, ty, tz;
    compute_tangents(r, N, tx, ty, tz);

    const double a2 = a * a;
    double E = 0.0;

#ifdef _OPENMP
#pragma omp parallel for reduction(+:E) schedule(dynamic, 32)
#endif
    for (ssize_t i = 0; i < N; ++i) {
        const double xi = r(i, 0), yi = r(i, 1), zi = r(i, 2);
        const double txi = tx[i], tyi = ty[i], tzi = tz[i];
        for (ssize_t j = 0; j < N; ++j) {
            if (i == j) continue;
            const double ex = xi - r(j, 0);
            const double ey = yi - r(j, 1);
            const double ez = zi - r(j, 2);
            const double d2 = ex*ex + ey*ey + ez*ez + a2;   // regularised
            const double dot = txi*tx[j] + tyi*ty[j] + tzi*tz[j];
            E += dot / std::sqrt(d2);
        }
    }
    return E;  // = I(K, a); multiply by rho_f Gamma^2 / (4pi) for energy
}

/* ── Writhe (Gauss self-linking integral) ─────────────────────────────── */
double writhe(py::array_t<double> pts_arr) {
    auto r = pts_arr.unchecked<2>();
    const ssize_t N = r.shape(0);
    if (N < 4)
        throw std::invalid_argument("need at least 4 points");

    std::vector<double> tx, ty, tz;
    compute_tangents(r, N, tx, ty, tz);

    double W = 0.0;

#ifdef _OPENMP
#pragma omp parallel for reduction(+:W) schedule(dynamic, 32)
#endif
    for (ssize_t i = 0; i < N; ++i) {
        const double xi = r(i, 0), yi = r(i, 1), zi = r(i, 2);
        const double txi = tx[i], tyi = ty[i], tzi = tz[i];
        for (ssize_t j = 0; j < N; ++j) {
            if (i == j) continue;
            const double ex = xi - r(j, 0);
            const double ey = yi - r(j, 1);
            const double ez = zi - r(j, 2);
            // cross(T_i, T_j) . r_ij / |r_ij|^3
            const double cx = tyi*tz[j] - tzi*ty[j];
            const double cy = tzi*tx[j] - txi*tz[j];
            const double cz = txi*ty[j] - tyi*tx[j];
            const double num = ex*cx + ey*cy + ez*cz;
            const double d2  = ex*ex + ey*ey + ez*ez;
            if (d2 > 1e-30) {
                W += num / (d2 * std::sqrt(d2));
            }
        }
    }
    return W / (4.0 * M_PI);
}

/* ── pybind11 module ─────────────────────────────────────────────────── */
PYBIND11_MODULE(sst_bs_kernel, m) {
    m.doc() =
        "SST Biot-Savart vortex-filament kernel (C++/pybind11).\n\n"
        "Functions\n"
        "---------\n"
        "biot_savart_integral(pts, a) -> float\n"
        "    Rosenhead-regularised self-integral I(K, a).\n"
        "    E_BS = rho_f * Gamma^2 / (4*pi) * I(K, a).\n\n"
        "writhe(pts) -> float\n"
        "    Gauss self-linking (writhe) of a closed polygon.\n";

    m.def(
        "biot_savart_integral",
        &biot_savart_integral,
        py::arg("pts"),
        py::arg("a"),
        R"doc(
Rosenhead-regularised Biot-Savart self-integral.

  I(K, a) = sum_{i != j} (dl_i . dl_j) / sqrt(|r_i - r_j|^2 + a^2)

Parameters
----------
pts : (N, 3) float64 ndarray
    Closed-curve sample points (last != first; wraps automatically).
a   : float
    Rosenhead regularisation radius (= tube radius).

Returns
-------
float
    I(K, a).  Multiply by rho_f * Gamma^2 / (4*pi) for physical energy.

Asymptotic (small a):
    I(K, a) ~ A_K * L * ln(L/a) + B_K * L
    A_K -> 1/(4*pi) for any smooth closed filament (slender-body limit).
)doc"
    );

    m.def(
        "writhe",
        &writhe,
        py::arg("pts"),
        R"doc(
Writhe of a closed curve via the Gauss self-linking integral (O(N^2)).

  Wr = (1/4pi) sum_{i!=j} [ (r_ij x T_i) . T_j ] / |r_ij|^3

For the ideal trefoil the writhe is ≈ 3.0 (topological self-linking).
)doc"
    );

#ifdef _OPENMP
    m.attr("openmp") = true;
    m.attr("n_threads") = omp_get_max_threads();
#else
    m.attr("openmp") = false;
    m.attr("n_threads") = 1;
#endif
}
