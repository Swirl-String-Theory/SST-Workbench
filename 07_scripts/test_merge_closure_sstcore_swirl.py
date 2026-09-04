"""Unit tests for merge_closure_sstcore_swirl helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("merge_closure_sstcore_swirl.py")


def _load():
    spec = importlib.util.spec_from_file_location("merge_closure_sstcore_swirl", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_should_skip():
    m = _load()
    assert m.should_skip("trefoil_closure/README.md")
    assert m.should_skip("trefoil_closure/foo.py")
    assert m.should_skip("__pycache__/x.py")
    assert not m.should_skip("main.py")
    assert not m.should_skip("multisector_fit_results/x.csv")


def test_rel_key(tmp_path):
    m = _load()
    root = tmp_path / "r"
    f = root / "a" / "b.txt"
    f.parent.mkdir(parents=True)
    f.write_text("x", encoding="utf-8")
    assert m.rel_key(root, f) == "a/b.txt"
