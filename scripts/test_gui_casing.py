"""SP03: gui casing is already normalized (no-op)."""

from __future__ import annotations

import subprocess
from pathlib import Path

WB = Path(__file__).resolve().parents[1]


def test_gui_index_is_lowercase_only():
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=WB,
        capture_output=True,
        check=True,
    )
    paths = [p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p]
    gui = [p for p in paths if p.startswith("gui/")]
    gui_upper = [p for p in paths if p.startswith("GUI/")]
    assert len(gui) > 0
    assert gui_upper == [], f"unexpected GUI/ index paths: {gui_upper[:5]}"
    assert (WB / "gui").is_dir()
    # On Windows the display name should be lowercase.
    assert (WB / "gui").name == "gui"
