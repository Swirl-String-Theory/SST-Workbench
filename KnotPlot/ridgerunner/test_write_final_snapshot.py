#!/usr/bin/env python3
"""Unit tests for write_final_snapshot and run_finalize_knotplot."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from run_finalize_knotplot import finalize_one, main as finalize_main
from write_final_snapshot import (
    campaign_root_from_path,
    final_basename,
    pick_best_across_campaign,
    unique_path,
    write_final_snapshot,
)


def _write_polish(folder: Path, name: str, rop: float) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    txt = folder / name
    txt.write_text(f"# polish {name}\n0 0 0\n", encoding="utf-8")
    met = Path(str(txt).removesuffix(".txt") + ".metrics.json")
    met.write_text(
        json.dumps({"ropelength": rop, "residual": 0.01}) + "\n",
        encoding="utf-8",
    )
    return txt


class TestFinalBasename(unittest.TestCase):
    def test_with_suffix(self) -> None:
        when = datetime(2026, 8, 12, 21, 45, 30)
        name = final_basename("build_knot_3.1", "min", suffix="scout", when=when)
        self.assertEqual(name, "build_knot_3.1_final_min_scout_20260812_214530")

    def test_unique_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            p1 = unique_path(d, "a_final_min_20260812_214530")
            p1.write_text("x", encoding="utf-8")
            p2 = unique_path(d, "a_final_min_20260812_214530")
            self.assertTrue(p2.name.endswith("_2.txt"))


class TestWriteFinalSnapshot(unittest.TestCase):
    def test_copy_next_to_kpc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_3.1"
            polish = _write_polish(
                folder, "seed_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt", 16.4
            )
            (folder / "build_knot_3.1.kpc").write_text("% build\n", encoding="utf-8")
            when = datetime(2026, 8, 12, 10, 0, 0)
            written = write_final_snapshot(
                polish,
                stem="build_knot_3.1",
                tag="min",
                dest=folder,
                when=when,
            )
            self.assertTrue(written["txt"].is_file())
            self.assertEqual(
                written["txt"].name,
                "build_knot_3.1_final_min_20260812_100000.txt",
            )
            self.assertEqual(written["txt"].parent, folder)
            self.assertIn("metrics", written)
            alias = json.loads(written["alias"].read_text(encoding="utf-8"))
            self.assertEqual(alias["polish_path"], str(polish.resolve()))


class TestBestAcrossTN(unittest.TestCase):
    def test_picks_lower_rop_into_campaign_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "3_1"
            t10 = root / "t10"
            t12 = root / "t12"
            _write_polish(t10, "n900p.txt", 17.0)
            best = _write_polish(t12, "n900p.txt", 16.1)
            polish, dest, rop, info = pick_best_across_campaign(t10)
            self.assertEqual(polish.resolve(), best.resolve())
            self.assertEqual(dest.resolve(), root.resolve())
            self.assertAlmostEqual(rop or 0.0, 16.1)
            self.assertEqual(campaign_root_from_path(t12), root.resolve())
            when = datetime(2026, 1, 2, 3, 4, 5)
            written = write_final_snapshot(
                polish, stem="3_1", tag="N900", dest=dest, when=when
            )
            self.assertEqual(written["txt"].parent.resolve(), root.resolve())
            self.assertTrue(written["txt"].name.startswith("3_1_final_N900_"))


class TestFinalizeKnotplot(unittest.TestCase):
    def test_finalize_one_writes_beside_kpc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_3.1"
            _write_polish(
                folder,
                "knot_3.1_trial_002k_rr_010k_coarse_rr_050k_eqfinal_rr_020k_polish.txt",
                16.5,
            )
            (folder / "build_knot_3.1.kpc").write_text("%x\n", encoding="utf-8")
            row = finalize_one(
                folder,
                tag="finalize",
                suffix="backlog",
                dry_run=False,
                catalog_upsert=False,
            )
            self.assertEqual(row["status"], "ok")
            self.assertTrue(Path(row["final_txt"]).is_file())
            self.assertTrue(
                Path(row["final_txt"]).name.startswith(
                    "build_knot_3.1_final_finalize_backlog_"
                )
            )

    def test_skip_no_polish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knot_9.2"
            folder.mkdir()
            (folder / "build_knot_9.2.kpc").write_text("%x\n", encoding="utf-8")
            row = finalize_one(
                folder, tag="finalize", suffix=None, dry_run=False, catalog_upsert=False
            )
            self.assertEqual(row["status"], "skipped")
            self.assertEqual(row["reason"], "no polish")

    def test_dry_run_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "knot_3.1"
            _write_polish(
                folder,
                "x_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt",
                16.0,
            )
            (folder / "build_knot_3.1.kpc").write_text("%x\n", encoding="utf-8")
            summary = root / "sum.json"
            rc = finalize_main(
                [
                    "--knots-root",
                    str(root),
                    "--ids",
                    "knot_3.1",
                    "--dry-run",
                    "--summary",
                    str(summary),
                ]
            )
            self.assertEqual(rc, 0)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "dry-run")
            self.assertEqual(payload["results"][0]["status"], "dry-run")


if __name__ == "__main__":
    unittest.main()
