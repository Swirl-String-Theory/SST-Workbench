"""Rebuild and seal A029 (q_m, p_m) before any C006 trajectory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import eig

from .measure import block_measure, cylindrical_weights, weighted_inner
from .paths import a029_v020_root, complex_hash, ensure_a029_import, load_thresholds, sha256_obj


SAME_BRANCH = "RECONSTRUCTED_SAME_BRANCH"
INDETERMINATE = "INDETERMINATE_MODE_RECONSTRUCTION"


def _case_mode(case: dict[str, Any]) -> dict[str, Any]:
    levels = case.get("eigen_convergence", {}).get("levels") or []
    if not levels:
        raise ValueError("frozen case has no eigen_convergence.levels")
    return dict(levels[-1]["mode"])


def _rel_ok(value: float, ref: float, rel: float, abs_floor: float = 1e-12) -> bool:
    return abs(float(value) - float(ref)) <= float(rel) * max(abs(float(ref)), abs_floor)


def match_frozen_scalars(mode: dict[str, Any], frozen: dict[str, Any], thr: dict[str, Any]) -> dict[str, Any]:
    lam = complex(mode["lambda"])
    fr = frozen["lambda"]
    frozen_lam = complex(float(fr["real"]), float(fr["imag"]))
    checks = {
        "omega": _rel_ok(mode["omega"], frozen["omega"], thr["omega_rel_tol"]),
        "omega_intrinsic": _rel_ok(mode["omega_intrinsic"], frozen["omega_intrinsic"], thr["omega_intrinsic_rel_tol"]),
        "growth": abs(float(mode["growth"]) - float(frozen["growth"])) <= thr["growth_abs_tol"],
        "lambda_real": abs(lam.real - frozen_lam.real) <= thr["lambda_real_abs_tol"],
        "lambda_imag": _rel_ok(lam.imag, frozen_lam.imag, thr["lambda_imag_rel_tol"]),
        "core_localization": abs(float(mode["core_localization"]) - float(frozen["core_localization"])) <= thr["localization_abs_tol"],
        "axial_energy_fraction": abs(float(mode["axial_energy_fraction"]) - float(frozen["axial_energy_fraction"])) <= thr["axial_energy_abs_tol"],
        "hybrid_score": abs(float(mode["hybrid_score"]) - float(frozen["hybrid_score"])) <= thr["hybrid_abs_tol"],
        "residual": float(mode["residual"]) <= thr["residual_max"],
    }
    return {"ok": all(checks.values()), "checks": checks}


def left_eigenvector(A, B, lam, q) -> np.ndarray:
    vals, vl, vr = eig(A, B, left=True, right=True)
    idx = int(np.argmin(np.abs(vals - complex(lam))))
    if abs(vals[idx] - complex(lam)) > 1e-6 * max(abs(complex(lam)), 1.0):
        # fall back: nearest right-column match then same index on left
        idx_r = int(np.argmin([np.linalg.norm(vr[:, j] - q) for j in range(vr.shape[1])]))
        idx = idx_r
    return np.asarray(vl[:, idx], dtype=complex)


def normalize_biorthogonal(p, q, weights, mass) -> tuple[np.ndarray, complex]:
    raw = weighted_inner(p, q, weights, mass)
    if abs(raw) < 1e-14:
        return np.asarray(p, dtype=complex), complex(raw)
    p = np.asarray(p, dtype=complex) / raw
    residual = weighted_inner(p, q, weights, mass) - 1.0
    return p, residual


def reconstruct_mode(carrier_id: str | None = None, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_a029_import()
    from sst_finite_core_falsifier.delay import loop_wavenumber
    from sst_finite_core_falsifier.eigen import build_generalized, select_hybrid_mode, solve_spectrum
    from sst_finite_core_falsifier.geometry import geometry_stats
    from sst_finite_core_falsifier.model import load_candidate

    thr_all = thresholds or load_thresholds()
    thr = thr_all["mode_reconstruction"]
    token = str(carrier_id or thr_all["bridge_qualification_carrier_id"])
    npz = a029_v020_root() / "outputs" / "basic" / "campaign" / "blind_catalog" / "geometry" / f"{token}.npz"
    case_path = a029_v020_root() / "outputs" / "basic" / "blind" / "cases" / f"{token}.json"
    cand = load_candidate(npz)
    case = json.loads(case_path.read_text(encoding="utf-8"))
    gs = geometry_stats(cand.components)
    Lhat = float(gs["length_total"] / cand.core_fraction)
    hol = float(gs["bishop_holonomy_mean"])
    k_hat = loop_wavenumber(Lhat, cand.m, cand.n, hol, float(cand.closure_offset))
    radial_n = int(thr["radial_n"])
    spec = solve_spectrum(cand.profile_name, cand.axial_ratio, cand.m, k_hat, radial_n, cand.rmax)
    mode = select_hybrid_mode(spec)
    if mode is None:
        rec = {
            "schema": "SST_MODE_RECONSTRUCTION-1.0",
            "schema_version": "1.0",
            "record_type": "mode_reconstruction",
            "status": INDETERMINATE,
            "carrier_id": token,
            "reason": "no hybrid mode",
            "q_hash": "0" * 64,
            "p_hash": "0" * 64,
            "biorthogonality_residual": float("nan"),
        }
        return {"record": rec, "q": None, "p": None, "candidate": cand}
    r, _re, _U, _V, _adv, A, B = build_generalized(
        cand.profile_name, cand.axial_ratio, cand.m, k_hat, radial_n, cand.rmax
    )
    w_r = cylindrical_weights(r, cand.rmax)
    W = block_measure(w_r, 4)
    q = np.asarray(mode["vector"], dtype=complex)
    p = left_eigenvector(A, B, mode["lambda"], q)
    p, bio = normalize_biorthogonal(p, q, W, B)
    frozen = _case_mode(case)
    match = match_frozen_scalars(mode, frozen, thr)
    status = SAME_BRANCH if match["ok"] and abs(bio) <= thr["biorthogonality_residual_max"] else INDETERMINATE
    if abs(int(cand.m)) != 1:
        status = INDETERMINATE
    record = {
        "schema": "SST_MODE_RECONSTRUCTION-1.0",
        "schema_version": "1.0",
        "record_type": "mode_reconstruction",
        "status": status,
        "carrier_id": token,
        "q_hash": complex_hash(q),
        "p_hash": complex_hash(p),
        "biorthogonality_residual": float(abs(bio)),
        "k_hat": float(k_hat),
        "L_hat": float(Lhat),
        "theta_B": float(hol),
        "m": int(cand.m),
        "n": int(cand.n),
        "profile_name": cand.profile_name,
        "axial_ratio": float(cand.axial_ratio),
        "core_fraction": float(cand.core_fraction),
        "rmax": float(cand.rmax),
        "radial_n": radial_n,
        "omega": float(mode["omega"]),
        "omega_intrinsic": float(mode["omega_intrinsic"]),
        "growth": float(mode["growth"]),
        "core_localization": float(mode["core_localization"]),
        "axial_energy_fraction": float(mode["axial_energy_fraction"]),
        "hybrid_score": float(mode["hybrid_score"]),
        "residual": float(mode["residual"]),
        "match": match,
        "prediction_inputs_consumed": [],
    }
    record["certificate_sha256"] = sha256_obj({k: record[k] for k in record if k != "certificate_sha256"})
    sealed = {
        "q": q,
        "p": p,
        "r": r,
        "A": A,
        "B": B,
        "W": W,
        "w_radial": w_r,
        "candidate": cand,
        "geometry_stats": gs,
        "record": record,
    }
    return sealed


def wr_convergence_gate(sealed: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_a029_import()
    from sst_finite_core_falsifier.eigen import build_generalized, select_hybrid_mode, solve_spectrum

    thr_all = thresholds or load_thresholds()
    cand = sealed["candidate"]
    k_hat = float(sealed["record"]["k_hat"])
    omegas = []
    bios = []
    for N in thr_all["measure"]["radial_ladder"]:
        spec = solve_spectrum(cand.profile_name, cand.axial_ratio, cand.m, k_hat, int(N), cand.rmax)
        mode = select_hybrid_mode(spec)
        if mode is None:
            return {"ok": False, "reason": f"no mode at radial_n={N}"}
        r, _re, _U, _V, _adv, A, B = build_generalized(
            cand.profile_name, cand.axial_ratio, cand.m, k_hat, int(N), cand.rmax
        )
        W = block_measure(cylindrical_weights(r, cand.rmax), 4)
        q = np.asarray(mode["vector"], dtype=complex)
        p, bio = normalize_biorthogonal(left_eigenvector(A, B, mode["lambda"], q), q, W, B)
        omegas.append(float(mode["omega"]))
        bios.append(float(abs(bio)))
    span = float(np.ptp(omegas) / max(abs(np.median(omegas)), 1e-6)) if omegas else float("inf")
    ok = span <= float(thr_all["wr_convergence_rel_tol"]) and max(bios) <= thr_all["mode_reconstruction"]["biorthogonality_residual_max"]
    return {"ok": bool(ok), "omega": omegas, "biorthogonality": bios, "omega_rel_span": span}


def write_certificate(sealed: dict[str, Any], path: Path) -> dict[str, Any]:
    rec = dict(sealed["record"])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rec
