"""Tests for catalog kpc -> iNNNNN conversion."""

from __future__ import annotations

from pathlib import Path

import pytest

from convert_catalog_kpc import (
    MATRIX_PREFIX,
    checkpoint_name,
    iter_source_kpc,
    transform_kpc,
)

MATRIX_DIR = Path(__file__).resolve().parents[1]
KNOTS_DIR = MATRIX_DIR.parent / "knots"


def test_checkpoint_mapping() -> None:
    assert checkpoint_name("analytic_D1") == "i00000"
    assert checkpoint_name("trial_001k") == "i01000"
    assert checkpoint_name("trial_015k") == "i15000"


def test_checkpoint_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        checkpoint_name("trial_final")


def test_refine_nbeads_remains_refine_nbeads() -> None:
    src = "refine nbeads 300\necho CHECKPOINT analytic_D1\nsave knots/knot_0.1/knot_0.1_analytic_D1.txt\n"
    out = transform_kpc(src, "knot_0.1")
    assert "refine nbeads 300" in out


def test_refine_nbeads_600_preserved() -> None:
    src = "refine nbeads 600\necho CHECKPOINT analytic_D1\nsave knots/link_2.2.1/link_2.2.1_analytic_D1.txt\n"
    out = transform_kpc(src, "link_2.2.1")
    assert "refine nbeads 600" in out


def test_torus_keeps_torus_line() -> None:
    src = (
        "torus 2 3 300\n"
        "echo CHECKPOINT analytic_D1\n"
        "save knots/torus_2.3/torus_2.3_analytic_D1.txt\n"
    )
    out = transform_kpc(src, "torus_2.3")
    assert "torus 2 3 300" in out
    assert "refine" not in out
    assert f"save {MATRIX_PREFIX}/catalog/torus_2.3/torus_2.3_i00000.k float" in out
    assert f"coords {MATRIX_PREFIX}/catalog/torus_2.3/torus_2.3_i00000.txt" in out


def test_dual_save_and_coords() -> None:
    src = (
        "echo CHECKPOINT trial_001k\n"
        "save knots/knot_0.1/knot_0.1_trial_001k.txt\n"
        "\n"
        "ago 1000\n"
    )
    out = transform_kpc(src, "knot_0.1")
    assert "echo CHECKPOINT i01000" in out
    assert f"save {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i01000.k float" in out
    assert f"coords {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i01000.txt" in out
    assert "save knots/" not in out
    assert (
        f"coords {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i01000.txt\n"
        "\n"
        "ago 1000\n"
    ) in out


def test_iter_source_skips_effort_active() -> None:
    if not KNOTS_DIR.is_dir(): pytest.skip("source KnotPlot/knots tree not bundled")
    paths = iter_source_kpc(KNOTS_DIR)
    names = [p.name for p in paths]
    assert "build_effort_active.kpc" not in names
    assert any(p.name == "build_knot_0.1.kpc" for p in paths)
    assert len(paths) == 49


def test_knot_0_1_golden_snippet() -> None:
    if not KNOTS_DIR.is_dir(): pytest.skip("source KnotPlot/knots tree not bundled")
    src_path = KNOTS_DIR / "knot_0.1" / "build_knot_0.1.kpc"
    text = src_path.read_text(encoding="utf-8")
    out = transform_kpc(text, "knot_0.1")
    expected_head = (
        "% build_knot_0.1.kpc\n"
        "reset all\n"
        "load 0.1\n"
        "refine nbeads 300\n"
        "mode cb\n"
    )
    assert out.startswith(expected_head)
    assert "echo CHECKPOINT i00000" in out
    assert (
        f"save {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i00000.k float\n"
        f"coords {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i00000.txt\n"
        "\n"
        "ago 1000\n"
        "echo CHECKPOINT i01000\n"
    ) in out
    assert (
        f"save {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i01000.k float\n"
        f"coords {MATRIX_PREFIX}/catalog/knot_0.1/knot_0.1_i01000.txt\n"
    ) in out
    assert "analytic_D1" not in out
    assert "trial_001k" not in out
