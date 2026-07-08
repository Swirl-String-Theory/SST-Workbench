from __future__ import annotations

import math

from sst_solid_core_chiE import (
    TARGET_CHI_E,
    SolidCoreParams,
    alpha_required_for_target,
    chi_from_xi,
    evaluate_solid_core,
    scan_alpha,
    scan_lambda,
    xi_internal_rankine,
    xi_total_solid_thin_ring,
)


def approx_equal(a: float, b: float, rel: float = 1e-12, abs_: float = 0.0) -> bool:
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b), 1.0))


def assert_raises(fn, exc_type=ValueError):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


def test_rankine_internal_core():
    assert approx_equal(xi_internal_rankine(1.0), 0.125)
    assert approx_equal(chi_from_xi(xi_internal_rankine(1.0)), math.pi * math.pi / 2.0)


def test_solid_constant_volume_horn_value():
    r = evaluate_solid_core(SolidCoreParams(lambda_=1.0, alpha_E=1.75))
    expected_xi = 0.5 * (math.log(8.0) - 1.75)
    assert approx_equal(r.Xi_total, expected_xi)
    assert r.chi_E > TARGET_CHI_E
    assert abs(r.target_residual) < 0.05


def test_alpha_required_roundtrip():
    alpha_req = alpha_required_for_target(1.0)
    r = evaluate_solid_core(SolidCoreParams(lambda_=1.0, alpha_E=alpha_req))
    assert approx_equal(r.chi_E, TARGET_CHI_E, rel=1e-12)


def test_lambda_guard():
    assert_raises(lambda: xi_internal_rankine(0.999), ValueError)
    assert_raises(lambda: xi_total_solid_thin_ring(0.999), ValueError)


def test_scans():
    rows = scan_lambda(1.0, 2.0, 5, SolidCoreParams(alpha_E=1.75))
    assert len(rows) == 5
    alphas = scan_alpha(1.5, 2.0, 6, SolidCoreParams(lambda_=1.0))
    assert len(alphas) == 6


def run_all():
    tests = [
        test_rankine_internal_core,
        test_solid_constant_volume_horn_value,
        test_alpha_required_roundtrip,
        test_lambda_guard,
        test_scans,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("[PASS] all solid-core constant-density tests completed")


if __name__ == "__main__":
    run_all()
