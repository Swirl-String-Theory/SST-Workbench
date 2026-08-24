"""Tests for MultiDynamics run_matrix_batch orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

MATRIX_DIR = Path(__file__).resolve().parents[1]
if str(MATRIX_DIR) not in sys.path:
    sys.path.insert(0, str(MATRIX_DIR))

from run_matrix_batch import (  # noqa: E402
    ALL_FAMILY,
    CORE_FAMILY,
    knotplot_argv,
    log_indicates_nothing_loaded,
    main,
    resolve_script,
)


def test_core_family_is_subset_of_all() -> None:
    assert set(CORE_FAMILY).issubset(set(ALL_FAMILY))
    assert "00_baseline_MEB_tight.kpc" in ALL_FAMILY
    assert "00_baseline_MEB_tight.kpc" not in CORE_FAMILY
    assert "90_charge_anneal_MEB.kpc" in CORE_FAMILY


def test_all_family_scripts_exist() -> None:
    for name in ALL_FAMILY:
        path = MATRIX_DIR / name
        assert path.is_file(), f"missing {path}"


def test_knotplot_argv_matches_run_build() -> None:
    argv = knotplot_argv(Path(r"C:\fake\KnotPlot.exe"))
    assert argv[-1] == "-nog"
    assert argv[0].endswith("KnotPlot.exe")
    assert len(argv) == 2


def test_nothing_loaded_detector() -> None:
    assert log_indicates_nothing_loaded("Current position is safe.\nnothing loaded\n")
    assert log_indicates_nothing_loaded("*** nothing to save\n")
    assert not log_indicates_nothing_loaded("Length = 12.3\nSMOKE_OK\n")
    # Startup noise then successful load/save must not fail the run.
    mixed = (
        "nothing loaded\n*** nothing to save\n"
        "knot loaded from `3.1'\nSMOKE_OK\nknot saved to `out.k'\n"
    )
    assert not log_indicates_nothing_loaded(mixed)


def test_resolve_script_relative() -> None:
    path = resolve_script(MATRIX_DIR, "smoke_load_3_1.kpc")
    assert path == (MATRIX_DIR / "smoke_load_3_1.kpc").resolve()


def test_dry_run_one_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "--one",
            "smoke_load_3_1.kpc",
            "--matrix-dir",
            str(MATRIX_DIR),
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN:" in out
    assert "-nog" in out
    assert "smoke_load_3_1.kpc" in out
    assert "logs" in out.replace("\\", "/")
    assert "smoke_load_3_1_console.log" in out
