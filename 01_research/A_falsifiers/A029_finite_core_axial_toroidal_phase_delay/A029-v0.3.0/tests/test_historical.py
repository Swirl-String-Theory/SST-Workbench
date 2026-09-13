from __future__ import annotations

import json
from pathlib import Path

import pytest

from sst_finite_core_falsifier.historical import (
    accounting_status_from_rows,
    case_to_accounting_row,
    classify_historical_independence,
    default_frozen_case_roots,
    discover_case_paths,
    extract_accounting_frequencies,
    extract_holonomy,
    find_sealed_cases,
    has_raw_trajectory_payload,
    is_analysis_case_record,
    is_excluded_case_path,
    load_historical_cases,
    looks_like_case_path,
    opaque_token,
    residual_status_from_rows,
    sha256_file,
    sibling_trajectory_paths,
)
from sst_finite_core_falsifier.holonomy import k_closed
from sst_finite_core_falsifier.phase_contract import wrap_phase
from sst_finite_core_falsifier.residual import (
    ACCOUNTING_OK,
    MISSING_CASES,
    NO_INDEPENDENT_PHASE,
    NONINDEPENDENT_TAU,
    run_phase_residual,
)


def _minimal_case(*, phi_env: float = 0.4, omega: float = 0.8, tau: float = 0.5, trajectory: bool = False) -> dict:
    omega_adv = 1.0
    omega_intr = -0.2
    l_hat = 10.0
    n, m, theta = 2, 1, 0.3
    rec = {
        "status": "OK",
        "analysis_semantics": "EXACT_CLOSED_LOOP",
        "k_hat": k_closed(n, m, theta, l_hat),
        "loop_length_over_core": l_hat,
        "bishop_holonomy": theta,
        "m_runtime": m,
        "n_runtime": n,
        "profile_name_runtime": "gaussian",
        "axial_ratio_runtime": 0.75,
        "omega_median": omega,
        "advective_frequency_median": omega_adv,
        "omega_intrinsic_median": omega_intr,
        "loop_phase": wrap_phase(-omega * tau + phi_env),
        "tau_return": tau,
        "delay": {"available": True, "loop_phase": wrap_phase(-omega * tau + phi_env), "tau_return": tau},
        "dispersion": {
            "center_mode": {
                "omega": omega,
                "advective_frequency": omega_adv,
                "omega_intrinsic": omega_intr,
            }
        },
        "swirl_clock": {"lambda_real": 0.01, "lambda_imag": -omega},
    }
    if trajectory:
        rec["trajectory"] = {"t": [0.0, tau], "a_t": [1.0, 0.5]}
    return rec


def test_sha256_file(tmp_path: Path):
    path = tmp_path / "blob.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_opaque_token_stable():
    assert opaque_token("a", 1) == opaque_token("a", 1)
    assert opaque_token("a", 1) != opaque_token("b", 1)


def test_is_analysis_case_record():
    assert is_analysis_case_record(_minimal_case())
    assert not is_analysis_case_record({"k_hat": 1.0})
    assert not is_analysis_case_record([1, 2])


def test_has_raw_trajectory_payload():
    assert has_raw_trajectory_payload(_minimal_case()) is False
    assert has_raw_trajectory_payload(_minimal_case(trajectory=True)) is True


def test_looks_like_case_path_and_exclusions(tmp_path: Path):
    cases = tmp_path / "blind" / "cases"
    cases.mkdir(parents=True)
    good = cases / "0e45d1b17df49c20.json"
    good.write_text("{}", encoding="utf-8")
    cert = tmp_path / "paper_upgrade" / "PHASE_ACCOUNTING_CERTIFICATE.json"
    cert.parent.mkdir(parents=True)
    cert.write_text("{}", encoding="utf-8")
    named = tmp_path / "sealed_case.json"
    named.write_text("{}", encoding="utf-8")
    assert looks_like_case_path(good)
    assert not looks_like_case_path(cert)
    assert looks_like_case_path(named)
    assert is_excluded_case_path(cert)


def test_find_sealed_cases_includes_cases_dir(tmp_path: Path):
    cases = tmp_path / "blind" / "cases"
    cases.mkdir(parents=True)
    path = cases / "0e45d1b17df49c20.json"
    path.write_text(json.dumps(_minimal_case()), encoding="utf-8")
    found = find_sealed_cases(tmp_path)
    assert found == [path.resolve()]
    assert find_sealed_cases(cases) == [path.resolve()]


def test_extract_frequencies_and_holonomy():
    obj = _minimal_case()
    freqs = extract_accounting_frequencies(obj)
    assert freqs["omega_center"] == pytest.approx(0.8)
    assert freqs["omega_adv_closed"] == pytest.approx(1.0)
    assert freqs["k_ref_eigensolve"] == "not_performed_reanalysis_only"
    hol = extract_holonomy(obj)
    assert hol["holonomy_representation"] == "embedded_in_k"
    assert hol["stored_k_matches_k_closed"]


def test_classify_historical_independence_derived():
    audit = classify_historical_independence(_minimal_case())
    assert audit["target_independence"]["class"] == "derived_from_predictors"
    assert audit["target_independence"]["temporal_frequency_source"] == "derived_from_predictors"
    assert audit["target_independence"]["return_phase_source"] == "derived_from_predictors"
    assert audit["target_independence"]["spatial_mode_basis_source"] == "unavailable"
    assert audit["target_independence"]["predicted_vg_used_in_extraction"] is True
    assert audit["tau_return_independence"]["class"] == "derived_from_predicted_dispersion"
    assert audit["tau_return_independence"]["l_over_vg_used"] is True
    assert audit["residual_reason"] == NO_INDEPENDENT_PHASE


def test_sibling_trajectory_paths(tmp_path: Path):
    case = tmp_path / "abcd.json"
    case.write_text("{}", encoding="utf-8")
    assert sibling_trajectory_paths(case) == []
    traj = tmp_path / "abcd_trajectory.npz"
    traj.write_bytes(b"x")
    assert sibling_trajectory_paths(case) == [traj]


def test_case_to_accounting_row_identity(tmp_path: Path):
    path = tmp_path / "case.json"
    obj = _minimal_case()
    path.write_text(json.dumps(obj), encoding="utf-8")
    row = case_to_accounting_row(path, obj)
    assert row["evaluable_accounting"]
    assert row["accounting_identity"] == ACCOUNTING_OK
    assert row["phi_envelope"] == pytest.approx(0.4)
    assert row["accounts"]["ACCOUNT_M3"] == pytest.approx(wrap_phase(-0.8 * 0.5))


def test_load_and_status_helpers(tmp_path: Path):
    path = tmp_path / "cases" / "aa11bb22.json"
    path.parent.mkdir()
    path.write_text(json.dumps(_minimal_case()), encoding="utf-8")
    loaded = load_historical_cases([path], relative_to=tmp_path)
    assert loaded["inventory"][0]["path"] == "cases/aa11bb22.json"
    assert len(loaded["rows"]) == 1
    status, secondary = residual_status_from_rows(loaded["rows"])
    assert status == NO_INDEPENDENT_PHASE
    assert NONINDEPENDENT_TAU in secondary
    assert accounting_status_from_rows(loaded["rows"]) == ACCOUNTING_OK
    assert residual_status_from_rows([])[0] == MISSING_CASES


def test_default_frozen_roots_empty_without_sibling(tmp_path: Path):
    assert default_frozen_case_roots(tmp_path / "A029-v0.3.0") == []


def test_discover_prefers_out_then_historical(tmp_path: Path):
    out = tmp_path / "out"
    hist = tmp_path / "hist" / "cases"
    hist.mkdir(parents=True)
    (hist / "aa11bb22.json").write_text(json.dumps(_minimal_case()), encoding="utf-8")
    empty = discover_case_paths(out, pack_root=tmp_path, historical_roots=[hist.parent], search_default_historical=False)
    assert empty["source"] == "frozen_historical"
    assert len(empty["paths"]) == 1
    local = out / "cases"
    local.mkdir(parents=True)
    (local / "cc33dd44.json").write_text(json.dumps(_minimal_case()), encoding="utf-8")
    preferred = discover_case_paths(out, historical_roots=[hist.parent], search_default_historical=False)
    assert preferred["source"] == "out"
    assert preferred["paths"][0].name == "cc33dd44.json"


def test_run_phase_residual_historical_is_indeterminate(tmp_path: Path):
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "aa11bb22.json").write_text(json.dumps(_minimal_case()), encoding="utf-8")
    out = tmp_path / "run"
    result = run_phase_residual(out, pack_root=tmp_path, historical_roots=[tmp_path], search_default_historical=False)
    assert result["residual"]["status"] == NO_INDEPENDENT_PHASE
    assert result["residual"]["scientific_pass"] is False
    assert result["accounting"]["status"] == ACCOUNTING_OK
    assert result["accounting"]["scientific_pass"] is False
    assert (out / "paper_upgrade" / "PHASE_RESIDUAL_CERTIFICATE.json").is_file()
    assert (out / "paper_upgrade" / "FROZEN_CASE_INVENTORY.json").is_file()
