from __future__ import annotations
import json, math
from pathlib import Path
from .core import *


def _expand_samples(candidate: dict) -> list[dict]:
    if candidate.get("samples"):
        return candidate["samples"]
    g = candidate.get("generator", {})
    if g.get("type") == "liv_power_law":
        n = int(g["n"]); E_star = float(g["E_star_GeV"])
        out=[]
        for E_TeV in (3.0,10.0,20.0,100.0,300.0):
            out.append({"energy_TeV":E_TeV,"delta_v_over_c":group_delay_fraction_exact(E_TeV*1e3,E_star,n)})
        return out
    return []


def run(root: Path, candidate_path: Path, output_root: Path) -> dict:
    blind_path = output_root/"blind"/"verdict.json"
    if not blind_path.exists():
        raise RuntimeError("Run blind phase first")
    public = json.loads((root/"data/public/constraints_prl_2026.json").read_text(encoding="utf-8"))
    cand = json.loads(candidate_path.read_text(encoding="utf-8"))
    out = output_root/"revealed"; out.mkdir(parents=True, exist_ok=True)

    if not cand.get("derived_without_GRB_target_fit", False):
        independent_status = "FAIL"
    else:
        independent_status = "PASS"

    samples = _expand_samples(cand)
    clean=[]
    for s in samples:
        E=float(s["energy_TeV"])*1e3
        if s.get("delta_v_over_c") is not None:
            delta=float(s["delta_v_over_c"])
            vg=1.0-delta if delta > 1e-15 else None
        elif s.get("vg_over_c") is not None:
            vg=float(s["vg_over_c"])
            delta=1.0-vg
        else:
            continue
        clean.append((E,delta,vg))

    gates=[{"id":"R01_INDEPENDENT_DERIVATION", "status":independent_status,
            "derived_without_GRB_target_fit":bool(cand.get("derived_without_GRB_target_fit",False)),
            "provenance":cand.get("provenance") }]

    if len(clean)<2:
        verdict={"verdict":"OPEN_NO_INDEPENDENT_CANDIDATE","candidate_id":cand.get("candidate_id"),"gates":gates}
        dump_json(out/"verdict.json",verdict)
        (out/"report.md").write_text("# Reveal verdict\n\n**OPEN_NO_INDEPENDENT_CANDIDATE** — supply at least two frozen non-null candidate velocity samples.\n",encoding="utf-8")
        return verdict

    Es=[x[0] for x in clean]; ds=[x[1] for x in clean]
    if any(d <= 0 for d in ds):
        gates.append({"id":"R02_SUBLUMINAL_SIGN", "status":"FAIL", "deltas":ds})
        sign_ok=False
    else:
        gates.append({"id":"R02_SUBLUMINAL_SIGN", "status":"PASS", "delta_min":min(ds),"delta_max":max(ds)})
        sign_ok=True

    fit=linear_fit_log_power(Es,ds) if sign_ok else None
    if fit:
        nearest=min((1,2), key=lambda n:abs(fit["n_eff"]-n))
        order_ok=abs(fit["n_eff"]-nearest)<=0.25 and fit["r2"]>=0.98
        gates.append({"id":"R03_EFFECTIVE_POWER_LAW", "status":"PASS" if order_ok else "FAIL", **fit,
                      "nearest_tested_order":nearest,"tolerance_abs_n":0.25,"min_r2":0.98})
    else:
        nearest=None; order_ok=False

    scale_ok=False; scale=None; scatter=None
    if order_ok and nearest:
        scales=implied_scales_GeV(Es,ds,nearest)
        scale=geometric_mean(scales)
        logs=[math.log(x) for x in scales]; lm=sum(logs)/len(logs)
        scatter=math.sqrt(sum((x-lm)**2 for x in logs)/len(logs))
        upper=float(public["transparency_upper_95_GeV"][str(nearest)]["central"])
        biref=bool(cand.get("birefringent",False))
        primary_lower=float(public["polarization_lower_GeV_framework_dependent"][str(nearest)]) if biref else 0.0
        scale_ok=(primary_lower < scale < upper) and scatter <= 0.35
        gates.append({"id":"R04_PRIMARY_BLIND_WINDOW_MATCH", "status":"PASS" if scale_ok else "FAIL",
                      "n":nearest,"E_star_geomean_GeV":scale,"log_scatter":scatter,
                      "primary_lower_GeV":primary_lower,"upper_GeV":upper,"birefringent":biref})

        legacy=public["legacy_A044_v0_1_lower_95_GeV"]
        legacy_lower=max(float(legacy["time_of_flight_GRB221009A"][str(nearest)]),float(legacy["breit_wheeler_spectral"][str(nearest)]))
        legacy_ok=legacy_lower < scale
        gates.append({"id":"R04B_LEGACY_BASELINE_LOWER", "status":"CONDITIONAL_PASS" if legacy_ok else "CONDITIONAL_FAIL",
                      "legacy_effective_lower_GeV":legacy_lower,"candidate_scale_GeV":scale,
                      "note":"Applicability requires matching photon/electron-sector and reaction-kinematics assumptions."})

        # Conditional timing check using representative 10 TeV lower-energy photon.
        c=public["diagnostic_cosmology"]
        dt=tof_delay_s(300.0,10.0,scale,nearest,public["source_object"]["redshift"],c["H0_km_s_Mpc"],c["Omega_m"],c["Omega_Lambda"])
        tcarpet=public["carpet"]["arrival_time_after_trigger_s"]
        tw=public["lhaaso"]["km2a_arrival_time_after_trigger_s"]
        dtwin=[tcarpet-tw["high"],tcarpet-tw["low"]]
        gates.append({"id":"R05_TIMING_COMMON_EMISSION_DIAGNOSTIC", "status":"CONDITIONAL_PASS" if dtwin[0] <= dt <= dtwin[1] else "CONDITIONAL_FAIL",
                      "predicted_delay_s":dt,"observed_delay_window_s":dtwin,
                      "assumption":"Common emission episode; intrinsic source delay neglected."})

        eps0=pair_threshold_eV(300.0); eps=pair_threshold_eV(300.0,scale,nearest)
        gates.append({"id":"R06_PAIR_THRESHOLD_DIAGNOSTIC", "status":"DIAGNOSTIC",
                      "epsilon_standard_eV":eps0,"epsilon_candidate_eV":eps,"uplift_ratio":eps/eps0})

    hard=[g for g in gates if g["status"] in ("PASS","FAIL")]
    hard_pass=all(g["status"]=="PASS" for g in hard)
    if independent_status != "PASS":
        overall="REJECTED_TARGET_FITTED_CANDIDATE"
    elif hard_pass and scale_ok:
        overall="SST_DISPERSION_CANDIDATE_QUALIFIES_PHENOMENOLOGICALLY"
    else:
        overall="SST_DISPERSION_CANDIDATE_REJECTED_OR_UNCLASSIFIED"
    verdict={"verdict":overall,"candidate_id":cand.get("candidate_id"),"effective_order":fit,"effective_scale_GeV":scale,"gates":gates,
             "nonclaim":"Qualification against the frozen phenomenological gates is not a full radiative-transfer likelihood reproduction."}
    dump_json(out/"verdict.json",verdict)
    lines=["# Reveal verdict","",f"**{overall}**","",f"Candidate: `{cand.get('candidate_id')}`"]
    if fit: lines += [f"Effective order: `{fit['n_eff']:.6g}` (R²={fit['r2']:.6g})"]
    if scale: lines += [f"Effective scale: `{scale:.9e} GeV`",f"Log-scatter of implied scales: `{scatter:.6g}`"]
    lines += ["", "The timing gate is conditional on a common emission episode and is not used as an unconditional source-independent falsification."]
    (out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return verdict
