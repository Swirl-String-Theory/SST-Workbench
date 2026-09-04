#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>
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
    const sst_fermat::Vec3 probe{0.17,-0.11,0.43};
    const auto value = sst_fermat::biot_savart_point_with_jacobian(
        ring, probe, beta0/2.0, 0.01);
    assert(std::isfinite(value.beta.z));

    const double h = 1e-6;
    for (int j = 0; j < 3; ++j) {
        auto pp = probe;
        auto pm = probe;
        if (j == 0) { pp.x += h; pm.x -= h; }
        if (j == 1) { pp.y += h; pm.y -= h; }
        if (j == 2) { pp.z += h; pm.z -= h; }
        const auto vp = sst_fermat::biot_savart_point_with_jacobian(ring, pp, beta0/2.0, 0.01).beta;
        const auto vm = sst_fermat::biot_savart_point_with_jacobian(ring, pm, beta0/2.0, 0.01).beta;
        const double fd[3] = {(vp.x-vm.x)/(2*h), (vp.y-vm.y)/(2*h), (vp.z-vm.z)/(2*h)};
        for (int i = 0; i < 3; ++i) {
            const double analytic = value.jacobian[static_cast<std::size_t>(i*3+j)];
            assert(std::abs(fd[i]-analytic) < 1e-8);
        }
    }
    std::cout << "PASS residual=" << residual
              << " K_hat=" << sst_fermat::k_hat(p, xstar)
              << " jacobian_checked=1\n";
    return 0;
}
