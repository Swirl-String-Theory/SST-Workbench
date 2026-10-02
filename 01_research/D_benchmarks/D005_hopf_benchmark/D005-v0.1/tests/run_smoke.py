#!/usr/bin/env python3
"""Low-resolution execution smoke test for all eight scripts."""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(args: list[str]) -> None:
    command = [PYTHON, *args]
    print("+", " ".join(str(x) for x in command))
    completed = subprocess.run(command, cwd=ROOT, text=True)
    if completed.returncode != 0:
        raise SystemExit(f"Command failed with exit code {completed.returncode}: {command}")


def assert_json(path: Path) -> None:
    with path.open(encoding="utf-8") as handle:
        json.load(handle)


def main() -> int:
    temp = Path(tempfile.mkdtemp(prefix="sst_hopf_smoke_"))
    try:
        step1 = temp / "step01"
        step2 = temp / "step02"
        step3 = temp / "step03"
        step4 = temp / "step04"
        step5 = temp / "step05"
        step6 = temp / "step06"
        step7 = temp / "step07"
        step8 = temp / "step08"

        run(["01_definieer_sst_orderparameter.py", "--n", "24", "--extent", "8", "--output", str(step1)])
        run(["02_analytische_hopf_benchmark.py", "--resolutions", "32", "48", "64", "--fiber-samples", "200", "--output", str(step2)])
        run(["03_toroflux_spinorveld.py", "--n-grid", "32", "--output", str(step3)])
        run(["04_hopf_lading_numeriek.py", str(step2 / "analytic_hopf_benchmark.npz"), "--output", str(step4)])
        run(["05_heliciteitsbridge.py", str(step2 / "analytic_hopf_benchmark.npz"), "--output", str(step5)])
        run(["06_effectieve_spinactie.py", "--samples", "200", "--output", str(step6)])
        run(["07_vier_pi_configuratieruimte.py", "--samples", "201", "--output", str(step7)])
        run(["08_trefoil_integratie.py", "--samples", "160", "--radial-samples", "5", "--angular-samples", "12", "--output", str(step8)])

        expected_json = [
            step1 / "H4_evidence.json",
            step2 / "H0_H3_evidence.json",
            step3 / "H4_toroflux_evidence.json",
            step4 / "H1_H3_evidence.json",
            step5 / "H5_evidence.json",
            step6 / "H6_H8_evidence.json",
            step7 / "H9_evidence.json",
            step8 / "H10_evidence.json",
        ]
        for path in expected_json:
            if not path.is_file():
                raise SystemExit(f"Missing expected output: {path}")
            assert_json(path)
        print(f"SMOKE PASS: {len(expected_json)} evidence files validated")
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
