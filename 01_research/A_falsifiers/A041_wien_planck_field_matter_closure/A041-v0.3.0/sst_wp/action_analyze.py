from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from .common import read_csv, load_json, dump_json, cv, logfit, relerr
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean, scan_blind_payload_leak

def main():
    p = argparse.ArgumentParser()
    p.add_argument("blind_csv")
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    assert_blind_code_clean(Path(__file__).resolve().parents[1])
    rows = read_csv(a.blind_csv)
    cfg = load_json(a.config)
    assert_blind_config_clean(cfg)
    bad = scan_blind_payload_leak({
        "config": cfg,
        "columns": list(rows[0]) if rows else [],
    })
    if bad:
        raise SystemExit(
            f"FAIL CLOSED SST/SI/target leakage in blind scorer inputs: {bad}"
        )

    rec = []
    by_res = defaultdict(list)
    by_carrier_res = defaultdict(list)
    energy_valid = []

    for r in rows:
        f = float(r["frequency_hat"])
        w = float(r["omega_hat"])
        dE = float(r["delta_E_hat"])
        base = float(r.get("base_energy_hat") or 0.0)
        rel = float(r.get("delta_E_over_abs_base") or 0.0)
        valid = (
            r.get("energy_signal_valid", "").lower() in ("true", "1", "yes")
            and np.isfinite(dE)
            and dE > 0
            and np.isfinite(rel)
            and rel >= cfg["gates"]["min_deltaE_relative_to_base"]
        )
        energy_valid.append(bool(valid))
        Jf = dE / f if valid and f > 0 else float("nan")
        Jw = dE / w if valid and w > 0 else float("nan")
        q = {
            **r,
            "Jf_hat": Jf,
            "Jomega_hat": Jw,
            "omega_consistency": relerr(w, 2 * math.pi * f),
            "energy_valid_blind": valid,
        }
        rec.append(q)
        by_res[r["resolution_N"]].append(q)
        by_carrier_res[(r["anon_carrier_id"], r["resolution_N"])].append(q)

    slopes, slope_r2, universality = [], [], []
    recurrence, mesh, re_ok, temp = [], [], [], []

    for g in by_carrier_res.values():
        if len(g) >= 3:
            g = sorted(g, key=lambda x: float(x["amplitude_hat"]))
            validg = [
                q for q in g
                if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])
            ]
            if len(validg) >= 3:
                x = [float(q["amplitude_hat"]) for q in validg]
                y = [float(q["Jf_hat"]) for q in validg]
                s, b, r2 = logfit(x, y)
                slopes.append(s)
                slope_r2.append(r2)
                universality.extend(y)

            recurrence += [
                str(q.get("frequency_window_limited", "true")).lower() not in ("true","1","yes")
                and float(q["cycles"]) >= cfg["gates"]["min_cycles"]
                and float(q["spectral_power"]) >= cfg["gates"]["min_spectral_power"]
                and float(q["harmonic_r2"]) >= cfg["gates"]["min_harmonic_r2"]
                for q in g
            ]
            mesh += [
                float(q["mesh_cv_plus"]) <= cfg["gates"]["max_mesh_cv"]
                and float(q["mesh_cv_minus"]) <= cfg["gates"]["max_mesh_cv"]
                for q in g
            ]
            re_ok += [
                float(q["epsilon_RE"]) <= cfg["gates"]["max_epsilon_RE"]
                for q in g
            ]
            temp += [
                q.get("temporal_frequency_rel_change", "") != ""
                and float(q["temporal_frequency_rel_change"])
                <= cfg["gates"]["max_temporal_rel_change"]
                for q in g
            ]

    omega_max = max(
        [float(q["omega_consistency"]) for q in rec] or [float("inf")]
    )
    slope_med = float(np.median(slopes)) if slopes else None
    r2_med = float(np.median(slope_r2)) if slope_r2 else None

    continuity = (
        bool(slopes)
        and slope_med >= cfg["gates"]["continuous_action_slope_min"]
        and r2_med >= cfg["gates"]["continuous_action_r2_min"]
    )

    gates = {
        "UA0_no_SST_SI_target_leak": not bad,
        "UA1_omega_equals_2pi_f": omega_max <= cfg["gates"]["omega_rel_tol"],
        "UA2_recurrent_mode_prerequisite":
            bool(recurrence)
            and sum(recurrence) / len(recurrence)
            >= cfg["gates"]["min_recurrence_fraction"],
        "UA2b_relative_equilibrium": bool(re_ok) and all(re_ok),
        "UA2c_positive_resolved_dimensionless_energy":
            bool(energy_valid) and all(energy_valid),
        "UA3_mesh_quality": bool(mesh) and all(mesh),
        "UA3b_temporal_convergence": bool(temp) and all(temp),
        "UA4_reject_classical_continuous_action": not continuity,
        "UA5_dimensionless_action_amplitude_independence":
            slope_med is not None
            and abs(slope_med)
            <= cfg["gates"]["max_action_amplitude_log_slope"],
        "UA6_dimensionless_action_universality":
            bool(universality)
            and cv(universality) <= cfg["gates"]["max_action_cv"],
    }

    meds = {}
    for N, rs in by_res.items():
        vals = [
            q["Jf_hat"] for q in rs
            if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])
        ]
        if vals:
            meds[N] = float(np.median(vals))
    Ns = sorted(meds, key=lambda x: int(x))
    conv = (
        relerr(meds[Ns[-1]], meds[Ns[-2]])
        if len(Ns) >= 2 else None
    )
    gates["UA7_spatial_convergence"] = (
        conv is not None
        and conv <= cfg["gates"]["max_resolution_rel_change"]
    )

    all_jf = [
        q["Jf_hat"] for q in rec
        if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])
    ]
    all_jw = [
        q["Jomega_hat"] for q in rec
        if q["energy_valid_blind"] and np.isfinite(q["Jomega_hat"])
    ]

    # Explicit prerequisite semantics: a downstream false after a missing recurrence/energy
    # prerequisite is reported as SKIP_PREREQUISITE rather than overinterpreted as physics.
    gate_status={k:("PASS" if v else "FAIL") for k,v in gates.items()}
    if not gates.get("UA2_recurrent_mode_prerequisite",False):
        for k in ["UA3b_temporal_convergence","UA4_reject_classical_continuous_action","UA5_dimensionless_action_amplitude_independence","UA6_dimensionless_action_universality","UA7_spatial_convergence"]:
            gate_status[k]="SKIP_PREREQUISITE"
    if not gates.get("UA2c_positive_resolved_dimensionless_energy",False):
        for k in ["UA4_reject_classical_continuous_action","UA5_dimensionless_action_amplitude_independence","UA6_dimensionless_action_universality","UA7_spatial_convergence"]:
            gate_status[k]="SKIP_PREREQUISITE"

    out = {
        "format": "SST-WP-BLIND-ACTION-3.0",
        "SST_canonical_constants_read": False,
        "SI_scales_read": False,
        "absolute_target_read": False,
        "n": len(rows),
        "summary": {
            "dimensionless_action_cv": cv(universality) if universality else None,
            "median_Jf_hat": float(np.median(all_jf)) if all_jf else None,
            "median_Jomega_hat": float(np.median(all_jw)) if all_jw else None,
            "median_action_amplitude_log_slope": slope_med,
            "median_action_amplitude_fit_r2": r2_med,
            "classical_continuity_null_triggered": continuity,
            "omega_rel_error_max": omega_max,
            "resolution_median_Jf_hat": meds,
            "highest_resolution_rel_change": conv,
            "relative_equilibrium_pass_fraction":
                sum(re_ok) / len(re_ok) if re_ok else None,
            "energy_signal_pass_fraction":
                sum(energy_valid) / len(energy_valid) if energy_valid else None,
            "temporal_convergence_pass_fraction":
                sum(temp) / len(temp) if temp else None,
        },
        "gates": gates,
        "gate_status": gate_status,
        "blind_pass": all(gates.values()),
        "interpretation":
            "The blind verdict concerns only a dimensionless universal-action candidate. "
            "No SI action, canonical normalization, or absolute-target comparison is permitted here. "
            "Discrete frequencies alone never count as action quantization.",
        "epistemic_status":
            "DIMENSIONLESS_NUMERICAL_CENTERLINE_CANDIDATE; "
            "topology and full 3-D finite-core Euler are not certified by this package.",
    }
    dump_json(a.out, out)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
