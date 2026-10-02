#include <cassert>
#include <cmath>
#include <iostream>
#include "../cpp/fermat_kernel.hpp"

int main() {
    constexpr double c = 299792458.0;
    constexpr double v = 1.09384563e6;
    const double beta0 = v/c;
    const double xstar = std::sqrt(2.0)*beta0;
    const auto p = sst_fermat::external_profile(xstar, beta0);
    const double residual = sst_fermat::fermat_residual(p, xstar);
    assert(std::abs(residual) < 1e-12);
    assert(std::abs(p.beta - 1.0/std::sqrt(2.0)) < 1e-12);
    assert(sst_fermat::k_hat(p, xstar) < 0.0);

    std::vector<sst_fermat::Vec3> ring = {{1,0,0},{0,1,0},{-1,0,0},{0,-1,0}};
    std::vector<sst_fermat::Vec3> probes = {{0,0,0.5}};
    const auto u = sst_fermat::biot_savart_batch(ring, probes, beta0/2.0, 0.01);
    assert(u.size() == 1);
    assert(std::isfinite(u[0].z));
    std::cout << "PASS residual=" << residual << " K_hat=" << sst_fermat::k_hat(p, xstar) << "\n";
    return 0;
}
