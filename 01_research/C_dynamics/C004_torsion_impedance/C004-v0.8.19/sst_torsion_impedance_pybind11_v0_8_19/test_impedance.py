#!/usr/bin/env python3
from __future__ import annotations

import math
import numpy as np

try:
    from sst_torsion_impedance_build import import_module as _import_sti
    sti = _import_sti(auto_build=True)
except Exception as exc:
    raise SystemExit(
        f"pybind11 extension could not be built/imported: {exc}\n"
        "Install pybind11 with `python -m pip install pybind11` or place "
        "pybind11_headers.zip next to sst_torsion_impedance_build.py."
    )


def test_trefoil_raw_medium_not_matched():
    opt = sti.canonical_medium_options()
    out = sti.audit_trefoil(1024, opt)
    chi = out["chi_T"]
    assert math.isfinite(chi)
    assert chi > 0.0
    assert chi < 1.0e-10


def test_fd_tensor_matches_quadrature():
    opt = sti.canonical_medium_options()
    out = sti.audit_trefoil(512, opt)
    assert out["fd_max_abs_error_kg"] < 1.0e-60


def test_density_scaling_is_linear():
    med = sti.canonical_medium_options()
    core = sti.canonical_core_density_options()
    a = sti.audit_figure_eight(512, med)["chi_T"]
    b = sti.audit_figure_eight(512, core)["chi_T"]
    expected = sti.RHO_CORE / sti.RHO_F
    assert np.isclose(b / a, expected, rtol=1.0e-12)


if __name__ == "__main__":
    test_trefoil_raw_medium_not_matched()
    test_fd_tensor_matches_quadrature()
    test_density_scaling_is_linear()
    print("PASS: sst_torsion_impedance pybind11 tests")
