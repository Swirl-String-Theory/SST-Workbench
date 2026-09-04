"""GUI casing: no `GUI/` ever entered the index, before or after the SP06 move.

SP00 Q3 established that the index held 459 files under lowercase `gui/` and none
under `GUI/`, so SP03's rename-through-a-temp-name was a no-op. SP06 then moved the
tree into `05_apps/` and `03_data/`, so `gui/` survives only as a compat junction.

What still has to hold is the thing that would corrupt a checkout on a case-sensitive
filesystem: the index must never carry both casings.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

WB = Path(__file__).resolve().parents[1]


def _tracked_paths() -> list[str]:
    proc = subprocess.run(
        ["git", "-c", "core.longpaths=true", "ls-files", "-z"],
        cwd=WB,
        capture_output=True,
        check=True,
    )
    return [p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p]


def test_index_never_carries_uppercase_gui():
    upper = [p for p in _tracked_paths() if p.startswith("GUI/")]
    assert upper == [], f"unexpected GUI/ index paths: {upper[:5]}"


def test_gui_tree_has_left_the_root():
    """After SP06 the old root is a junction, not tracked content."""
    tracked = [p for p in _tracked_paths() if p.startswith("gui/")]
    assert tracked == [], f"gui/ still tracked at root: {tracked[:5]}"


def test_gui_content_landed_in_apps():
    apps = WB / "05_apps"
    assert apps.is_dir()
    families = {p.name for p in apps.iterdir() if p.is_dir()}
    for expected in ("A002_coil_gui", "A003_vortexlab", "A004_math_lab"):
        assert expected in families, f"{expected} missing from 05_apps: {sorted(families)}"
