"""Validate 10_docs/migration/path_map.csv against disk and CATALOG_v0.1.md."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
PATH_MAP = WB / "10_docs" / "migration" / "path_map.csv"
CATALOG = WB / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"

REQUIRED_FIELDS = {
    "old_path",
    "new_path",
    "domain",
    "letter",
    "catalog_id",
    "kind",
    "phase",
    "junction",
    "status",
    "note",
}
VALID_STATUS = {"pending", "moved", "verified", "reverted", "skipped"}
VALID_PHASE = re.compile(r"^(SP\d{2})( / SP\d{2})?$|^-$")
VALID_KIND = {
    "code",
    "data",
    "output",
    "tooling",
    "archive",
    "vendored",
    "stub",
    "app",
    "campaign",
    "tool",
}


def _load_rows() -> list[dict[str, str]]:
    if not PATH_MAP.is_file():
        pytest.skip(f"missing {PATH_MAP}")
    with PATH_MAP.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows, "path_map.csv is empty"
    return rows


def _catalog_ids() -> set[str]:
    text = CATALOG.read_text(encoding="utf-8")
    return set(re.findall(r"^\|\s*`?([A-F]\d{3})`?\s*\|", text, flags=re.M))


def test_path_map_schema_and_status():
    rows = _load_rows()
    assert REQUIRED_FIELDS <= set(rows[0].keys())
    for row in rows:
        assert row["status"] in VALID_STATUS, row
        assert VALID_PHASE.match(row["phase"]), row
        assert row["kind"] in VALID_KIND, row
        assert row["junction"] in {"yes", "no"}, row


def _is_glob(old_path: str) -> bool:
    return any(ch in old_path for ch in "*?[")


def test_path_map_unique_new_paths():
    """No two whole-directory rows may claim the same destination.

    Two kinds of row are excluded, because for them a shared destination is correct:

    * skipped rows record provenance, not an action - a directory that was partly moved
      and partly locked legitimately leaves a second row pointing at the same place;
    * glob rows deposit *files* into a collection directory, so KnotPlot/*.py,
      *.kps, *.lnk, *.js, *.md and run_build*.cmd all landing in the knotplot tool
      directory is the intended result, not a collision.

    A row that moves a whole directory still claims its destination exclusively.
    """
    rows = [
        r
        for r in _load_rows()
        if r["status"] != "skipped" and not _is_glob(r["old_path"])
    ]
    news = [r["new_path"] for r in rows]
    dupes = sorted({p for p in news if news.count(p) > 1})
    assert dupes == [], f"whole-directory rows share a destination: {dupes}"


def test_path_map_old_paths_exist_when_pending():
    rows = _load_rows()
    missing = []
    for row in rows:
        if row["status"] != "pending":
            continue
        op = row["old_path"]
        if "*" in op:
            # Glob patterns are resolved at move time
            continue
        if not (WB / op).exists():
            missing.append(op)
    assert missing == [], f"pending old_path missing on disk: {missing}"


def test_path_map_catalog_ids_known():
    rows = _load_rows()
    known = _catalog_ids()
    # IDs are unique only within domain-letter; bare ID must appear somewhere in catalog
    bad = []
    for row in rows:
        cid = row["catalog_id"]
        if not cid:
            continue
        if cid not in known:
            bad.append((row["old_path"], cid))
    assert bad == [], f"unknown catalog_id values: {bad}"
