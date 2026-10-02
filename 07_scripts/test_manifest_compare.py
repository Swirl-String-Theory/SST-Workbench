"""Unit tests for SP10 manifest comparison harness."""
from __future__ import annotations

import json
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import manifest_compare as mc  # noqa: E402


def test_ignores_timestamps_and_paths_but_catches_quantity_drift(tmp_path: Path):
    left = {
        "timestamp": "2026-01-01T00:00:00Z",
        "cwd": r"C:\old\SST_Pack_v0.1.0",
        "gate": "PASS",
        "energy": 1.2345,
        "topology": {"crossing_number": 3},
    }
    right = {
        "timestamp": "2026-09-05T12:00:00Z",
        "cwd": r"C:\workspace\projects\SST-Workbench\01_research\A_x\A001-v0.1.0",
        "gate": "PASS",
        "energy": 1.2345,
        "topology": {"crossing_number": 3},
    }
    assert mc.compare_quantities(mc.extract_quantities(left), mc.extract_quantities(right)) == []

    right_bad = dict(right)
    right_bad["energy"] = 9.999
    diffs = mc.compare_quantities(mc.extract_quantities(left), mc.extract_quantities(right_bad))
    assert diffs and any("energy" in d for d in diffs)


def test_compare_manifest_files_roundtrip(tmp_path: Path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    payload = {"run_id": "abc", "path": "/tmp/x", "n_links": 2, "score": 0.5}
    a.write_text(json.dumps(payload), encoding="utf-8")
    payload2 = dict(payload)
    payload2["run_id"] = "zzz"
    payload2["path"] = "D:/elsewhere"
    b.write_text(json.dumps(payload2), encoding="utf-8")
    assert mc.compare_manifest_files(a, b) == []

    payload2["n_links"] = 7
    b.write_text(json.dumps(payload2), encoding="utf-8")
    assert mc.compare_manifest_files(a, b)


def test_integer_exact_float_tolerance():
    left = {"n": 3, "x": 1.0}
    right = {"n": 3, "x": 1.0 + 1e-12}
    assert mc.compare_quantities(
        mc.extract_quantities(left), mc.extract_quantities(right), rtol=1e-9, atol=0.0,
    ) == []
    right["n"] = 4
    assert mc.compare_quantities(mc.extract_quantities(left), mc.extract_quantities(right))
