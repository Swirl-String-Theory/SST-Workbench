from __future__ import annotations

from typing import Any

from .io import ffloat, fbool


def energy_ledger_audit(rows: list[dict[str, str]], rel_tol: float) -> list[dict[str, Any]]:
    channels = ["delta_E_CM_eV", "delta_E_rot_eV", "delta_E_kelvin_eV", "delta_E_twist_eV", "delta_E_core_eV"]
    out = []
    for r in rows:
        ch_sum = sum((ffloat(r, c, 0.0) or 0.0) for c in channels)
        drift = ffloat(r, "total_energy_drift_eV", 0.0) or 0.0
        e0 = abs(ffloat(r, "initial_total_energy_eV", 0.0) or 0.0)
        rel = abs(drift) / max(e0, 1e-300)
        status = "PASS" if rel <= rel_tol else "FAIL"
        out.append({
            "interaction_id": r.get("interaction_id", ""),
            "channel_sum_eV": ch_sum,
            "total_energy_drift_eV": drift,
            "relative_energy_drift": rel,
            "delta_Wr": ffloat(r, "delta_Wr", 0.0) or 0.0,
            "status": status,
        })
    return out


def taxonomy_guard(mode_rows: list[dict[str, str]], finite_core_resolved: bool, material_frame_resolved: bool) -> list[dict[str, Any]]:
    out = []
    for r in mode_rows:
        family = r.get("family", "").strip().lower()
        issues = []
        if family == "writhe" and fbool(r, "independent_energy_channel", False):
            issues.append("writhe is an independent energy channel without an explicit independence proof")
        if family == "twist" and not material_frame_resolved:
            issues.append("twist mode declared without a resolved material frame")
        if family == "core" and not finite_core_resolved:
            issues.append("core mode declared without a resolved finite core")
        if issues:
            out.append({"knot": r.get("knot", ""), "mode_id": r.get("mode_id", ""), "status": "FAIL", "issues": issues})
    return out
