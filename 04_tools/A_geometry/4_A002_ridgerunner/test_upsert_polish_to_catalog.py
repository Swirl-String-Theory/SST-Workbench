#!/usr/bin/env python3
"""Tests for upsert_polish_to_catalog (uniform-of-final-polish → JS)."""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from upsert_polish_to_catalog import (
    find_latest_final_for_polish,
    prefer_polish_in_catalog_status,
    resample_polish_uniform,
    try_upsert_polish_to_catalog,
    uniform_path_for_polish,
    upsert_polish_to_catalog,
)
from write_final_snapshot import write_final_snapshot


def _circle_xyz(n: int = 48, radius: float = 1.0) -> str:
    lines = ["# circle polish"]
    for i in range(n):
        ang = 2.0 * math.pi * i / n
        lines.append(f"{radius * math.cos(ang):.12g} {radius * math.sin(ang):.12g} 0")
    return "\n".join(lines) + "\n"


def _write_circle_polish(folder: Path, name: str, rop: float = 16.4) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    txt = folder / name
    txt.write_text(_circle_xyz(), encoding="utf-8")
    met = Path(str(txt).removesuffix(".txt") + ".metrics.json")
    met.write_text(
        json.dumps(
            {
                "ropelength": rop,
                "residual": 0.008,
                "thickness": 0.5,
                "length": 8.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return txt


class TestResampleUniform(unittest.TestCase):
    def test_uniform_naming_and_point_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            polish = _write_circle_polish(
                folder, "seed_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt"
            )
            uni = resample_polish_uniform(polish, points=300, method="linear")
            self.assertEqual(uni, uniform_path_for_polish(polish, points=300))
            self.assertTrue(uni.is_file())
            pts = [
                ln
                for ln in uni.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
            self.assertEqual(len(pts), 300)


class TestPreferPolishAndFinal(unittest.TestCase):
    def test_prefer_and_find_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_3.1"
            polish = _write_circle_polish(
                folder, "a_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt"
            )
            written = write_final_snapshot(
                polish, stem="build_knot_3.1", tag="min", dest=folder
            )
            status = prefer_polish_in_catalog_status(
                folder, polish, final_txt=written["txt"]
            )
            self.assertIn("primary_polish", status)
            self.assertEqual(
                Path(status["final_snapshot"]).resolve(), written["txt"].resolve()
            )
            found = find_latest_final_for_polish(folder, polish)
            self.assertEqual(found.resolve(), written["txt"].resolve())


class TestUpsertPath(unittest.TestCase):
    def test_upsert_calls_build_with_preferred_polish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_3.1"
            polish = _write_circle_polish(
                folder, "b_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt"
            )
            final = write_final_snapshot(
                polish, stem="build_knot_3.1", tag="finalize", dest=folder
            )["txt"]
            js_out = Path(tmp) / "knotplot_knots_data.js"

            with mock.patch(
                "upsert_polish_to_catalog.classify_outdir",
                return_value={"status": "near-ideal-candidate"},
            ), mock.patch(
                "upsert_polish_to_catalog.upsert_js_from_outdir", return_value=0
            ) as upsert_js:
                result = upsert_polish_to_catalog(
                    polish,
                    folder,
                    final_txt=final,
                    js_output=js_out,
                    skip_classify=False,
                )
            self.assertTrue(Path(result["uniform"]).is_file())
            upsert_js.assert_called_once()
            status = json.loads(
                (folder / "catalog_status.json").read_text(encoding="utf-8")
            )
            self.assertTrue(
                Path(status["primary_polish"]).name.startswith(
                    "b_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish"
                )
            )
            self.assertEqual(Path(status["final_snapshot"]).resolve(), final.resolve())

    def test_try_upsert_warns_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            polish = folder / "missing_polish.txt"
            out = try_upsert_polish_to_catalog(polish, folder)
            self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
