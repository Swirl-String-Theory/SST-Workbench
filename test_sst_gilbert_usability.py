#!/usr/bin/env python3
"""Tests for sst_gilbert_usability thickness-partition C_cont gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_gilbert_usability import (  # noqa: E402
    DEFAULT_MIN_C_CONT,
    CurvatureOnlyIdealError,
    c_cont,
    i_kappa2,
    is_usable_ideal,
    kappa_hat_max,
    require_usable_ideal,
    usability_from_coeffs,
    usability_report,
)

RR = ROOT / "KnotPlot" / "ridgerunner"
if str(RR) not in sys.path:
    sys.path.insert(0, str(RR))

from gilbert_ab_to_xyz import parse_ideal_ab_block  # noqa: E402

IDEAL = ROOT / "knots_ideal_favorites.txt"


class TestGilbertUsability(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IDEAL.is_file():
            raise unittest.SkipTest(f"missing ideal DB: {IDEAL}")
        cls.text = IDEAL.read_text(encoding="utf-8", errors="replace")

    def test_circle_0_1_1_c_cont_near_zero(self) -> None:
        coeffs, attrs = parse_ideal_ab_block(self.text, "0:1:1")
        D = float(attrs.get("D", "1").strip())
        pts, report = usability_from_coeffs(coeffs, D=D, samples=256)
        self.assertLessEqual(float(report["C_cont"]), 0.05)
        self.assertFalse(bool(report["usable"]))
        # Geometric tube diameter 2/κ gives I_κ²/L_D ≈ 4 for the unit circle.
        kappa_max = float(report["kappa_hat_max"]) / D
        D_geom = 2.0 / kappa_max
        L = float(report["L"])
        # Recompute I with geometric D on analytic samples.
        pts2, report2 = usability_from_coeffs(coeffs, D=D_geom, samples=256)
        ratio = float(report2["I_kappa2"]) / (L / D_geom)
        self.assertAlmostEqual(ratio, 4.0, delta=0.05)

    def test_trefoil_3_1_1_usable(self) -> None:
        coeffs, attrs = parse_ideal_ab_block(self.text, "3:1:1")
        D = float(attrs.get("D", "1").strip())
        _pts, report = usability_from_coeffs(coeffs, D=D, samples=512)
        self.assertGreater(float(report["C_cont"]), DEFAULT_MIN_C_CONT)
        self.assertTrue(bool(report["usable"]))
        self.assertGreater(float(report["C_cont"]), 0.5)
        # Fourier seed can slightly exceed κ̂=2; contact score is the gate.

    def test_require_usable_raises_on_circle(self) -> None:
        coeffs, attrs = parse_ideal_ab_block(self.text, "0:1:1")
        D = float(attrs.get("D", "1").strip())
        pts, kappa = __import__(
            "sst_gilbert_usability", fromlist=["fourier_sample_with_kappa"]
        ).fourier_sample_with_kappa(coeffs, 256)
        with self.assertRaises(CurvatureOnlyIdealError):
            require_usable_ideal(pts, D=D, knot_id="0:1:1", kappa=kappa)
        ok = require_usable_ideal(
            pts, D=D, knot_id="0:1:1", allow_curvature_only=True, kappa=kappa
        )
        self.assertFalse(ok["usable"])

    def test_kappa_hat_max_positive(self) -> None:
        coeffs, _ = parse_ideal_ab_block(self.text, "3:1:1")
        _pts, report = usability_from_coeffs(coeffs, D=1.0, samples=128)
        self.assertGreater(float(report["kappa_hat_max"]), 0.0)
        self.assertGreater(kappa_hat_max(_pts, D=1.0), 0.0)


if __name__ == "__main__":
    unittest.main()
