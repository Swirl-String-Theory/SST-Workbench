from __future__ import annotations

import math

from sst_horn_torus_chiE import (
    HornTorusParams,
    chi_from_xi,
    evaluate_horn_torus,
    p_vac_from_variational_a0,
    scan_lambda,
    v0_from_gamma_a0,
    xi_cavitation,
    xi_regularized_circular_filament,
)


def approx_equal(a: float, b: float, rel: float = 1e-12, abs_: float = 0.0) -> bool:
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b), 1.0))


def assert_raises(fn, exc_type=ValueError):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


def test_v0_from_gamma_a0():
    Gamma0 = 2.0 * math.pi * 3.0 * 5.0
    assert approx_equal(v0_from_gamma_a0(Gamma0, 3.0), 5.0)


def test_pvac_variational_roundtrip():
    rho = 7.0
    Gamma0 = 11.0
    a0 = 2.0
    P = p_vac_from_variational_a0(rho, Gamma0, a0)
    a_back = Gamma0 / (2.0 * math.pi) * math.sqrt(rho / (2.0 * P))
    assert approx_equal(a_back, a0, rel=1e-14)


def test_xi_cavitation_chi_conversion():
    assert approx_equal(xi_cavitation(1.0), 0.25)
    assert approx_equal(chi_from_xi(xi_cavitation(1.0)), math.pi**2)


def test_lambda_below_horn_rejected():
    assert_raises(lambda: xi_cavitation(0.999), ValueError)


def test_quadrature_convergence_regularized():
    x1 = xi_regularized_circular_filament(1.0, epsilon=1.0, quadrature_n=4096)
    x2 = xi_regularized_circular_filament(1.0, epsilon=1.0, quadrature_n=8192)
    assert abs(x2 - x1) / max(1.0, abs(x2)) < 1e-10


def test_hollow_total_not_false_match_to_2pi_at_horn_regularized():
    r = evaluate_horn_torus(HornTorusParams(lambda_=1.0, epsilon=1.0, quadrature_n=4096))
    assert abs(r.chi_E_hollow - 2.0 * math.pi) / (2.0 * math.pi) > 1e-2


def test_scan_lambda_count():
    rows = scan_lambda(1.0, 2.0, 5, HornTorusParams(quadrature_n=1024))
    assert len(rows) == 5


def run_all():
    tests = [
        test_v0_from_gamma_a0,
        test_pvac_variational_roundtrip,
        test_xi_cavitation_chi_conversion,
        test_lambda_below_horn_rejected,
        test_quadrature_convergence_regularized,
        test_hollow_total_not_false_match_to_2pi_at_horn_regularized,
        test_scan_lambda_count,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("[PASS] all horn-torus chiE tests completed")


if __name__ == "__main__":
    run_all()
