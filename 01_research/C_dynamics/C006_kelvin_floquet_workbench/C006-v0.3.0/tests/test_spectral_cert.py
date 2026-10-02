import numpy as np

from sst_kelvin_workbench.spectral_cert import (
    branch_nonmonotonicity,
    match_spectra,
    overdamped_census,
    symmetry_defect,
    track_spectrum,
    quadratic_eigenproblem_selftest,
)


def test_match_spectra_permutation_invariant():
    a = np.array([1+2j, -1+0.5j, 3-4j])
    b = np.array([3-4j, 1+2j, -1+0.5j])
    m = match_spectra(a, b)
    assert len(m["matched"]) == 3
    assert max(p["relative_distance"] for p in m["matched"]) < 1e-14


def test_track_spectrum_small_shifts_persist():
    levels = [
        {"label": 24, "eigenvalues": [1+1j, -1-1j]},
        {"label": 32, "eigenvalues": [-1.01-0.99j, 1.01+0.99j]},
        {"label": 40, "eigenvalues": [1.015+0.985j, -1.015-0.985j]},
    ]
    t = track_spectrum(levels, rel_tol=0.05)
    assert t["ok"]
    assert t["persistent_count"] == 2


def test_overdamped_like_is_temporal_generator_definition():
    c = overdamped_census([2+0j, -1+0.01j, 1j], oscillation_fraction_max=0.05)
    flags = [r["overdamped_like"] for r in c["modes"]]
    assert flags == [True, True, False]


def test_symmetry_defect_exact_quartet():
    vals = [1+2j, 1-2j, -1+2j, -1-2j]
    s = symmetry_defect(vals)
    assert s["conjugate_max"] < 1e-14
    assert s["quartet_max"] < 1e-14


def test_branch_nonmonotonicity_detects_turning_point():
    scans = [0.0, 1.0, 2.0]
    spectra = [[1+1j], [2+1j], [1.5+1j]]
    r = branch_nonmonotonicity(scans, spectra)
    assert r["ok"]
    assert r["nonmonotonic_real_count"] == 1


def test_quadratic_eigenproblem_selftest_passes():
    r = quadratic_eigenproblem_selftest()
    assert r["pass"]
    roots = sorted(round(x["re"], 12) for x in r["roots"])
    assert roots == [-2.0, -1.0]
