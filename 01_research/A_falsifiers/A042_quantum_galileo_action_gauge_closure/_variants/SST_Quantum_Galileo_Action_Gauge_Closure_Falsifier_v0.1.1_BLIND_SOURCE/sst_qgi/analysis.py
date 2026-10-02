from __future__ import annotations
from pathlib import Path
import csv, json
import numpy as np

from .constants import legacy_h_echo, legacy_hbar_echo, provenance_audit
from .qgi import (
    ideal_action, generalized_action, finite_pulse_action, phase_from_action,
    lab_action_numeric, lab_action_analytic, freefall_boundary_action, fit_power_law
)
from .geometry import descriptors

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
        path.write_text("",encoding="utf-8")
        return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def source_target_leak_scan(project_root: Path) -> dict:
    # Scan runtime modules for exact SI-target symbols/literals.
    forbidden=("H"+"_"+"SI","H"+"BAR"+"_"+"SI","scipy.constants."+"h","physical_"+"constants")
    hits=[]
    for p in (project_root/"sst_qgi").rglob("*.py"):
        if p.name=="reveal.py":
            continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        for token in forbidden:
            if token in text:
                hits.append({"file":str(p.relative_to(project_root)),"token":token})
    return {"hits":hits,"n_hits":len(hits),"status":"PASS" if not hits else "FAIL"}

def run_blind(cfg: dict, project_root: Path, mode: str) -> dict:
    out=project_root/f"{cfg['project_name']}-outputs"
    blind=out/"blind"
    manifest=load_json(blind/"public_manifest.json")
    phys=cfg["physics"]
    m=float(phys["mass_kg"])
    g=float(phys["g_m_s2"])
    T=np.array(phys["T_s"],dtype=float)

    # Primary blind observable is action, not phase. No Planck target is needed.
    S=ideal_action(T,m,g)
    p_action,A_action=fit_power_law(T,S)

    # Legacy SST near-h number retained only as a provenance-negative control.
    h_echo=legacy_h_echo()
    hbar_echo=legacy_hbar_echo()
    phase_echo=phase_from_action(S,hbar_echo)
    p_phase_echo,A_phase_echo=fit_power_law(T,phase_echo)

    ns=cfg["numerics"]["action_n_extended" if mode=="extended" else "action_n_basic"]
    action_rows=[]
    for n in ns:
        for Tv in T:
            sn=lab_action_numeric(float(Tv),m,g,int(n))
            sa=lab_action_analytic(float(Tv),m,g)
            sf=freefall_boundary_action(float(Tv),m,g)
            action_rows.append({
                "T_s":float(Tv),
                "n_time":int(n),
                "S_lab_numeric_J_s":sn,
                "S_lab_analytic_J_s":sa,
                "S_freefall_boundary_J_s":sf,
                "action_rel_error":_relerr(sn,sa),
                "frame_rel_error":_relerr(sn,sf),
            })

    finest=max(ns)
    finest_rows=[r for r in action_rows if r["n_time"]==finest]
    finest_action=max(r["action_rel_error"] for r in finest_rows)
    finest_frame=max(r["frame_rel_error"] for r in finest_rows)

    gen=generalized_action(g,T,m,g)
    gen_err=float(np.max(np.abs((gen-S)/np.maximum(np.abs(S),1e-300))))
    fp=finite_pulse_action(T,0.0,0.0,m,g)
    fp_err=float(np.max(np.abs((np.abs(fp)-np.abs(S))/np.maximum(np.abs(S),1e-300))))

    metric_rows=[]
    hash_mismatches=0
    for c in manifest["candidates"]:
        pts=np.load(blind/"geometries"/f"{c['candidate_id']}.npy",allow_pickle=False)
        d=descriptors(pts)
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
            "geometry_to_qgi_phase_coupling_used":False,
        })

    leak=source_target_leak_scan(project_root)
    thr=cfg["gates"][mode]
    gates={
        "G1_ACTION_CUBIC_EXPONENT":{
            "status":"PASS" if abs(p_action-3.0)<=thr["cubic_exponent_abs"] else "FAIL",
            "value":abs(p_action-3.0),
            "threshold":thr["cubic_exponent_abs"],
        },
        "G2_NUMERIC_LAB_ACTION":{
            "status":"PASS" if finest_action<=thr["action_rel"] else "FAIL",
            "value":finest_action,
            "threshold":thr["action_rel"],
            "n_time":finest,
        },
        "G3_FRAME_GAUGE_ACTION_CLOSURE":{
            "status":"PASS" if finest_frame<=thr["frame_rel"] else "FAIL",
            "value":finest_frame,
            "threshold":thr["frame_rel"],
            "n_time":finest,
        },
        "G4_GENERALIZED_ACTION_A_EQUALS_G":{
            "status":"PASS" if gen_err<=thr["identity_rel"] else "FAIL",
            "value":gen_err,
            "threshold":thr["identity_rel"],
        },
        "G5_FINITE_PULSE_ACTION_ZERO_LIMIT":{
            "status":"PASS" if fp_err<=thr["identity_rel"] else "FAIL",
            "value":fp_err,
            "threshold":thr["identity_rel"],
        },
        "G6_BLIND_GEOMETRY_INTEGRITY":{
            "status":"PASS" if hash_mismatches==0 else "FAIL",
            "hash_mismatches":hash_mismatches,
            "source_identity_read":False,
            "private_mapping_read":False,
        },
        "G7_REVEAL_TARGET_LEAK_SCAN":leak,
    }
    primary_pass=all(g["status"]=="PASS" for g in gates.values())

    _write_csv(blind/f"carrier_metrics_{mode}.csv",metric_rows)
    _write_csv(blind/f"action_convergence_{mode}.csv",action_rows)
    _write_csv(blind/f"sealed_action_prediction_{mode}.csv",[
        {
            "T_s":float(Tv),
            "action_prediction_J_s":float(Sv),
            "legacy_echo_phase_prediction_rad":float(pv),
        }
        for Tv,Sv,pv in zip(T,S,phase_echo)
    ])

    result={
        "format":"SST-QGI-STRICT-BLIND-RUN-1.1",
        "mode":mode,
        "backend":"cpp-pybind11" if _native_available() else "numpy-fallback",
        "source_identity_read":False,
        "reveal_target_read":False,
        "n_candidates":len(metric_rows),
        "action_fit":{
            "p":p_action,
            "prefactor_abs_J_s_per_s3":A_action,
        },
        "legacy_echo_control":{
            "classification":"ALGEBRAIC_ECHO_CONTROL",
            "h_echo_J_s":h_echo,
            "hbar_echo_J_s":hbar_echo,
            "phase_fit_p":p_phase_echo,
            "phase_fit_prefactor_abs":A_phase_echo,
            "independent_prediction":False,
            "provenance":provenance_audit(),
        },
        "gates":gates,
        "blind_verdict":"STRICT_TARGET_BLIND_MACRO_ACTION_PASS" if primary_pass else "BLIND_FALSIFIER_HIT",
        "interpretation":(
            "No Planck target is used. The legacy h-like SST number is explicitly "
            "classified as an algebraic echo control, not a discovery or independent prediction."
        ),
    }
    dump_json(blind/f"gate_report_{mode}.json",result)

    if mode=="extended":
        _extended_sweeps(cfg,blind,m,g)

    return result

def _native_available():
    try:
        import sst_qgi_native
        return True
    except Exception:
        return False

def _extended_sweeps(cfg,blind,m,g):
    T=np.array(cfg["physics"]["T_s"],dtype=float)
    rows=[]
    for ratio in cfg["physics"]["a_over_g"]:
        a=float(ratio)*g
        S=generalized_action(a,T,m,g)
        for Tv,s in zip(T,S):
            rows.append({"a_over_g":float(ratio),"T_s":float(Tv),"action_J_s":float(s)})
    _write_csv(blind/"generalized_acceleration_action_sweep.csv",rows)

    fp_rows=[]
    for tk in cfg["physics"]["Tkick_s"]:
        for td in cfg["physics"]["Td_s"]:
            S=finite_pulse_action(T,float(tk),float(td),m,g)
            for Tv,s in zip(T,S):
                fp_rows.append({
                    "Tkick_s":float(tk),
                    "Td_s":float(td),
                    "T_s":float(Tv),
                    "action_J_s":float(s),
                })
    _write_csv(blind/"finite_pulse_action_sweep.csv",fp_rows)
