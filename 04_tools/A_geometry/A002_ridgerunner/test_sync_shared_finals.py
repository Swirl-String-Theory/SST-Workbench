#!/usr/bin/env python3
"""Tests for shared knots/final mirror and sync_shared_finals."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from sync_shared_finals import (
    list_historical_finals,
    pick_best_final_in_folder,
    sync_shared_finals,
)
from write_final_snapshot import (
    is_knots_catalog_dest,
    mirror_final_to_shared,
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


class TestIsKnotsCatalogDest(unittest.TestCase):
    def test_under_knots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "knots" / "knot_3.1"
            folder.mkdir(parents=True)
            self.assertTrue(is_knots_catalog_dest(folder))

    def test_campaign_out_not_mirrored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "out" / "3_1"
            folder.mkdir(parents=True)
            self.assertFalse(is_knots_catalog_dest(folder))


class TestMirrorShared(unittest.TestCase):
    def test_write_snapshot_mirrors_under_knots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            knots = Path(tmp) / "knots"
            folder = knots / "knot_3.1"
            polish = _write_polish(
                folder,
                "seed_rr_010k_coarse_rr_050k_eqfinal_rr_030k_polish.txt",
                16.4,
            )
            (folder / "build_knot_3.1.kpc").write_text("%x\n", encoding="utf-8")
            when = datetime(2026, 8, 13, 12, 0, 0)
            written = write_final_snapshot(
                polish,
                stem="build_knot_3.1",
                tag="min",
                dest=folder,
                when=when,
                shared_dir=knots / "final",
            )
            self.assertIn("shared_txt", written)
            shared = written["shared_txt"]
            self.assertEqual(shared.name, "knot_3.1_final.txt")
            self.assertEqual(shared.parent, (knots / "final").resolve())
            self.assertEqual(
                shared.read_text(encoding="utf-8"),
                written["txt"].read_text(encoding="utf-8"),
            )
            alias = json.loads(written["shared_alias"].read_text(encoding="utf-8"))
            self.assertEqual(alias["build_id"], "knot_3.1")
            self.assertEqual(Path(alias["source_final"]).resolve(), written["txt"].resolve())

    def test_mirror_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shared = Path(tmp) / "final"
            folder = Path(tmp) / "knots" / "knot_4.1"
            p1 = _write_polish(folder, "a_polish.txt", 18.0)
            f1 = write_final_snapshot(
                p1,
                stem="build_knot_4.1",
                tag="a",
                dest=folder,
                when=datetime(2026, 1, 1, 0, 0, 0),
                shared_dir=shared,
            )
            p2 = _write_polish(folder, "b_polish.txt", 16.0)
            f2 = write_final_snapshot(
                p2,
                stem="build_knot_4.1",
                tag="b",
                dest=folder,
                when=datetime(2026, 1, 2, 0, 0, 0),
                shared_dir=shared,
            )
            self.assertEqual(f1["shared_txt"], f2["shared_txt"])
            self.assertEqual(
                f2["shared_txt"].read_text(encoding="utf-8"),
                f2["txt"].read_text(encoding="utf-8"),
            )

    def test_no_mirror_outside_knots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            campaign = Path(tmp) / "out" / "3_1"
            polish = _write_polish(campaign, "n900p.txt", 16.2)
            written = write_final_snapshot(
                polish,
                stem="3_1",
                tag="N900",
                dest=campaign,
                when=datetime(2026, 1, 1, 0, 0, 0),
            )
            self.assertNotIn("shared_txt", written)


class TestSyncSharedFinals(unittest.TestCase):
    def test_picks_lower_rop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            knots = Path(tmp) / "knots"
            folder = knots / "knot_3.1"
            folder.mkdir(parents=True)
            (folder / "build_knot_3.1.kpc").write_text("%x\n", encoding="utf-8")
            # Two historical finals with different Rop
            worse = folder / "build_knot_3.1_final_min_20260101_000000.txt"
            worse.write_text("worse\n", encoding="utf-8")
            Path(str(worse).removesuffix(".txt") + ".metrics.json").write_text(
                json.dumps({"ropelength": 17.0}) + "\n", encoding="utf-8"
            )
            better = folder / "build_knot_3.1_final_min_20260102_000000.txt"
            better.write_text("better\n", encoding="utf-8")
            Path(str(better).removesuffix(".txt") + ".metrics.json").write_text(
                json.dumps({"ropelength": 16.1}) + "\n", encoding="utf-8"
            )
            picked, rop, info = pick_best_final_in_folder(folder)
            self.assertEqual(picked.resolve(), better.resolve())
            self.assertAlmostEqual(rop or 0.0, 16.1)
            self.assertEqual(info["pick"], "lowest_rop")

            shared = knots / "final"
            result = sync_shared_finals(
                knots_root=knots,
                shared_dir=shared,
                ids=["knot_3.1"],
            )
            self.assertEqual(result["failures"], 0)
            out = shared / "knot_3.1_final.txt"
            self.assertTrue(out.is_file())
            self.assertEqual(out.read_text(encoding="utf-8"), "better\n")

    def test_list_skips_uniform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "build_x_final_min_20260101_000000.txt").write_text(
                "ok\n", encoding="utf-8"
            )
            (folder / "build_x_final_min_20260101_000000_uniform_N300.txt").write_text(
                "no\n", encoding="utf-8"
            )
            finals = list_historical_finals(folder)
            self.assertEqual(len(finals), 1)
            self.assertTrue(finals[0].name.endswith("000000.txt"))


class TestMirrorDirect(unittest.TestCase):
    def test_mirror_final_to_shared_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            final = src / "build_knot_5.1_final_min_20260101_000000.txt"
            final.write_text("geom\n", encoding="utf-8")
            Path(str(final).removesuffix(".txt") + ".metrics.json").write_text(
                json.dumps({"ropelength": 20.0}) + "\n", encoding="utf-8"
            )
            Path(str(final).removesuffix(".txt") + ".alias.json").write_text(
                json.dumps({"polish_path": "x"}) + "\n", encoding="utf-8"
            )
            shared = Path(tmp) / "final"
            written = mirror_final_to_shared(final, build_id="knot_5.1", shared_dir=shared)
            self.assertEqual(written["txt"].name, "knot_5.1_final.txt")
            self.assertTrue(written["metrics"].is_file())


if __name__ == "__main__":
    unittest.main()
