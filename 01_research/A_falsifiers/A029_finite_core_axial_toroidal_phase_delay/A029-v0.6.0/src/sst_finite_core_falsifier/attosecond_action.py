"""A029 v0.5.0: physically qualified phase-delay -> specific-action producer.

The central rule is deliberately conservative: an existing dimensionless modal
phase, loop phase, eigenfrequency, or dimensionless return time is NOT promoted
to a physical action merely because it looks phase-like. A physical SI scale and
an independently derived action integrand are required.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any

import numpy as np


CLEAN_FLAGS = (
    "depends_on_h",
    "depends_on_hbar",
    "depends_on_compton_radius",
    "depends_on_electron_mass",
    "depends_on_alpha",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def provenance_clean(meta: dict) -> tuple[bool, list[str]]:
    reasons = []
    if meta.get("physical_scale_status") != "INDEPENDENT_PHYSICAL_SCALE":
        reasons.append("physical_scale_status must be INDEPENDENT_PHYSICAL_SCALE")
    for key in CLEAN_FLAGS:
        if bool(meta.get(key, True)):
            reasons.append(f"{key} must be false")
    if int(meta.get("free_attosecond_phase_fit_parameters", -1)) != 0:
        reasons.append("free_attosecond_phase_fit_parameters must equal 0")
    return (not reasons), reasons


def effective_parcel_specific_lagrangian(velocity_m_s, pressure_Pa, rho_f_kg_m3: float) -> np.ndarray:
    """Effective material-parcel diagnostic ℓ_eff = |v|^2/2 - p/rho_f.

    Units are m^2/s^2. This reproduces the pressure-gradient force for a
    parcel moving in a *prescribed* pressure field. It is not asserted to be
    the complete constrained Euler-field action; incompressibility constraints
    and self-consistent pressure remain part of the upstream fluid solver.
    """
    rho = float(rho_f_kg_m3)
    if not np.isfinite(rho) or rho <= 0.0:
        raise ValueError("rho_f_kg_m3 must be positive and finite")
    v = np.asarray(velocity_m_s, dtype=float)
    p = np.asarray(pressure_Pa, dtype=float)
    if v.shape[:-1] != p.shape or v.shape[-1] != 3:
        raise ValueError("velocity_m_s must have shape (...,3) and pressure_Pa shape (...)")
    speed2 = np.sum(v*v, axis=-1)
    return 0.5*speed2 - p/rho


def delta_specific_lagrangian_from_euler_fields(
    velocity_candidate_m_s, pressure_candidate_Pa,
    velocity_reference_m_s, pressure_reference_Pa,
    rho_f_kg_m3: float,
) -> np.ndarray:
    """Candidate-minus-reference effective parcel Lagrangian difference."""
    lc = effective_parcel_specific_lagrangian(velocity_candidate_m_s, pressure_candidate_Pa, rho_f_kg_m3)
    lr = effective_parcel_specific_lagrangian(velocity_reference_m_s, pressure_reference_Pa, rho_f_kg_m3)
    return lc-lr


def cumulative_specific_action(t_s, delta_specific_lagrangian_m2_s2) -> np.ndarray:
    """Compute δs(t)=∫δℓ dt, with [δs]=m²/s.

    This operation is valid only if the supplied δℓ is already a physically
    derived mass-specific Lagrangian difference. This function does not assert
    that any particular A029 eigenmode observable is such a Lagrangian.
    """
    t = np.asarray(t_s, dtype=float)
    q = np.asarray(delta_specific_lagrangian_m2_s2, dtype=float)
    if t.ndim != 1 or len(t) < 2 or not np.all(np.diff(t) > 0):
        raise ValueError("t_s must be a strictly increasing 1D array")
    if q.ndim == 1:
        q = q[None, :]
    if q.ndim != 2 or q.shape[1] != len(t):
        raise ValueError("delta_specific_lagrangian_m2_s2 must have shape (n_samples,n_t)")
    if not np.all(np.isfinite(q)) or not np.all(np.isfinite(t)):
        raise ValueError("timeseries must be finite")
    dt = np.diff(t)
    trap = 0.5 * (q[:, 1:] + q[:, :-1]) * dt[None, :]
    out = np.zeros_like(q)
    out[:, 1:] = np.cumsum(trap, axis=1)
    return out


def stationary_delay_action(specific_energy_m2_s2, delta_t_s) -> np.ndarray:
    """Conditional stationary-channel relation δs=-ε δt.

    This is dimensionally correct but is not automatically promoted to the
    fully qualified producer status; the caller must provide an independent
    derivation establishing this stationary-channel mapping for the model.
    """
    e = np.asarray(specific_energy_m2_s2, dtype=float)
    dt = np.asarray(delta_t_s, dtype=float)
    if e.shape != dt.shape:
        raise ValueError("specific_energy_m2_s2 and delta_t_s must have the same shape")
    return -e * dt


def existing_modal_phase_classification(record: dict) -> dict:
    """Classify a current A029 phase/delay record without over-promoting it."""
    phase_keys = [k for k in ("loop_phase", "phi_target_independent", "phase_residual") if k in record]
    time_keys = [k for k in ("tau_return", "tau_group", "tau_return_independent") if k in record]
    return {
        "status": "DIMENSIONLESS_MODAL_PHASE_ONLY",
        "qualifies_as_specific_action": False,
        "phase_fields_seen": phase_keys,
        "time_fields_seen": time_keys,
        "reason": (
            "A029-v0.4.0 modal phase/delay fields are not, by themselves, an SI action difference. "
            "A physical action integrand or separately derived energy-delay relation is required."
        ),
    }


def _relative_rms(a: np.ndarray) -> tuple[np.ndarray, float, float]:
    if a.ndim == 1:
        a = a[None, :]
    rel = a - np.mean(a, axis=1, keepdims=True)
    rms = np.sqrt(np.mean(rel*rel, axis=1))
    return rms, float(np.median(rms)), float(np.max(rms))


def export_from_contract_file(contract_path: str | Path, out_dir: str | Path, config: dict | None = None) -> dict:
    contract_path = Path(contract_path).resolve()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg = config or {}
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    mode = str(contract.get("mode", ""))
    meta = dict(contract.get("provenance", {}))
    clean, reasons = provenance_clean(meta)
    gates = {
        "A29A1_PHYSICAL_SCALE_PROVENANCE": {
            "status": "PASS" if clean else "INVALID",
            "reasons": reasons,
        },
        "A29A2_SPECIFIC_ACTION_DIMENSIONAL_CLOSURE": {"status": "NOT_RUN"},
        "A29A3_MODAL_PHASE_NONPROMOTION": {
            "status": "PASS",
            "rule": "dimensionless A029 loop/eigen phase is never directly relabeled as SI action",
        },
        "A29A4_RELATIVE_ACTION_STRUCTURE": {"status": "NOT_RUN"},
        "A29A5_EXPORT_SEAL": {"status": "NOT_RUN"},
    }
    if not clean:
        result = {"status": "INVALID_PROVENANCE", "mode": mode, "gates": gates, "provenance": meta}
        _write_json(out/"attosecond_action_export.json", result)
        return result

    npz_ref = contract.get("npz")
    if not npz_ref:
        result = {"status": "NOT_RUN", "reason": "contract has no npz field", "mode": mode, "gates": gates}
        _write_json(out/"attosecond_action_export.json", result)
        return result
    inp = (contract_path.parent / npz_ref).resolve()
    if not inp.exists():
        result = {"status": "NOT_RUN", "reason": f"input NPZ not found: {inp}", "mode": mode, "gates": gates}
        _write_json(out/"attosecond_action_export.json", result)
        return result

    with np.load(inp, allow_pickle=False) as z:
        d = {k: np.asarray(z[k]) for k in z.files}

    qualification = ""
    if mode == "specific_lagrangian_timeseries":
        if "t_s" not in d or "delta_specific_lagrangian_m2_s2" not in d:
            raise ValueError("specific_lagrangian_timeseries requires t_s and delta_specific_lagrangian_m2_s2")
        delta_s = cumulative_specific_action(d["t_s"], d["delta_specific_lagrangian_m2_s2"])
        qualification = "DERIVED_SPECIFIC_ACTION"
        dimensional_equation = "(m^2/s^2)*s = m^2/s"
    elif mode == "stationary_delay_energy":
        if "specific_energy_m2_s2" not in d or "delta_t_s" not in d:
            raise ValueError("stationary_delay_energy requires specific_energy_m2_s2 and delta_t_s")
        delta_s = stationary_delay_action(d["specific_energy_m2_s2"], d["delta_t_s"])
        # Dimensionally valid, but only fully qualified if the contract explicitly
        # certifies an independent derivation of the stationary-channel relation.
        if contract.get("stationary_relation_status") == "INDEPENDENTLY_DERIVED":
            qualification = "DERIVED_SPECIFIC_ACTION"
        else:
            qualification = "CONDITIONAL_SPECIFIC_ACTION"
        dimensional_equation = "(m^2/s^2)*s = m^2/s"
    elif mode == "dimensionless_modal_phase_only":
        result = {
            "status": "DIMENSIONLESS_MODAL_PHASE_ONLY",
            "mode": mode,
            "gates": gates,
            "reason": "No SI specific action is exported from a dimensionless modal phase alone.",
        }
        _write_json(out/"attosecond_action_export.json", result)
        return result
    else:
        raise ValueError(f"unsupported mode: {mode}")

    if delta_s.ndim == 1:
        delta_s = delta_s[None, :]
    gates["A29A2_SPECIFIC_ACTION_DIMENSIONAL_CLOSURE"] = {
        "status": "PASS",
        "equation": dimensional_equation,
        "output_units": "m^2/s",
    }
    rms, med, mx = _relative_rms(delta_s)
    floor = float(cfg.get("relative_specific_action_rms_floor_m2_s", 0.0))
    gates["A29A4_RELATIVE_ACTION_STRUCTURE"] = {
        "status": "PASS" if med > floor else "GLOBAL_OR_CONSTANT_ACTION_ONLY",
        "median_relative_specific_action_rms_m2_s": med,
        "max_relative_specific_action_rms_m2_s": mx,
        "floor_m2_s": floor,
    }

    export_npz = out/"sst_specific_action_field.npz"
    payload = {"delta_specific_action_m2_s": delta_s}
    for key in ("t_s", "energy_eV", "theta_rad", "delay_s", "direction", "sample_id"):
        if key in d:
            payload[key] = d[key]
    np.savez(export_npz, **payload)

    export_meta = {
        "schema": "A029-ATTOS-ACTION-PRODUCER-1.0",
        "status": qualification,
        "source_model": "A029-v0.5.0",
        "source_contract": str(contract_path),
        "source_npz_sha256": _sha256(inp),
        "free_phase_fit_parameters": 0,
        "mapping_to_attosecond_kernel": "NOT_YET_SUPPLIED_BY_A029",
        **{k: bool(meta.get(k, True)) for k in CLEAN_FLAGS},
        "note": (
            "This export supplies an SST specific-action field only. A separate, frozen physical map "
            "from the A029 state variables to the orthodox attosecond kernel coordinates is still required."
        ),
    }
    meta_path = out/"action_provenance.json"
    _write_json(meta_path, export_meta)
    gates["A29A5_EXPORT_SEAL"] = {
        "status": "PASS",
        "specific_action_npz_sha256": _sha256(export_npz),
        "provenance_json_sha256": _sha256(meta_path),
    }
    result = {
        "status": qualification,
        "mode": mode,
        "specific_action_npz": str(export_npz),
        "action_provenance_json": str(meta_path),
        "gates": gates,
        "important_boundary": (
            "A029 does not produce the orthodox Volkov/SFA kernel and does not infer a photoionization phase from its legacy loop_phase field."
        ),
    }
    _write_json(out/"attosecond_action_export.json", result)
    return result
