"""A042 v0.3.0: target-blind action -> attosecond phase -> intensity bridge.

This module deliberately contains no CODATA h or hbar target. The reduced
specific-action scale is reconstructed from the already-blind QGI result:
    (hbar/m)_QGI = (h/m)_QGI / (2*pi).
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
from typing import Any

import numpy as np


REQUIRED_CLEAN_FLAGS = (
    "depends_on_h",
    "depends_on_hbar",
    "depends_on_compton_radius",
    "depends_on_electron_mass",
    "depends_on_alpha",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dump_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _status(status: str, **kwargs) -> dict:
    return {"status": status, **kwargs}


def producer_provenance_ok(meta: dict) -> tuple[bool, list[str]]:
    reasons = []
    if meta.get("status") != "DERIVED_SPECIFIC_ACTION":
        reasons.append("status must be DERIVED_SPECIFIC_ACTION")
    if int(meta.get("free_phase_fit_parameters", -1)) != 0:
        reasons.append("free_phase_fit_parameters must equal 0")
    if meta.get("mapping_to_attosecond_kernel") != "PHYSICALLY_DERIVED_AND_FROZEN":
        reasons.append("mapping_to_attosecond_kernel must be PHYSICALLY_DERIVED_AND_FROZEN")
    for key in REQUIRED_CLEAN_FLAGS:
        if bool(meta.get(key, True)):
            reasons.append(f"{key} must be false")
    return (not reasons), reasons


def _load_bundle(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        d = {k: np.asarray(z[k]) for k in z.files}
    required = ("kernel_re", "kernel_im", "weights", "delta_specific_action_m2_s")
    missing = [k for k in required if k not in d]
    if missing:
        raise ValueError(f"action_kernel_bundle.npz missing arrays: {missing}")
    k = np.asarray(d["kernel_re"], float) + 1j * np.asarray(d["kernel_im"], float)
    if k.ndim == 1:
        k = k[None, :]
    ds = np.asarray(d["delta_specific_action_m2_s"], float)
    if ds.ndim == 1:
        ds = ds[None, :]
    w = np.asarray(d["weights"], float)
    if ds.shape != k.shape:
        raise ValueError("delta_specific_action_m2_s must match kernel shape")
    if w.ndim != 1 or len(w) != k.shape[1]:
        raise ValueError("weights must match kernel integration axis")
    if not np.all(np.isfinite(k.real)) or not np.all(np.isfinite(k.imag)):
        raise ValueError("kernel contains non-finite values")
    if not np.all(np.isfinite(ds)) or not np.all(np.isfinite(w)):
        raise ValueError("bundle contains non-finite action/weight values")
    d["kernel"] = k
    d["delta_specific_action_m2_s"] = ds
    d["weights"] = w
    return d


def _forward(kernel: np.ndarray, weights: np.ndarray, phase: np.ndarray) -> dict[str, np.ndarray]:
    kw = kernel * weights[None, :]
    m0 = np.sum(kw, axis=1)
    m1 = np.sum(kw * np.exp(1j * phase), axis=1)
    dm = 1j * np.sum(kw * phase, axis=1)
    i0 = np.abs(m0) ** 2
    i1 = np.abs(m1) ** 2
    di_lin = 2.0 * np.real(np.conjugate(m0) * dm)
    return {"M0": m0, "M1": m1, "I0": i0, "I1": i1, "dI_exact": i1-i0, "dI_linear": di_lin}


def _relative_phase(phase: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    aw = np.abs(weights)
    sw = float(np.sum(aw))
    if sw <= 0.0:
        raise ValueError("absolute integration weights sum to zero")
    mean = np.sum(phase * aw[None, :], axis=1) / sw
    rel = phase - mean[:, None]
    rms = np.sqrt(np.sum(rel * rel * aw[None, :], axis=1) / sw)
    return rel, rms


def _global_null(kernel: np.ndarray, weights: np.ndarray, probe_rad: float) -> float:
    p = np.full(kernel.shape, float(probe_rad), dtype=float)
    r = _forward(kernel, weights, p)
    rel = np.abs(r["I1"] - r["I0"]) / np.maximum(r["I0"], 1e-300)
    return float(np.max(rel))


def run_attosecond_bridge_gate(project_root: Path, cfg: dict, *, qgi: dict, mode: str) -> dict:
    root = Path(project_root)
    acfg = cfg.get("attosecond_bridge", {})
    bundle_path = root / acfg.get("bundle_npz", "data/attosecond/prepared/action_kernel_bundle.npz")
    meta_path = root / acfg.get("provenance_json", "data/attosecond/prepared/action_provenance.json")
    out = root / f"{cfg['project_name']}-outputs" / "blind" / "attosecond_bridge"
    out.mkdir(parents=True, exist_ok=True)

    base_gates = {
        "G13_ATTOS_ACTION_PRODUCER_PROVENANCE": _status("NOT_RUN"),
        "G14_TARGET_BLIND_ACTION_TO_PHASE": _status("NOT_RUN"),
        "G15_GLOBAL_PHASE_NULL": _status("NOT_RUN"),
        "G16_RELATIVE_PHASE_OBSERVABILITY": _status("NOT_RUN"),
        "G17_FORWARD_MODEL_SEAL": _status("NOT_RUN"),
    }

    if not bundle_path.exists() or not meta_path.exists():
        result = {
            "status": "NOT_RUN",
            "reason": "Prepared attosecond action/kernel bundle is not available; no synthetic data are substituted.",
            "bundle_path": str(bundle_path.relative_to(root)) if bundle_path.is_relative_to(root) else str(bundle_path),
            "provenance_path": str(meta_path.relative_to(root)) if meta_path.is_relative_to(root) else str(meta_path),
            "gates": base_gates,
        }
        _dump_json(out / f"attosecond_bridge_{mode}.json", result)
        return result

    meta = _load_json(meta_path)
    clean, reasons = producer_provenance_ok(meta)
    base_gates["G13_ATTOS_ACTION_PRODUCER_PROVENANCE"] = _status(
        "PASS" if clean else "INVALID",
        reasons=reasons,
        source_model=meta.get("source_model"),
        free_phase_fit_parameters=meta.get("free_phase_fit_parameters"),
    )
    if not clean:
        result = {"status": "INVALID_PROVENANCE", "gates": base_gates, "producer": meta}
        _dump_json(out / f"attosecond_bridge_{mode}.json", result)
        return result

    if not qgi.get("available") or qgi.get("h_over_m_m2_s") in (None, ""):
        base_gates["G14_TARGET_BLIND_ACTION_TO_PHASE"] = _status(
            "NOT_RUN", reason="QGI-specific action is unavailable."
        )
        result = {"status": "NOT_RUN_QGI_SCALE", "gates": base_gates, "producer": meta}
        _dump_json(out / f"attosecond_bridge_{mode}.json", result)
        return result

    b = _load_bundle(bundle_path)
    reduced_specific_action = float(qgi["h_over_m_m2_s"]) / (2.0 * math.pi)
    if reduced_specific_action <= 0.0 or not math.isfinite(reduced_specific_action):
        raise ValueError("QGI h/m must imply positive finite hbar/m")
    phase = b["delta_specific_action_m2_s"] / reduced_specific_action
    base_gates["G14_TARGET_BLIND_ACTION_TO_PHASE"] = _status(
        "PASS",
        reduced_specific_action_m2_s=reduced_specific_action,
        dimensional_identity="(m^2/s)/(m^2/s)=1",
        planck_target_used=False,
        mass_used=False,
    )

    null_rel = _global_null(b["kernel"], b["weights"], float(acfg.get("global_phase_probe_rad", 0.731)))
    null_thr = float(acfg.get("global_phase_null_rel_max", 1e-12))
    base_gates["G15_GLOBAL_PHASE_NULL"] = _status(
        "PASS" if null_rel <= null_thr else "FAIL",
        max_relative_intensity_change=null_rel,
        threshold=null_thr,
    )

    rel_phase, rel_rms = _relative_phase(phase, b["weights"])
    obs_floor = float(acfg.get("relative_phase_rms_floor_rad", 1e-12))
    med_rms = float(np.median(rel_rms))
    base_gates["G16_RELATIVE_PHASE_OBSERVABILITY"] = _status(
        "PASS" if med_rms > obs_floor else "NULL_PREDICTION",
        median_relative_phase_rms_rad=med_rms,
        max_relative_phase_rms_rad=float(np.max(rel_rms)),
        floor_rad=obs_floor,
        note="A phase that is constant over the coherent integration coordinate is intensity-null.",
    )

    fw = _forward(b["kernel"], b["weights"], phase)
    max_phase = float(np.max(np.abs(phase)))
    lin_limit = float(acfg.get("linearization_phase_max_rad", 0.05))
    if max_phase <= lin_limit:
        denom = max(float(np.linalg.norm(fw["dI_exact"])), 1e-300)
        linear_rel = float(np.linalg.norm(fw["dI_exact"]-fw["dI_linear"]) / denom)
        linear_state = "QUALIFIED_SMALL_PHASE"
    else:
        linear_rel = None
        linear_state = "NONPERTURBATIVE_USE_EXACT_ONLY"

    bundle_hash = _sha256_file(bundle_path)
    meta_hash = _sha256_file(meta_path)
    base_gates["G17_FORWARD_MODEL_SEAL"] = _status(
        "PASS",
        bundle_sha256=bundle_hash,
        provenance_sha256=meta_hash,
        free_phase_fit_parameters=0,
        exact_forward_model=True,
    )

    rows = []
    n = len(fw["I0"])
    for i in range(n):
        row = {
            "sample_index": i,
            "I_orthodox": float(fw["I0"][i]),
            "I_sst_exact": float(fw["I1"][i]),
            "delta_I_exact": float(fw["dI_exact"][i]),
            "delta_I_linear": float(fw["dI_linear"][i]),
            "relative_phase_rms_rad": float(rel_rms[i]),
        }
        for key in ("energy_eV", "theta_rad", "delay_s", "direction"):
            if key in b and np.asarray(b[key]).ndim == 1 and len(b[key]) == n:
                val = np.asarray(b[key])[i]
                row[key] = float(val) if np.issubdtype(np.asarray(b[key]).dtype, np.number) else str(val)
        rows.append(row)

    # JSON only here; CSV is generated by the parent analysis when desired.
    prediction_path = out / f"attosecond_prediction_{mode}.json"
    _dump_json(prediction_path, {"rows": rows})
    result = {
        "status": "READY",
        "producer": meta,
        "qgi_scale_source_grade": qgi.get("source_grade"),
        "reduced_specific_action_m2_s": reduced_specific_action,
        "phase": {
            "max_abs_rad": max_phase,
            "median_relative_rms_rad": med_rms,
            "max_relative_rms_rad": float(np.max(rel_rms)),
        },
        "linearization": {
            "status": linear_state,
            "max_abs_phase_rad": max_phase,
            "limit_rad": lin_limit,
            "relative_exact_vs_linear_deltaI": linear_rel,
        },
        "prediction_file": str(prediction_path.relative_to(root)),
        "gates": base_gates,
    }
    _dump_json(out / f"attosecond_bridge_{mode}.json", result)
    return result
