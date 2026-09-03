from __future__ import annotations
from pathlib import Path
import csv, json, math
import numpy as np

from .constants import HBAR_SI, hbar_sst, action_scale_audit
from .qgi import (
    ideal_phase, generalized_phase, finite_pulse_phase,
    lab_action_numeric, lab_action_analytic, freefall_boundary_action,
    fit_power_law
)
from .geometry import descriptors, geometry_sha256

def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _relerr(a,b):
    return abs(a-b)/max(abs(b),1e-300)

def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader(); w.writerows(rows)

def run_blind(cfg: dict, project_root: Path, mode: str) -> dict:
    out=project_root/f"{cfg['project_name']}-outputs"
    blind=out/"blind"
    manifest=load_json(blind/"public_manifest.json")
    phys=cfg["physics"]
    m=float(phys["mass_kg"]); g=float(phys["g_m_s2"])
    T=np.array(phys["T_s"],dtype=float)
    hs=hbar_sst()

    # Phase fits are independent of carrier identity.
    phi_si=ideal_phase(T,m,g,HBAR_SI)
    phi_sst=ideal_phase(T,m,g,hs)
    p_si,A_si=fit_power_law(T,phi_si)
    p_sst,A_sst=fit_power_law(T,phi_sst)

    target_pref=abs(m*g*g/(3.0*HBAR_SI))
    sst_pref=abs(m*g*g/(3.0*hs))
    pref_rel=_relerr(sst_pref,target_pref)

    ns=cfg["numerics"]["action_n_extended" if mode=="extended" else "action_n_basic"]
    action_rows=[]
    max_action_err=0.0
    max_frame_err=0.0
    for n in ns:
        for Tv in T:
            sn=lab_action_numeric(float(Tv),m,g,int(n))
            sa=lab_action_analytic(float(Tv),m,g)
            sf=freefall_boundary_action(float(Tv),m,g)
            erra=_relerr(sn,sa)
            errf=_relerr(sn,sf)
            max_action_err=max(max_action_err,erra)
            max_frame_err=max(max_frame_err,errf)
            action_rows.append({
                "T_s":float(Tv),"n_time":int(n),
                "S_lab_numeric_J_s":sn,
                "S_lab_analytic_J_s":sa,
                "S_freefall_boundary_J_s":sf,
                "action_rel_error":erra,
                "frame_rel_error":errf,
            })
    # Gate on finest resolution, not coarse ladder maximum.
    finest=max(ns)
    finest_rows=[r for r in action_rows if r["n_time"]==finest]
    finest_action=max(r["action_rel_error"] for r in finest_rows)
    finest_frame=max(r["frame_rel_error"] for r in finest_rows)

    # Generalized law identity at a=g must reduce to ideal phase.
    gen=generalized_phase(g,T,m,g,HBAR_SI)
    gen_err=float(np.max(np.abs((gen-phi_si)/np.maximum(np.abs(phi_si),1e-300))))

    # Finite-pulse formula: with zero kick/delay the sign convention is opposite
    # the ideal Eq.2 expression in the paper's Eq.5 convention; compare magnitudes.
    fp=finite_pulse_phase(T,0.0,0.0,m,g,HBAR_SI)
    fp_err=float(np.max(np.abs((np.abs(fp)-np.abs(phi_si))/np.maximum(np.abs(phi_si),1e-300))))

    # Blind carrier metrics: source identity is never read.
    metric_rows=[]
    hash_mismatches=0
    for c in manifest["candidates"]:
        p=np.load(blind/"geometries"/f"{c['candidate_id']}.npy",allow_pickle=False)
        d=descriptors(p)
        if d["geometry_sha256"] != c["geometry_sha256"]:
            hash_mismatches += 1
        metric_rows.append({
            "candidate_id":c["candidate_id"],
            "stratum_token":c["stratum_token"],
            "geometry_sha256":d["geometry_sha256"],
            "n_points":d["n_points"],
            "length":d["length"],
            "segment_cv":d["segment_cv"],
            "curvature_mean":d["curvature_mean"],
            "curvature_rms":d["curvature_rms"],
            "curvature_max":d["curvature_max"],
            "min_nonlocal_distance_proxy":d["min_nonlocal_distance_proxy"],
            "phase_model_uses_geometry":False,
            "phase_prefactor_rel_error_sst_vs_si":pref_rel,
        })

    thr=cfg["gates"][mode]
    gates={
        "G1_CUBIC_EXPONENT":{
            "status":"PASS" if abs(p_sst-3.0)<=thr["cubic_exponent_abs"] else "FAIL",
            "value":abs(p_sst-3.0),"threshold":thr["cubic_exponent_abs"]
        },
        "G2_SST_PREFACTOR_QGI_COMPATIBILITY":{
            "status":"PASS" if pref_rel<=thr["prefactor_rel"] else "FAIL",
            "value":pref_rel,"threshold":thr["prefactor_rel"],
            "note":"experimental compatibility only; not a microphysical derivation"
        },
        "G3_NUMERIC_LAB_ACTION":{
            "status":"PASS" if finest_action<=thr["action_rel"] else "FAIL",
            "value":finest_action,"threshold":thr["action_rel"],"n_time":finest
        },
        "G4_FRAME_GAUGE_CLOSURE":{
            "status":"PASS" if finest_frame<=thr["frame_rel"] else "FAIL",
            "value":finest_frame,"threshold":thr["frame_rel"],"n_time":finest
        },
        "G5_GENERALIZED_A_EQUALS_G":{
            "status":"PASS" if gen_err<=thr["identity_rel"] else "FAIL",
            "value":gen_err,"threshold":thr["identity_rel"]
        },
        "G6_FINITE_PULSE_ZERO_LIMIT":{
            "status":"PASS" if fp_err<=thr["identity_rel"] else "FAIL",
            "value":fp_err,"threshold":thr["identity_rel"]
        },
        "G7_BLIND_INTEGRITY":{
            "status":"PASS" if hash_mismatches==0 else "FAIL",
            "hash_mismatches":hash_mismatches,
            "source_identity_read":False,
            "private_mapping_read":False,
        }
    }
    primary_pass=all(g["status"]=="PASS" for g in gates.values())

    phase_rows=[]
    for Tv,ps,pt in zip(T,phi_sst,phi_si):
        phase_rows.append({
            "T_s":float(Tv),
            "phase_target_rad":float(pt),
            "phase_sst_rad":float(ps),
            "relative_difference":float((ps-pt)/pt),
        })

    _write_csv(blind/f"carrier_metrics_{mode}.csv",metric_rows)
    _write_csv(blind/f"action_convergence_{mode}.csv",action_rows)
    _write_csv(blind/f"phase_curve_{mode}.csv",phase_rows)
    result={
        "format":"SST-QGI-BLIND-RUN-1.0",
        "mode":mode,
        "backend":"cpp-pybind11" if _native_available() else "numpy-fallback",
        "source_identity_read":False,
        "private_mapping_read":False,
        "n_candidates":len(metric_rows),
        "n_blind_strata":manifest["n_blind_strata"],
        "action_scale_audit":action_scale_audit(),
        "fit":{
            "p_si":p_si,"p_sst":p_sst,
            "prefactor_si_abs":A_si,"prefactor_sst_abs":A_sst,
            "prefactor_rel_error_sst_vs_si":pref_rel
        },
        "gates":gates,
        "blind_verdict":"BLIND_MACRO_CLOSURE_PASS" if primary_pass else "BLIND_FALSIFIER_HIT",
        "interpretation":"Knot microdynamics not tested in v0.1.0; no geometry-to-phase coupling is inserted.",
    }
    dump_json(blind/f"gate_report_{mode}.json",result)
    if mode=="extended":
        _extended_sweeps(cfg,blind,m,g)
        _make_plots(blind,T,phi_si,phi_sst,action_rows)
    return result

def _native_available():
    try:
        import sst_qgi_native
        return True
    except Exception:
        return False

def _extended_sweeps(cfg,blind,m,g):
    T=np.array(cfg["physics"]["T_s"],dtype=float)
    ratios=np.array(cfg["physics"]["a_over_g"],dtype=float)
    rows=[]
    for ratio in ratios:
        a=ratio*g
        ph=generalized_phase(a,T,m,g,HBAR_SI)
        for Tv,p in zip(T,ph):
            rows.append({"a_over_g":float(ratio),"T_s":float(Tv),"phase_rad":float(p)})
    _write_csv(blind/"generalized_acceleration_sweep.csv",rows)

    fp_rows=[]
    for tk in cfg["physics"]["Tkick_s"]:
        for td in cfg["physics"]["Td_s"]:
            ph=finite_pulse_phase(T,float(tk),float(td),m,g,HBAR_SI)
            for Tv,p in zip(T,ph):
                fp_rows.append({"Tkick_s":float(tk),"Td_s":float(td),"T_s":float(Tv),"phase_rad":float(p)})
    _write_csv(blind/"finite_pulse_sweep.csv",fp_rows)

def _make_plots(blind,T,phi_si,phi_sst,action_rows):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    plt.figure()
    plt.plot(2*T*1e3,phi_si,label="QGI / SI hbar")
    plt.plot(2*T*1e3,phi_sst,"--",label="SST action quantum")
    plt.xlabel("free-fall duration 2T [ms]")
    plt.ylabel("phase [rad]")
    plt.legend()
    plt.tight_layout()
    plt.savefig(blind/"phase_vs_duration.png",dpi=160)
    plt.close()

    ns=sorted(set(r["n_time"] for r in action_rows))
    vals=[]
    for n in ns:
        vals.append(max(r["action_rel_error"] for r in action_rows if r["n_time"]==n))
    plt.figure()
    plt.loglog(ns,vals,marker="o")
    plt.xlabel("time samples")
    plt.ylabel("max relative lab-action error")
    plt.tight_layout()
    plt.savefig(blind/"action_convergence.png",dpi=160)
    plt.close()
