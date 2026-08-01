"""Unit tests for merge_trefoil_closure helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("merge_trefoil_closure.py")


def _load():
    spec = importlib.util.spec_from_file_location("merge_trefoil_closure", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def merge_mod():
    return _load()


def test_only_in_left_and_identical_overlaps(tmp_path, merge_mod):
    left = tmp_path / "left"
    right = tmp_path / "right"
    (left / "shared").mkdir(parents=True)
    (right / "shared").mkdir(parents=True)
    (left / "shared" / "a.txt").write_text("same", encoding="utf-8")
    (right / "shared" / "a.txt").write_text("same", encoding="utf-8")
    (left / "only_l.txt").write_text("L", encoding="utf-8")
    (right / "only_r.txt").write_text("R", encoding="utf-8")

    both = merge_mod.assert_identical_overlaps(left, right)
    assert both == ["shared/a.txt"]
    assert merge_mod.only_in_left(left, right) == ["only_l.txt"]
    assert merge_mod.only_in_left(right, left) == ["only_r.txt"]


def test_abort_on_content_mismatch(tmp_path, merge_mod):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "x.txt").write_text("A", encoding="utf-8")
    (right / "x.txt").write_text("B", encoding="utf-8")
    with pytest.raises(RuntimeError, match="differ in content"):
        merge_mod.assert_identical_overlaps(left, right)


def test_count_files_skips_pycache(tmp_path, merge_mod):
    root = tmp_path / "t"
    (root / "__pycache__").mkdir(parents=True)
    (root / "__pycache__" / "x.pyc").write_bytes(b"\0")
    (root / "ok.txt").write_text("y", encoding="utf-8")
    assert merge_mod.count_files(root) == 1
