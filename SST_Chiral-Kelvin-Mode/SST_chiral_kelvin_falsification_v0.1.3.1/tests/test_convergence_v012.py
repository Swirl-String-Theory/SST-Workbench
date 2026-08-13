"""Unit tests for chiral_kelvin.convergence_v012 and conclusions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from chiral_kelvin import __version__
from chiral_kelvin.conclusions import (
    CONCLUSIONS,
    build_conclusions_summary,
    write_conclusions_summary,
)
from chiral_kelvin.core import make_ring
from chiral_kelvin.convergence_v012 import (
    CORE_DIAGNOSTIC_MAX,
    CORE_RESOLVED_MAX,
    WAVELENGTH_DIAGNOSTIC_PPW,
    WAVELENGTH_RESOLVED_PPW,
    _relative_complex_distance,
    arclength_fourier_fingerprint,
    core_resolution,
    eigen_condition_numbers,
    fingerprint_similarity,
    group_matching_clusters,
    matcher_self_check_v012,
    mode_ppw,
    wavelength_resolution_status,
)


PACK_ROOT = Path(__file__).resolve().parents[1]


def test_package_version() -> None:
    assert __version__ == "0.1.3.1"


def test_core_resolution_statuses() -> None:
    points = make_ring(8)
    from chiral_kelvin.convergence_v012 import segment_lengths

    ds_max = float(np.max(segment_lengths(points)))

    resolved = core_resolution(
        points,
        core_a=ds_max / (CORE_RESOLVED_MAX * 0.5),
    )
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved"] is True
    assert resolved["eta_a_max"] <= CORE_RESOLVED_MAX

    diagnostic = core_resolution(
        points,
        core_a=ds_max / 1.0,
    )
    assert diagnostic["status"] == "DIAGNOSTIC"
    assert CORE_RESOLVED_MAX < diagnostic["eta_a_max"] <= CORE_DIAGNOSTIC_MAX

    under = core_resolution(
        points,
        core_a=ds_max / (CORE_DIAGNOSTIC_MAX * 2.0),
    )
    assert under["status"] == "UNDERRESOLVED"
    assert under["eta_a_max"] > CORE_DIAGNOSTIC_MAX


def test_core_resolution_rejects_nonpositive_core() -> None:
    points = make_ring(8)
    with pytest.raises(ValueError, match="core_a must be positive"):
        core_resolution(points, core_a=0.0)
    with pytest.raises(ValueError, match="core_a must be positive"):
        core_resolution(points, core_a=-1.0)


def test_arclength_fourier_fingerprint_normalized() -> None:
    n = 16
    points = make_ring(n)
    # Pure m=2 circumferential displacement in the plane.
    theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    q3d = np.column_stack(
        [
            np.cos(2.0 * theta),
            np.sin(2.0 * theta),
            np.zeros(n),
        ]
    ).astype(complex)

    fp = arclength_fourier_fingerprint(q3d, points, max_m=8)

    assert fp.shape == (9,)
    assert np.all(fp >= 0.0)
    assert abs(float(np.sum(fp)) - 1.0) < 1.0e-12
    assert int(np.argmax(fp)) == 2


def test_arclength_fourier_fingerprint_default_nyquist() -> None:
    n = 64
    points = make_ring(n)
    q3d = np.zeros((n, 3), dtype=complex)
    q3d[:, 0] = 1.0

    fp = arclength_fourier_fingerprint(q3d, points)
    expected_max_m = n // 2 - 1

    assert fp.shape == (expected_max_m + 1,)
    assert expected_max_m > 24


def test_mode_ppw_and_wavelength_status() -> None:
    assert mode_ppw(96, 0) == float("inf")
    assert wavelength_resolution_status(mode_ppw(96, 0)) == "NOT_APPLICABLE"

    assert mode_ppw(96, 8) == pytest.approx(12.0)
    assert wavelength_resolution_status(12.0) == "RESOLVED"
    assert wavelength_resolution_status(WAVELENGTH_RESOLVED_PPW) == "RESOLVED"

    assert wavelength_resolution_status(10.0) == "DIAGNOSTIC"
    assert wavelength_resolution_status(WAVELENGTH_DIAGNOSTIC_PPW) == "DIAGNOSTIC"

    assert wavelength_resolution_status(7.0) == "UNDERRESOLVED"
    assert mode_ppw(96, 16) == pytest.approx(6.0)


def test_fingerprint_similarity_identity_and_orthogonal() -> None:
    a = np.asarray([1.0, 0.0, 0.0])
    b = np.asarray([0.0, 1.0, 0.0])
    assert fingerprint_similarity(a, a) == pytest.approx(1.0)
    assert fingerprint_similarity(a, b) == pytest.approx(0.0)
    assert fingerprint_similarity(np.zeros(3), a) == 0.0
    assert fingerprint_similarity(np.array([]), a) == 0.0


def test_eigen_condition_numbers_well_conditioned() -> None:
    # Diagonal Hermitian operator: left == right, kappa == 1.
    operator = np.diag([1.0 + 0.0j, 2.0 + 0.0j, 3.0 + 0.0j])
    eigenvalues = np.diag(operator).copy()
    right_vectors = np.eye(3, dtype=complex)

    kappa = eigen_condition_numbers(
        operator,
        eigenvalues,
        right_vectors,
    )

    assert kappa.shape == (3,)
    assert np.all(np.isfinite(kappa))
    assert np.all(kappa >= 1.0 - 1.0e-9)
    assert np.allclose(kappa, 1.0, atol=1.0e-8)


def test_relative_complex_distance() -> None:
    assert _relative_complex_distance(1.0, 1.0) == 0.0
    assert _relative_complex_distance(1.0, 1.001) == pytest.approx(
        0.001 / 1.001,
        rel=1e-12,
    )


def _synthetic_mode(
    index: int,
    lam: complex,
    vector: np.ndarray,
    *,
    branch: int = 1,
    n_points: int = 48,
) -> dict:
    fingerprint = np.zeros(5, dtype=float)
    fingerprint[index % 5] = 1.0
    dominant_m = int(np.argmax(fingerprint))
    ppw = mode_ppw(n_points, dominant_m)
    return {
        "index": index,
        "lambda": lam,
        "sigma": float(np.real(lam)),
        "omega": float(-np.imag(lam)),
        "branch_sign": branch,
        "circularity": float((-1) ** index),
        "vector": vector,
        "fingerprint": fingerprint,
        "dominant_m": dominant_m,
        "ppw": ppw,
        "wavelength_status": wavelength_resolution_status(ppw),
        "condition_number": 1.0,
        "q3d": np.zeros((4, 3), dtype=complex),
    }


def test_group_matching_clusters_merges_near_degenerate() -> None:
    from chiral_kelvin.convergence_v012 import OMEGA_K

    v0 = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=complex)
    v1 = np.asarray([0.0, 1.0, 0.0, 0.0], dtype=complex)
    v2 = np.asarray([0.0, 0.0, 1.0, 0.0], dtype=complex)

    # Two near-degenerate modes (relative split 1e-4) and one distant.
    lam0 = (1.0 - 1.0j) * OMEGA_K
    lam1 = (1.00005 - 1.00005j) * OMEGA_K
    lam2 = (3.0 - 2.0j) * OMEGA_K

    bundle = {
        "modes": [
            _synthetic_mode(0, lam0, v0),
            _synthetic_mode(1, lam1, v1),
            _synthetic_mode(2, lam2, v2),
        ],
        "core_resolution": {
            "eta_a_max": 0.1,
            "status": "RESOLVED",
        },
        "equilibrium_status": "relative_equilibrium_reference",
    }

    clusters = group_matching_clusters(bundle, tolerance=1.0e-3)
    dims = sorted(c["dimension"] for c in clusters)
    assert dims == [1, 2]
    merged = next(c for c in clusters if c["dimension"] == 2)
    assert set(merged["member_indices"]) == {0, 1}
    assert "ppw" in merged
    assert "wavelength_status" in merged


def test_matcher_self_check_v012_ring() -> None:
    result = matcher_self_check_v012(force_python=True)
    assert result["ok"] is True
    assert result["minimum_self_overlap"] > 1.0 - 1.0e-9
    assert result["minimum_fingerprint_similarity"] > 1.0 - 1.0e-9


def test_run_resolution_ladder_help() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(PACK_ROOT / "run_resolution_ladder.py"),
            "--help",
        ],
        cwd=PACK_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "v0.1.3.1" in completed.stdout
    assert "resolved" in completed.stdout


def test_build_conclusions_summary() -> None:
    summary = build_conclusions_summary(
        implementation_ok=True,
        numerical_tracking_ready=False,
        physical_interpretation_ready=False,
    )

    assert summary["release"] == "0.1.3.1"
    assert summary["ledger_type"] == "scientific_conclusions"
    assert summary["implementation_ok"] is True
    assert summary["numerical_tracking_ready"] is False
    assert summary["physical_interpretation_ready"] is False
    assert summary["conclusion_count"] == len(CONCLUSIONS)
    assert summary["status_counts"]["NUMERICALLY_VERIFIED"] >= 1
    assert summary["conclusions"] is CONCLUSIONS


def test_write_conclusions_summary(tmp_path: Path) -> None:
    path = tmp_path / "conclusions_summary.json"
    summary = write_conclusions_summary(
        path,
        implementation_ok=True,
        numerical_tracking_ready=True,
        physical_interpretation_ready=False,
    )

    assert path.is_file()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["release"] == "0.1.3.1"
    assert loaded["conclusion_count"] == summary["conclusion_count"]
    assert loaded["implementation_ok"] is True


def test_safe_fraction_and_eligibility_gates() -> None:
    from chiral_kelvin.convergence_v012 import (
        _physical_eligible,
        _resolved_eligible,
        _safe_fraction,
    )

    assert _safe_fraction(3, 4) == 0.75
    assert _safe_fraction(1, 0) == 0.0

    resolved_row = {
        "low_core_status": "RESOLVED",
        "high_core_status": "RESOLVED",
        "low_wavelength_status": "RESOLVED",
        "high_wavelength_status": "RESOLVED",
        "equilibrium_ready": False,
    }
    assert _resolved_eligible(resolved_row) is True
    assert _physical_eligible(resolved_row) is False

    underresolved = dict(resolved_row)
    underresolved["high_wavelength_status"] = "DIAGNOSTIC"
    assert _resolved_eligible(underresolved) is False

    physical_row = dict(resolved_row)
    physical_row["equilibrium_ready"] = True
    assert _physical_eligible(physical_row) is True


def test_conclusions_include_c3_entries() -> None:
    ids = {row["id"] for row in CONCLUSIONS}
    for required in (
        "C3.1",
        "C3.2",
        "C3.3",
        "C3.4",
        "C3.5",
        "C3.6",
        "C3.7",
        "C3.8",
    ):
        assert required in ids
