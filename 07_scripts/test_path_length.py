"""SP09: report the longest tracked paths; leftover overages must be deep trees."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
SHORT_VERSION_DIR = re.compile(r"^[A-F]\d{3}-v")
FAMILY_DIR = re.compile(r"^[A-F]\d{3}_")
DEEP_MARKERS = (
    "/_variants/",
    "-outputs/",
    "_outputs/",
    "/outputs_",
    "/geometries/",
    "/build/",
    "/.venv/",
)


def _tracked_files() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=WB)
    return [p.replace("\\", "/") for p in raw.decode("utf-8").split("\0") if p]


def test_reports_the_longest_ten_tracked_paths():
    files = _tracked_files()
    ranked = sorted(((len(p), p) for p in files), reverse=True)[:10]
    assert ranked, "git ls-files returned nothing"
    # Visible in failure output if a later assertion trips; also a live snapshot.
    snapshot = "\n".join(f"{n:3d}  {p}" for n, p in ranked)
    assert ranked[0][0] > 0, snapshot


def test_over_200_are_deep_trees_not_unrenamed_version_dirs():
    """Paths longer than 200 chars are allowed only as deep artifact trees.

    SP09 shortens version directories. Remaining overages live under ``_variants``
    or output folders whose names are frozen by the output-naming invariant.
    """
    bad = []
    over = []
    for path in _tracked_files():
        if len(path) <= 200:
            continue
        over.append(path)
        parts = path.split("/")
        for i, part in enumerate(parts[:-1]):
            if FAMILY_DIR.match(part) and i + 1 < len(parts):
                version = parts[i + 1]
                if version.startswith("_"):
                    continue
                if SHORT_VERSION_DIR.match(version):
                    continue
                if any(m in path for m in DEEP_MARKERS):
                    continue
                bad.append(path)
                break
    assert over, "expected some deep trees still over 200 characters"
    assert bad == [], f"long path still uses an unrenamed version dir: {bad[:5]}"
