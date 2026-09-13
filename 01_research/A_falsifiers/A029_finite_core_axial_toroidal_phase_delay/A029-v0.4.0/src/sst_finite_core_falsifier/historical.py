"""P2.5 reanalysis of frozen A029 analyze() case JSON.

Historical records store derived Phi_loop and synthetic tau_return. This
module ingests those fields for algebraic accounting and refuses to treat
them as an independent residual target.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from .holonomy import forbid_double_counted_holonomy, holonomy_record
from .phase_contract import (
    carrier_derived_phase,
    classify_target_independence,
    classify_tau_independence,
    convention_bridge,
    envelope_phase_from_derived,
    identity_fields,
)

CASE_GLOBS = (
    "**/cases/*.json",
    "**/*case*.json",
    "**/sealed_cases/*.json",
    "**/analysis/*closed*.json",
)
EXCLUDE_NAME_MARKERS = (
    "certificate",
    "manifest",
    "summary",
    "contract",
    "heartbeat",
    "run_state",
    "thresholds",
    "blind_split",
)
EXCLUDE_PARTS = {"paper_upgrade", "private_reveal_keys", ".venv", "__pycache__"}
REQUIRED_CASE_KEYS = ("k_hat", "loop_length_over_core")
CASE_HINT_KEYS = (
    "loop_phase",
    "delay",
    "tau_return",
    "bishop_holonomy",
    "m_runtime",
    "dispersion",
)
TRAJECTORY_KEYS = (
    "trajectory",
    "time_series",
    "times",
    "t",
    "a_t",
    "a_m",
    "modal_coefficient",
    "modal_coefficients",
    "envelope_raw",
    "raw_envelope",
    "complex_trace",
    "raw_trajectory",
)
TRAJECTORY_SUFFIXES = (
    "_trajectory.npz",
    "_trajectory.json",
    "_timeseries.npz",
    "_raw_envelope.npz",
)
HEX_STEM = re.compile(r"^[0-9a-f]{8,}$", re.I)
PARENT_BASIC_CASES = Path("A029-v0.2.0") / "outputs" / "basic" / "blind" / "cases"
V012_ARCHIVE_NAME = "SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.2_outputs.zip"
INDEPENDENT_PHASE_CLASSES = {
    "fully_model_independent_time_domain",
    "independent_time_domain_given_frozen_spatial_mode",
}


def sha256_file(path: Path | str, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def opaque_token(*parts: Any) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def is_excluded_case_path(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return True
    name = path.name.lower()
    return any(marker in name for marker in EXCLUDE_NAME_MARKERS)


def looks_like_case_path(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".json" or is_excluded_case_path(path):
        return False
    parent = path.parent.name.lower()
    if parent in {"cases", "sealed_cases"}:
        return True
    stem = path.stem.lower()
    if HEX_STEM.match(stem):
        return parent == "cases"
    return "case" in stem


def is_analysis_case_record(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if any(key not in obj for key in REQUIRED_CASE_KEYS):
        return False
    return any(key in obj for key in CASE_HINT_KEYS)


def has_raw_trajectory_payload(obj: dict[str, Any]) -> bool:
    for key in TRAJECTORY_KEYS:
        if obj.get(key) not in (None, {}, [], ""):
            return True
    delay = obj.get("delay")
    if isinstance(delay, dict):
        for key in TRAJECTORY_KEYS:
            if delay.get(key) not in (None, {}, [], ""):
                return True
    return False


def sibling_trajectory_paths(case_path: Path) -> list[Path]:
    stem = case_path.stem
    found = []
    for suffix in TRAJECTORY_SUFFIXES:
        candidate = case_path.with_name(stem + suffix)
        if candidate.is_file():
            found.append(candidate)
    return found


def find_sealed_cases(*roots: Path | str) -> list[Path]:
    hits: list[Path] = []
    for root in roots:
        if root is None:
            continue
        path = Path(root)
        if path.is_file():
            if looks_like_case_path(path):
                hits.append(path.resolve())
            continue
        if not path.exists():
            continue
        if path.name.lower() in {"cases", "sealed_cases"}:
            for candidate in path.glob("*.json"):
                if looks_like_case_path(candidate):
                    hits.append(candidate.resolve())
        for pattern in CASE_GLOBS:
            for candidate in path.glob(pattern):
                if looks_like_case_path(candidate):
                    hits.append(candidate.resolve())
    return sorted(set(hits))


def default_frozen_case_roots(pack_root: Path | str | None) -> list[Path]:
    if pack_root is None:
        return []
    family = Path(pack_root).resolve().parent
    parent_cases = family / PARENT_BASIC_CASES
    return [parent_cases] if parent_cases.is_dir() else []


def discover_case_paths(
    out: Path | str,
    *,
    pack_root: Path | str | None = None,
    historical_roots: Iterable[Path | str] | None = None,
    search_default_historical: bool = True,
) -> dict[str, Any]:
    out_cases = find_sealed_cases(Path(out))
    if out_cases:
        return {"paths": out_cases, "source": "out", "roots": [str(Path(out).resolve())]}
    roots = [Path(root).resolve() for root in (historical_roots or [])]
    if search_default_historical:
        roots.extend(default_frozen_case_roots(pack_root))
    unique_roots: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve())
        if key not in seen:
            seen.add(key)
            unique_roots.append(root)
    paths = find_sealed_cases(*unique_roots) if unique_roots else []
    return {
        "paths": paths,
        "source": "frozen_historical" if paths else "none",
        "roots": [str(root.resolve()) for root in unique_roots],
    }


def load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def classify_historical_independence(obj: dict[str, Any], *, case_path: Path | None = None) -> dict[str, Any]:
    from .residual import NO_INDEPENDENT_PHASE, NONINDEPENDENT_TAU, independence_gates_pass

    raw = has_raw_trajectory_payload(obj)
    siblings = sibling_trajectory_paths(case_path) if case_path is not None else []
    raw = raw or bool(siblings)
    delay = obj.get("delay") if isinstance(obj.get("delay"), dict) else {}
    synthetic = bool(delay.get("available")) or _finite(obj.get("tau_return"))
    target = classify_target_independence(
        predicted_omega_used_in_extraction=not raw,
        predicted_omega_used_for_demodulation=False,
        predicted_omega_used_for_bandpass=False,
        predicted_vg_used_in_extraction=not raw,
        spatial_mode_basis_source="unavailable" if not raw else "model_conditioned_frozen",
        raw_trajectory=raw,
        temporal_frequency_source="derived_from_predictors",
        return_phase_source="derived_from_predictors",
    )
    tau = classify_tau_independence(
        predicted_omega_used=not raw,
        predicted_group_velocity_used=not raw,
        synthetic_wavepacket_used=synthetic or not raw,
        l_over_vg_used=True,
        raw_trajectory=raw,
        search_window_source="unavailable" if not raw else "predictor_centered_wavepacket",
    )
    residual_reason = NO_INDEPENDENT_PHASE
    if independence_gates_pass(target, tau):
        residual_reason = "EVALUABLE"
    elif target.get("class") in INDEPENDENT_PHASE_CLASSES and not target.get("predicted_omega_used_in_extraction"):
        residual_reason = NONINDEPENDENT_TAU
    return {
        "target_independence": target,
        "tau_return_independence": tau,
        "has_raw_trajectory": raw,
        "sibling_trajectory_files": [str(path) for path in siblings],
        "residual_reason": residual_reason,
    }


def _center_mode(obj: dict[str, Any]) -> dict[str, Any]:
    dispersion = obj.get("dispersion")
    if not isinstance(dispersion, dict):
        return {}
    center = dispersion.get("center_mode")
    return center if isinstance(center, dict) else {}


def extract_accounting_frequencies(obj: dict[str, Any]) -> dict[str, Any]:
    center = _center_mode(obj)
    omega_center = _float_or_none(center.get("omega"))
    omega_source = "dispersion.center_mode.omega" if omega_center is not None else None
    if omega_center is None:
        omega_center = _float_or_none(obj.get("omega_median"))
        omega_source = "omega_median" if omega_center is not None else None
    omega_adv = _float_or_none(center.get("advective_frequency"))
    omega_intr = _float_or_none(center.get("omega_intrinsic"))
    split_source = "dispersion.center_mode"
    if omega_adv is None:
        omega_adv = _float_or_none(obj.get("advective_frequency_median"))
        split_source = "case_medians"
    if omega_intr is None:
        omega_intr = _float_or_none(obj.get("omega_intrinsic_median"))
        split_source = "case_medians" if omega_adv is not None else split_source
    return {
        "omega_center": omega_center,
        "omega_adv_closed": omega_adv,
        "omega_intr_closed": omega_intr,
        "omega_source": omega_source,
        "split_source": split_source,
        "k_ref_frequency_source": "reused_k_closed_center_mode",
        "k_ref_eigensolve": "not_performed_reanalysis_only",
    }


def extract_holonomy(obj: dict[str, Any]) -> dict[str, Any]:
    n = int(obj.get("n_runtime") if obj.get("n_runtime") is not None else 0)
    m = int(obj.get("m_runtime") if obj.get("m_runtime") is not None else 0)
    l_hat = float(obj["loop_length_over_core"])
    theta = float(obj.get("bishop_holonomy") or 0.0)
    record = holonomy_record(n, m, theta, l_hat)
    forbid_double_counted_holonomy(record)
    stored_k = _float_or_none(obj.get("k_hat"))
    record["stored_k_hat"] = stored_k
    record["stored_k_matches_k_closed"] = (
        stored_k is not None and abs(stored_k - float(record["k_closed"])) <= 1e-10 * (1.0 + abs(float(record["k_closed"])))
    )
    return record


def case_to_accounting_row(path: Path, obj: dict[str, Any]) -> dict[str, Any]:
    case_id = path.stem
    freqs = extract_accounting_frequencies(obj)
    hol = extract_holonomy(obj)
    delay = obj.get("delay") if isinstance(obj.get("delay"), dict) else {}
    phi_loop = _float_or_none(obj.get("loop_phase"))
    if phi_loop is None:
        phi_loop = _float_or_none(delay.get("loop_phase"))
    tau = _float_or_none(obj.get("tau_return"))
    if tau is None:
        tau = _float_or_none(delay.get("tau_return"))
    audit = classify_historical_independence(obj, case_path=path)
    omega_c = freqs["omega_center"]
    omega_adv = freqs["omega_adv_closed"]
    omega_intr = freqs["omega_intr_closed"]
    from .residual import account_nested, accounting_identity_status, sha256_obj

    evaluable = all(v is not None for v in (phi_loop, tau, omega_c, omega_adv, omega_intr))
    phi_envelope = envelope_phase_from_derived(phi_loop, omega_c, tau) if evaluable else None
    phi_carrier = carrier_derived_phase(phi_loop, phi_envelope) if evaluable else None
    accounts = (
        account_nested(
            omega_adv_ref=float(omega_adv),
            omega_intr_ref=float(omega_intr),
            omega_adv_closed=float(omega_adv),
            omega_intr_closed=float(omega_intr),
            tau_synthetic=float(tau),
            phi_null=0.0,
        )
        if evaluable
        else None
    )
    identity = accounting_identity_status(phi_carrier, accounts["ACCOUNT_M3"]) if evaluable else None
    lambda_real = _float_or_none((obj.get("swirl_clock") or {}).get("lambda_real") if isinstance(obj.get("swirl_clock"), dict) else None)
    lambda_imag = _float_or_none((obj.get("swirl_clock") or {}).get("lambda_imag") if isinstance(obj.get("swirl_clock"), dict) else None)
    if lambda_real is None:
        lambda_real = _float_or_none(obj.get("signed_growth_median"))
    if lambda_imag is None and omega_c is not None:
        lambda_imag = -float(omega_c)
    convention = convention_bridge(lambda_real, lambda_imag) if lambda_real is not None and lambda_imag is not None else None
    parent_hashes = {"case_sha256": sha256_file(path)}
    code_hash = sha256_obj({"module": "historical", "case_id": case_id})
    return {
        **identity_fields(case_id, parent_hashes, code_hash, record_type="phase_observation"),
        "case_id": case_id,
        "case_path": str(path),
        "status": obj.get("status"),
        "analysis_semantics": obj.get("analysis_semantics"),
        "carrier_group_token": opaque_token(obj.get("profile_name_runtime"), obj.get("m_runtime"), obj.get("n_runtime"), obj.get("axial_ratio_runtime")),
        "geometry_group_token": opaque_token(case_id, obj.get("loop_length_over_core"), obj.get("bishop_holonomy")),
        "phi_loop": phi_loop,
        "phi_envelope": phi_envelope,
        "phi_carrier_derived": phi_carrier,
        "tau_return_synthetic": tau,
        "tau_group": _float_or_none(obj.get("tau_group") if obj.get("tau_group") is not None else delay.get("tau_group")),
        "phase_uncertainty_rad": _float_or_none(obj.get("phase_uncertainty_rad") if obj.get("phase_uncertainty_rad") is not None else delay.get("phase_uncertainty_rad")),
        "phase_gate_valid": bool(obj.get("phase_gate_valid")),
        "delay_gate_valid": bool(obj.get("delay_gate_valid")),
        "evaluable_accounting": evaluable,
        "accounts": accounts,
        "accounting_identity": identity,
        "convention": convention,
        **freqs,
        **hol,
        **audit,
    }


def _relative_case_path(path: Path, relative_to: Path | str | None) -> str:
    if relative_to is None:
        return path.name
    try:
        return str(path.resolve().relative_to(Path(relative_to).resolve())).replace("\\", "/")
    except ValueError:
        return path.name


def load_historical_cases(paths: Iterable[Path], *, relative_to: Path | str | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []
    for path in paths:
        inventory.append(
            {
                "path": _relative_case_path(path, relative_to),
                "name": path.name,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
        obj = load_json_object(path)
        if obj is None or not is_analysis_case_record(obj):
            skipped.append({"path": str(path), "reason": "not_an_analysis_case"})
            continue
        rows.append(case_to_accounting_row(path, obj))
    return {"rows": rows, "skipped": skipped, "inventory": inventory}


def residual_status_from_rows(rows: list[dict[str, Any]]) -> tuple[str, list[str]]:
    from .residual import MISSING_CASES, NO_INDEPENDENT_PHASE, NONINDEPENDENT_TAU

    if not rows:
        return MISSING_CASES, []
    reasons = {row.get("residual_reason") for row in rows}
    secondary: list[str] = []
    if any(reason == "EVALUABLE" for reason in reasons):
        return "EVALUABLE", []
    if any(row.get("target_independence", {}).get("class") in INDEPENDENT_PHASE_CLASSES for row in rows):
        status = NONINDEPENDENT_TAU
        if any(row.get("tau_return_independence", {}).get("class") != "raw_trajectory_phase_blind" for row in rows):
            secondary.append(NONINDEPENDENT_TAU)
        return status, secondary
    status = NO_INDEPENDENT_PHASE
    if all(row.get("tau_return_independence", {}).get("class") != "raw_trajectory_phase_blind" for row in rows):
        secondary.append(NONINDEPENDENT_TAU)
    return status, secondary


def accounting_status_from_rows(rows: list[dict[str, Any]]) -> str:
    from .residual import ACCOUNTING_FAIL, ACCOUNTING_OK, MISSING_CASES

    identities = [row.get("accounting_identity") for row in rows if row.get("evaluable_accounting")]
    if not identities:
        return ACCOUNTING_FAIL if rows else MISSING_CASES
    return ACCOUNTING_OK if all(item == ACCOUNTING_OK for item in identities) else ACCOUNTING_FAIL


def sibling_version_counts(family_root: Path) -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for name in ("A029-v0.1.0", "A029-v0.1.1", "A029-v0.1.2", "A029-v0.2.0", "A029-v0.3.0", "A029-v0.4.0"):
        root = family_root / name / "outputs"
        n = len(list(root.glob("**/blind/cases/*.json"))) if root.is_dir() else 0
        counts[name] = {"n_blind_case_json": n, "outputs_present": root.is_dir()}
    archive = family_root / V012_ARCHIVE_NAME
    if archive.is_file():
        counts["v0.1.2_archive"] = {
            "present": True,
            "name": archive.name,
            "sha256": sha256_file(archive),
            "size": archive.stat().st_size,
        }
    else:
        counts["v0.1.2_archive"] = {"present": False, "name": V012_ARCHIVE_NAME}
    return counts


def rows_to_tables(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    phase_contract = []
    dispersion_contract = []
    return_time_contract = []
    predictor_inputs = []
    predictions = []
    summary = []
    for row in rows:
        accounts = row.get("accounts") or {}
        phase_contract.append(
            {
                "case_id": row["case_id"],
                "carrier_group_token": row["carrier_group_token"],
                "geometry_group_token": row["geometry_group_token"],
                "phi_loop": row["phi_loop"],
                "phi_envelope": row["phi_envelope"],
                "phi_carrier_derived": row["phi_carrier_derived"],
                "target_independence_class": row["target_independence"]["class"],
                "phase_uncertainty_rad": row["phase_uncertainty_rad"],
            }
        )
        dispersion_contract.append(
            {
                "case_id": row["case_id"],
                "k_ref": row["k_ref"],
                "k_closed": row["k_closed"],
                "stored_k_hat": row["stored_k_hat"],
                "L_hat": row["L_hat"],
                "m": row["m"],
                "n": row["n"],
                "theta_B": row["theta_B"],
                "holonomy_representation": row["holonomy_representation"],
                "phi_holonomy_explicit": row["phi_holonomy_explicit"],
                "omega_center": row["omega_center"],
                "omega_adv_closed": row["omega_adv_closed"],
                "omega_intr_closed": row["omega_intr_closed"],
                "k_ref_eigensolve": row["k_ref_eigensolve"],
                "k_ref_frequency_source": row["k_ref_frequency_source"],
            }
        )
        return_time_contract.append(
            {
                "case_id": row["case_id"],
                "tau_return_synthetic": row["tau_return_synthetic"],
                "tau_group": row["tau_group"],
                "tau_return_independence_class": row["tau_return_independence"]["class"],
                "synthetic_wavepacket_used": row["tau_return_independence"]["synthetic_wavepacket_used"],
            }
        )
        predictor_inputs.append(
            {
                "case_id": row["case_id"],
                "carrier_group_token": row["carrier_group_token"],
                "omega_adv_closed": row["omega_adv_closed"],
                "omega_intr_closed": row["omega_intr_closed"],
                "tau_return_synthetic": row["tau_return_synthetic"],
                "k_ref": row["k_ref"],
                "k_closed": row["k_closed"],
            }
        )
        predictions.append(
            {
                "case_id": row["case_id"],
                "carrier_group_token": row["carrier_group_token"],
                "ACCOUNT_M0": accounts.get("ACCOUNT_M0"),
                "ACCOUNT_M1": accounts.get("ACCOUNT_M1"),
                "ACCOUNT_M2": accounts.get("ACCOUNT_M2"),
                "ACCOUNT_M3": accounts.get("ACCOUNT_M3"),
                "scientific_pred_scored": False,
            }
        )
        summary.append(
            {
                "case_id": row["case_id"],
                "evaluable_accounting": row["evaluable_accounting"],
                "accounting_identity": row["accounting_identity"],
                "residual_reason": row["residual_reason"],
                "phi_carrier_derived": row["phi_carrier_derived"],
                "ACCOUNT_M3": accounts.get("ACCOUNT_M3"),
                "stored_k_matches_k_closed": row["stored_k_matches_k_closed"],
            }
        )
    return {
        "phase_contract": phase_contract,
        "dispersion_contract": dispersion_contract,
        "return_time_contract": return_time_contract,
        "phase_predictor_inputs": predictor_inputs,
        "blind_phase_predictions": predictions,
        "phase_decomposition_summary": summary,
    }
