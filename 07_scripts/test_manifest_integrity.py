"""Validate checksums.sha256 covers every tracked file in file_manifest.csv."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
MANIFEST = WB / "10_docs" / "migration" / "file_manifest.csv"
CHECKSUMS = WB / "10_docs" / "migration" / "checksums.sha256"


def test_manifest_integrity_tracked_covered():
    if not MANIFEST.is_file() or not CHECKSUMS.is_file():
        pytest.skip("SP00 provenance artifacts not generated yet")

    with MANIFEST.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    tracked = {r["path"].replace("\\", "/") for r in rows if r.get("tracked") == "yes"}
    assert tracked, "no tracked files in manifest"

    covered: set[str] = set()
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "  " in line:
            _, path = line.split("  ", 1)
        else:
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            _, path = parts
        covered.add(path.replace("\\", "/"))

    missing = sorted(tracked - covered)
    assert missing == [], f"{len(missing)} tracked files lack checksums (e.g. {missing[:5]})"
