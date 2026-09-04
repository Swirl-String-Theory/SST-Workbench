"""Unit tests for merge_sst_dashboard helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("merge_sst_dashboard.py")


def _load():
    spec = importlib.util.spec_from_file_location("merge_sst_dashboard", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_rel_key(tmp_path):
    m = _load()
    root = tmp_path / "r"
    f = root / "exports" / "ideal.txt"
    f.parent.mkdir(parents=True)
    f.write_text("x", encoding="utf-8")
    assert m.rel_key(root, f) == "exports/ideal.txt"


def test_place_identical_and_conflict_prefer_sstcore(tmp_path):
    m = _load()
    dest = tmp_path / "dash"
    dest.mkdir()
    # swirl first places a file
    swirl_src = tmp_path / "swirl_ideal.txt"
    swirl_src.write_text("SWIRL", encoding="utf-8")
    assert m.place_file(swirl_src, dest, "exports/ideal.txt", "swirl", dry_run=False) == "moved"
    assert (dest / "exports" / "ideal.txt").read_text(encoding="utf-8") == "SWIRL"

    # identical skip
    again = tmp_path / "again.txt"
    again.write_text("SWIRL", encoding="utf-8")
    assert m.place_file(again, dest, "exports/ideal.txt", "swirl", dry_run=False) == "skipped_identical"
    assert not again.exists()

    # sstcore wins
    sst = tmp_path / "sst_ideal.txt"
    sst.write_text("SSTCORE", encoding="utf-8")
    assert (
        m.place_file(sst, dest, "exports/ideal.txt", "sstcore", dry_run=False)
        == "conflict_preferred"
    )
    assert (dest / "exports" / "ideal.txt").read_text(encoding="utf-8") == "SSTCORE"
    assert (dest / "_merge_conflict" / "exports" / "ideal.txt").read_text(encoding="utf-8") == "SWIRL"
