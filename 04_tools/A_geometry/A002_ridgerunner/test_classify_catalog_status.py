#!/usr/bin/env python3
"""Unit tests for classify_catalog_status.py taxonomy gates."""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from classify_catalog_status import (
    CAMPAIGN_SOURCE,
    classify,
    is_stalled_polish,
    resolve_external_reference,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _polish_metrics(
    folder: Path,
    name: str,
    *,
    residual: float,
    ropelength: float,
    stop_reason: str | None = "residual",
    residual_converged: bool | None = True,
    thickness: float = 0.5,
    stop_residual: float | None = 0.005,
) -> Path:
    args = ["-c", "--EqOn", "-s", "30000"]
    if stop_residual is not None:
        args.append(f"--StopResidual={stop_residual}")
    met = {
        "residual": residual,
        "ropelength": ropelength,
        "thickness": thickness,
        "stop_reason": stop_reason,
        "residual_converged": residual_converged,
        "ridgerunner_args": args,
    }
    path = folder / name
    _write_json(path, met)
    return path


class TestStalledDetection(unittest.TestCase):
    def test_stop20_high_residual(self) -> None:
        self.assertTrue(
            is_stalled_polish(
                {
                    "stop_reason": "stop20",
                    "residual_converged": False,
                    "ridgerunner_args": ["--StopResidual=0.05"],
                },
                1.0,
            )
        )

    def test_not_stalled_when_candidate_residual(self) -> None:
        self.assertFalse(
            is_stalled_polish({"stop_reason": "stop20"}, 0.009)
        )


class TestReferenceSplit(unittest.TestCase):
    def test_external_gilbert(self) -> None:
        refs = {
            "knot_3.1": {
                "ropelength": 32.743274,
                "source": "Brian-Gilbert-3:1:1",
            }
        }
        r, src = resolve_external_reference("knot_3.1", refs)
        self.assertAlmostEqual(r or 0.0, 32.743274)
        self.assertEqual(src, "Brian-Gilbert-3:1:1")

    def test_no_campaign_fallback_as_external(self) -> None:
        r, src = resolve_external_reference("torus_2.9", {})
        self.assertIsNone(r)
        self.assertIsNone(src)


class TestClassifyTaxonomy(unittest.TestCase):
    def test_stalled_not_converged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "link_0.2.1"
            _write_json(
                folder / "seed_selection.json",
                {"topology_status": "topology-verified"},
            )
            _polish_metrics(
                folder,
                "x_rr_002k_coarse_rr_005k_eqfinal_rr_005k_polish.metrics.json",
                residual=1.0,
                ropelength=20.0,
                stop_reason="stop20",
                residual_converged=False,
                stop_residual=0.05,
            )
            result = classify(folder)
            self.assertEqual(result["status"], "stalled-not-converged")
            self.assertEqual(
                result["campaign_reference"]["source"], CAMPAIGN_SOURCE
            )
            self.assertIsNone(result["reference"])
            self.assertEqual(result["checks"]["ropelength_excess"], "not-tested")

    def test_tautology_blocked_for_near_ideal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "torus_2.9"
            _write_json(
                folder / "seed_selection.json",
                {"topology_status": "topology-verified"},
            )
            _polish_metrics(
                folder,
                "t_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.metrics.json",
                residual=0.0045,
                ropelength=80.5,
            )
            result = classify(folder)
            self.assertEqual(result["status"], "converged-local-candidate")
            self.assertEqual(result["checks"]["ropelength_excess"], "not-tested")
            self.assertFalse(result["strict_near_ideal"])

    def test_mirror_disagreement_blocks_near_ideal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, rop, res in (
                ("knot_5.1", 47.384097, 0.048),
                ("torus_2.5", 48.218362, 0.004961),
            ):
                folder = root / name
                _write_json(
                    folder / "seed_selection.json",
                    {"topology_status": "topology-verified"},
                )
                _polish_metrics(
                    folder,
                    f"{name}_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.metrics.json",
                    residual=res,
                    ropelength=rop,
                    residual_converged=res <= 0.005,
                    stop_reason="residual" if res <= 0.005 else "stop20",
                    stop_residual=0.005,
                )
            result = classify(root / "torus_2.5")
            self.assertEqual(result["status"], "converged-local-candidate")
            self.assertEqual(result["checks"]["multistart_spread"], "fail")

    def test_analytic_unknot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_0.1"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "knot_0.1_analytic_D1.txt").write_text(
                "1 0 0\n0 1 0\n-1 0 0\n0 -1 0\n",
                encoding="utf-8",
            )
            _write_json(
                folder / "seed_selection.json",
                {"topology_status": "topology-verified"},
            )
            # Stale RR polish must not become baseline.
            _polish_metrics(
                folder,
                "knot_0.1_trial_015k_rr_010k_coarse_rr_050k_eqfinal_rr_020k_polish.metrics.json",
                residual=0.997,
                ropelength=6.31,
                stop_reason="stop20",
                residual_converged=False,
            )
            result = classify(folder)
            self.assertEqual(result["status"], "near-ideal")
            self.assertTrue(result["primary_metrics"]["analytic"])
            self.assertAlmostEqual(
                float(result["primary_metrics"]["ropelength"]),
                2.0 * math.pi,
                places=6,
            )
            self.assertEqual(result["reference"]["source"], "analytic-circle")

    def test_chirality_aliases_from_dowker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_3.1"
            _write_json(
                folder / "seed_selection.json",
                {
                    "topology_status": "topology-verified",
                    "dowker_code": "4 6 2",
                },
            )
            _polish_metrics(
                folder,
                "k_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.metrics.json",
                residual=0.009,
                ropelength=32.75,
            )
            result = classify(folder)
            self.assertEqual(result["chirality"], "R")
            self.assertIn("3_1_R", result["catalog_aliases"] or [])


if __name__ == "__main__":
    unittest.main()
