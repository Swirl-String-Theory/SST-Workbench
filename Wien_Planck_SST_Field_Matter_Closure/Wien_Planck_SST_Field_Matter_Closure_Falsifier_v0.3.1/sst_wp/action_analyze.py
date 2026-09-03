from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from .common import read_csv, load_json, dump_json, cv, logfit, relerr
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean, scan_blind_payload_leak


def _truth(v, default=False):
    if v is None or v == "":
        return bool(default)
    return str(v).strip().lower() in ("true", "1", "yes", "pass", "ok")


def _float(v, default=float("nan")):
    try:
        x = float(v)
        return x
    except Exception:
        return default


def main():
    p = argparse.ArgumentParser()
    p.add_argument("blind_csv")
    p.add_argument("--config", required=True)
    p.add_argument("--campaign", default=None, help="Public campaign JSON for preregistered coverage accounting.")
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
        raise SystemExit(f"FAIL CLOSED SST/SI/target leakage in blind scorer inputs: {bad}")

    campaign = load_json(a.campaign) if a.campaign else None
    if campaign is not None:
        expected_n = int(campaign.get("expected_observations", len(rows)))
        campaign_reports_complete = bool(campaign.get("coverage_complete", False))
    else:
        expected_n = len(rows)
        campaign_reports_complete = True

    ok_rows = [r for r in rows if str(r.get("row_status", "OK")).upper() == "OK"]
    coverage_complete = bool(
        len(rows) == expected_n
        and len(ok_rows) == expected_n
        and campaign_reports_complete
    )

    rec = []
    by_res = defaultdict(list)
    by_carrier_res = defaultdict(list)
    energy_valid = []

    for r in ok_rows:
        f = _float(r.get("frequency_hat"))
        w = _float(r.get("omega_hat"))
        dE = _float(r.get("delta_E_hat"))
        base = _float(r.get("base_energy_hat"), 0.0)
        rel = _float(r.get("delta_E_over_abs_base"), float("nan"))
        valid = (
            _truth(r.get("energy_signal_valid"), False)
            and np.isfinite(dE)
            and dE > 0
            and np.isfinite(rel)
            and rel >= cfg["gates"]["min_deltaE_relative_to_base"]
        )
        energy_valid.append(bool(valid))
        Jf = dE / f if valid and np.isfinite(f) and f > 0 else float("nan")
        Jw = dE / w if valid and np.isfinite(w) and w > 0 else float("nan")
        q = {
            **r,
            "Jf_hat": Jf,
            "Jomega_hat": Jw,
            "omega_consistency": relerr(w, 2 * math.pi * f) if np.isfinite(f) and np.isfinite(w) and f > 0 else float("inf"),
            "energy_valid_blind": valid,
        }
        rec.append(q)
        by_res[r.get("resolution_N", "")].append(q)
        by_carrier_res[(r.get("anon_carrier_id", ""), r.get("resolution_N", ""))].append(q)

    slopes, slope_r2, universality = [], [], []
    recurrence, mesh, re_ok, temp = [], [], [], []
    mode_ok, matched_ok = [], []

    for g in by_carrier_res.values():
        if len(g) < 1:
            continue
        g = sorted(g, key=lambda x: _float(x.get("amplitude_hat"), 0.0))
        validg = [q for q in g if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])]
        if len(validg) >= 3:
            x = [_float(q.get("amplitude_hat")) for q in validg]
            y = [float(q["Jf_hat"]) for q in validg]
            s, b, r2 = logfit(x, y)
            slopes.append(s)
            slope_r2.append(r2)
            universality.extend(y)

        for q in g:
            certified = _truth(q.get("frequency_certified"), default=False)
            if "frequency_certified" not in q:
                certified = (
                    not _truth(q.get("frequency_window_limited"), True)
                    and _float(q.get("cycles"), 0.0) >= cfg["gates"]["min_cycles"]
                )
            recurrence.append(
                certified
                and not _truth(q.get("frequency_window_limited"), True)
                and _float(q.get("cycles"), 0.0) >= cfg["gates"]["min_cycles"]
                and _float(q.get("spectral_power"), 0.0) >= cfg["gates"]["min_spectral_power"]
                and _float(q.get("harmonic_r2"), 0.0) >= cfg["gates"]["min_harmonic_r2"]
            )

            mode_present = "mode_normal_fraction" in q or "mode_discovery_valid" in q
            mode_ok.append(
                True if not mode_present else (
                    _truth(q.get("mode_discovery_valid"), False)
                    and _float(q.get("mode_normal_fraction"), 0.0)
                    >= cfg["gates"].get("min_mode_normal_fraction", 0.5)
                )
            )
            matched_ok.append(
                _truth(q.get("matched_energy_frequency_same_frozen_mode"), True)
            )

            mcvp = _float(q.get("mesh_cv_plus"), float("inf"))
            mcvm = _float(q.get("mesh_cv_minus"), float("inf"))
            erp = _float(q.get("mesh_edge_ratio_plus"), 1.0)
            erm = _float(q.get("mesh_edge_ratio_minus"), 1.0)
            mesh.append(
                mcvp <= cfg["gates"]["max_mesh_cv"]
                and mcvm <= cfg["gates"]["max_mesh_cv"]
                and erp <= cfg["gates"].get("max_mesh_edge_ratio", float("inf"))
                and erm <= cfg["gates"].get("max_mesh_edge_ratio", float("inf"))
            )

            eps_re = _float(q.get("epsilon_RE_perp", q.get("epsilon_RE")), float("inf"))
            re_ok.append(eps_re <= cfg["gates"]["max_epsilon_RE"])
            temp.append(
                q.get("temporal_frequency_rel_change", "") != ""
                and _float(q.get("temporal_frequency_rel_change"), float("inf"))
                <= cfg["gates"]["max_temporal_rel_change"]
            )

    omega_max = max([float(q["omega_consistency"]) for q in rec] or [float("inf")])
    slope_med = float(np.median(slopes)) if slopes else None
    r2_med = float(np.median(slope_r2)) if slope_r2 else None

    continuity = (
        bool(slopes)
        and slope_med >= cfg["gates"]["continuous_action_slope_min"]
        and r2_med >= cfg["gates"]["continuous_action_r2_min"]
    )

    gates = {
        "UA0_no_SST_SI_target_leak": not bad,
        "UA0b_complete_campaign_coverage": coverage_complete,
        "UA1_omega_equals_2pi_f": bool(rec) and omega_max <= cfg["gates"]["omega_rel_tol"],
        "UA2_recurrent_mode_prerequisite": bool(recurrence) and sum(recurrence) / len(recurrence) >= cfg["gates"]["min_recurrence_fraction"],
        "UA2a_frozen_mode_normal_content": bool(mode_ok) and all(mode_ok),
        "UA2b_normal_relative_equilibrium": bool(re_ok) and all(re_ok),
        "UA2c_positive_resolved_dimensionless_mode_energy": bool(energy_valid) and all(energy_valid),
        "UA2d_matched_mode_energy_frequency": bool(matched_ok) and all(matched_ok),
        "UA3_adaptive_mesh_quality": bool(mesh) and all(mesh),
        "UA3b_temporal_convergence": bool(temp) and all(temp),
        "UA4_reject_classical_continuous_action": not continuity,
        "UA5_dimensionless_action_amplitude_independence": slope_med is not None and abs(slope_med) <= cfg["gates"]["max_action_amplitude_log_slope"],
        "UA6_dimensionless_action_universality": bool(universality) and cv(universality) <= cfg["gates"]["max_action_cv"],
    }

    meds = {}
    for N, rs in by_res.items():
        vals = [q["Jf_hat"] for q in rs if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])]
        if vals:
            meds[N] = float(np.median(vals))
    Ns = sorted(meds, key=lambda x: int(x))
    conv = relerr(meds[Ns[-1]], meds[Ns[-2]]) if len(Ns) >= 2 else None
    gates["UA7_spatial_convergence"] = conv is not None and conv <= cfg["gates"]["max_resolution_rel_change"]

    all_jf = [q["Jf_hat"] for q in rec if q["energy_valid_blind"] and np.isfinite(q["Jf_hat"])]
    all_jw = [q["Jomega_hat"] for q in rec if q["energy_valid_blind"] and np.isfinite(q["Jomega_hat"])]

    gate_status = {k: ("PASS" if v else "FAIL") for k, v in gates.items()}

    recurrence_prereq = (
        gates["UA0_no_SST_SI_target_leak"]
        and gates["UA0b_complete_campaign_coverage"]
        and gates["UA2a_frozen_mode_normal_content"]
        and gates["UA2d_matched_mode_energy_frequency"]
        and gates["UA3_adaptive_mesh_quality"]
    )
    if not recurrence_prereq or not gates["UA2_recurrent_mode_prerequisite"]:
        gate_status["UA3b_temporal_convergence"] = "SKIP_PREREQUISITE"

    action_prereq = (
        recurrence_prereq
        and gates["UA2_recurrent_mode_prerequisite"]
        and gates["UA2b_normal_relative_equilibrium"]
        and gates["UA2c_positive_resolved_dimensionless_mode_energy"]
        and gates["UA3b_temporal_convergence"]
    )
    if not action_prereq:
        for k in [
            "UA4_reject_classical_continuous_action",
            "UA5_dimensionless_action_amplitude_independence",
            "UA6_dimensionless_action_universality",
            "UA7_spatial_convergence",
        ]:
            gate_status[k] = "SKIP_PREREQUISITE"

    out = {
        "format": "SST-WP-BLIND-ACTION-3.1",
        "SST_canonical_constants_read": False,
        "SI_scales_read": False,
        "absolute_target_read": False,
        "n": len(rows),
        "n_ok": len(ok_rows),
        "expected_n": expected_n,
        "summary": {
            "coverage_fraction": len(ok_rows) / expected_n if expected_n else 0.0,
            "dimensionless_action_cv": cv(universality) if universality else None,
            "median_Jf_hat": float(np.median(all_jf)) if all_jf else None,
            "median_Jomega_hat": float(np.median(all_jw)) if all_jw else None,
            "median_action_amplitude_log_slope": slope_med,
            "median_action_amplitude_fit_r2": r2_med,
            "classical_continuity_null_triggered": continuity,
            "omega_rel_error_max": omega_max,
            "resolution_median_Jf_hat": meds,
            "highest_resolution_rel_change": conv,
            "recurrence_pass_fraction": sum(recurrence) / len(recurrence) if recurrence else None,
            "frozen_mode_pass_fraction": sum(mode_ok) / len(mode_ok) if mode_ok else None,
            "relative_equilibrium_pass_fraction": sum(re_ok) / len(re_ok) if re_ok else None,
            "energy_signal_pass_fraction": sum(energy_valid) / len(energy_valid) if energy_valid else None,
            "mesh_pass_fraction": sum(mesh) / len(mesh) if mesh else None,
            "temporal_convergence_pass_fraction": sum(temp) / len(temp) if temp else None,
        },
        "gates": gates,
        "gate_status": gate_status,
        "blind_pass": all(gates.values()),
        "interpretation": (
            "The blind verdict concerns only a dimensionless universal-action candidate measured on one frozen, "
            "normal-projected mode per carrier/resolution. Energy and frequency are paired on that same mode. "
            "Tangential marker motion is excluded from the centerline relative-equilibrium gate. No SI action, "
            "canonical normalization, or absolute-target comparison is permitted here."
        ),
        "epistemic_status": (
            "DIMENSIONLESS_NUMERICAL_CENTERLINE_CANDIDATE; topology and full 3-D finite-core Euler are not certified by this package."
        ),
    }
    dump_json(a.out, out)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
