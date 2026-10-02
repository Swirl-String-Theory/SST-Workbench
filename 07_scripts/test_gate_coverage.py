"""SP10: every active family appears in the gate report; non-pass rows have reasons."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402

REPORT = WB / "10_docs" / "migration" / "reproducibility_gate.csv"


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    if not REPORT.is_file():
        pytest.skip("reproducibility_gate.csv not generated yet")
    with REPORT.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_every_active_family_has_a_gate_row(rows: list[dict[str, str]]):
    reported = {(r["domain"], r["catalog_id"]) for r in rows}
    missing = []
    for fam in cm.discover():
        yaml = fam.path / "FAMILY.yaml"
        status = "active"
        if yaml.is_file():
            for line in yaml.read_text(encoding="utf-8").splitlines():
                if line.startswith("status:"):
                    status = line.split(":", 1)[1].strip()
        if status != "active":
            continue
        if (fam.domain, fam.catalog_id) not in reported:
            missing.append((fam.domain, fam.catalog_id))
    assert missing == [], f"active families missing from gate report: {missing[:20]}"


def test_non_pass_rows_have_a_reason(rows: list[dict[str, str]]):
    bad = [
        (r["catalog_id"], r["status"], r.get("note"))
        for r in rows
        if r["status"] != "pass" and not (r.get("note") or "").strip()
    ]
    assert bad == [], f"non-pass rows without note: {bad[:10]}"


def test_fail_rows_are_justified_or_absent(rows: list[dict[str, str]]):
    fails = [r for r in rows if r["status"] == "fail"]
    for r in fails:
        assert (r.get("note") or "").strip(), r
