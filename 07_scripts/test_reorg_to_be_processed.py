"""Unit tests for reorg_to_be_processed mapping."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("reorg_to_be_processed.py")


def _load():
    spec = importlib.util.spec_from_file_location("reorg_to_be_processed", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_dir_moves_unique_and_cover_key_targets():
    m = _load()
    srcs = [s for s, _ in m.DIR_MOVES]
    dsts = [d for _, d in m.DIR_MOVES]
    assert len(srcs) == len(set(srcs))
    assert len(dsts) == len(set(dsts))
    assert any(d.startswith("SST_chi_phase_research/") for d in dsts)
    assert any(d.startswith("SST_horn_bem_research/") for d in dsts)
    assert any(d.startswith("SST_v0_8_19_routes_research/") for d in dsts)
    assert (
        "SST_fermat_pybind_research/SST_fermat_pybind_research_v0.1" in dsts
    )
    assert (
        "SST_Route_I_relative_entropy_PoC/routeI_heat_guard_patch_bundle_v0_8_19"
        in dsts
    )


def test_resolve_dir_moves_paths(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "WB", tmp_path)
    monkeypatch.setattr(m, "SRC", tmp_path / "to_be_processed")
    pairs = m.resolve_dir_moves()
    assert pairs[0][0] == tmp_path / "to_be_processed" / m.DIR_MOVES[0][0]
    assert pairs[0][1] == tmp_path / m.DIR_MOVES[0][1]


def test_vortex_inbox_constant():
    m = _load()
    assert m.VORTEX_INBOX == "GUI/vortexring-lab/inbox_from_to_be_processed"
