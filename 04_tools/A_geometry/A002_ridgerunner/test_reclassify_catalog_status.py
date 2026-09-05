#!/usr/bin/env python3
"""Tests for reclassify_catalog_status + versioned log naming in run_build.cmd."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reclassify_catalog_status import main as reclassify_main


class TestReclassifyCli(unittest.TestCase):
    def test_reclassify_writes_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "link_0.2.1"
            folder.mkdir()
            (folder / "build_link_0.2.1.kpc").write_text("% stub\n", encoding="utf-8")
            (folder / "seed_selection.json").write_text(
                json.dumps({"topology_status": "topology-verified"}) + "\n",
                encoding="utf-8",
            )
            (folder / "x_rr_002k_coarse_rr_005k_eqfinal_rr_005k_polish.metrics.json").write_text(
                json.dumps(
                    {
                        "residual": 1.0,
                        "ropelength": 12.0,
                        "thickness": 0.5,
                        "stop_reason": "stop20",
                        "residual_converged": False,
                        "ridgerunner_args": ["--StopResidual=0.05"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary = root / "sum.json"
            rc = reclassify_main(
                [
                    "--knots-root",
                    str(root),
                    "--ids",
                    "link_0.2.1",
                    "--summary",
                    str(summary),
                ]
            )
            self.assertEqual(rc, 0)
            status = json.loads(
                (folder / "catalog_status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["status"], "stalled-not-converged")
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["results"][0]["status"], "stalled-not-converged")


class TestRunBuildLogVersioning(unittest.TestCase):
    def test_run_build_cmd_has_versioned_log(self) -> None:
        cmd = Path(__file__).resolve().parents[1] / "run_build.cmd"
        text = cmd.read_text(encoding="utf-8")
        self.assertIn("build_knotplot_!LOG_TS!.log", text)
        self.assertIn('copy /Y "!LOG_VERSIONED!" "!LOG!"', text)


if __name__ == "__main__":
    unittest.main()
