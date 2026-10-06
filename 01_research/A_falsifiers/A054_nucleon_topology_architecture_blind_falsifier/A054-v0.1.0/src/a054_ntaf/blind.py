from __future__ import annotations
from pathlib import Path
import json,hashlib
import numpy as np
from .blind_geometry import load_components_npz,resample_closed_curve,rotate_components
from .physics import evaluate_static,evaluate_dynamic,backend_name,fibonacci_sphere
from .seal import sha256_file


def _rotation():
    a=np.array([0.37,-0.61,0.70]); a=a/np.linalg.norm(a); th=0.731
    K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3)+np.sin(th)*K+(1-np.cos(th))*(K@K)

def _load_config(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def run_blind(campaign:Path,config_path:Path):
    if "_private" in str(config_path).lower(): raise RuntimeError("blind code refuses private paths")
    manifest=json.loads((campaign/"BLIND_MANIFEST.json").read_text(encoding="utf-8")); cfg=_load_config(config_path)
    results=[]; R=_rotation(); far_dirs=fibonacci_sphere(96)
    for row in manifest["candidates"]:
        p=campaign/"blind_inputs"/row["file"]
        if sha256_file(p)!=row["sha256"]: raise RuntimeError("blind input hash mismatch")
        base=load_components_npz(p)
        for n in cfg["resolutions"]:
            comps=[resample_closed_curve(c,n) for c in base]
            for core_ratio in cfg["core_ratios"]:
                for sector in cfg.get("circulation_sectors",["Q0","Q1","Q2","Q3","Q4","Q5","Q6","Q7"]):
                    s=evaluate_static(comps,core_ratio,sector,far_dirs=far_dirs)
                    # SO(3) objectivity rotates both source and measurement frame.
                    sr=evaluate_static(rotate_components(comps,R),core_ratio,sector,far_dirs=far_dirs@R.T)
                    obj=max(abs(s[k]-sr[k]) for k in ("rel_eq_residual","farfield_anisotropy_r6","cross_stabilization"))
                    rec={"anonymous_id":row["anonymous_id"],"N":n,"core_ratio":core_ratio,"sector":sector,**s,"objectivity_delta":obj}
                    if cfg.get("dynamic_steps",0)>0:
                        # Dimensionless dt; no SST constant or mass target is consumed.
                        try:
                            dyn,_=evaluate_dynamic(comps,core_ratio,sector,cfg["dt"],cfg["dynamic_steps"]); rec.update(dyn)
                        except Exception as e:
                            rec.update({"shape_drift":None,"linking_drift_max":None,"finite":False,"dynamic_error":type(e).__name__})
                    results.append(rec)
    rp=campaign/"BLIND_RESULTS.json"; rp.write_text(json.dumps({"schema":"A054-BLIND-RESULTS-1.0","results":results},indent=2),encoding="utf-8")
    analysis=analyze(results,cfg,manifest)
    ap=campaign/"ANALYSIS_BLIND.json"; ap.write_text(json.dumps(analysis,indent=2),encoding="utf-8")
    report=campaign/"REPORT_BLIND.md"; report.write_text(render_report(analysis,manifest),encoding="utf-8")
    seal={"schema":"A054-BLIND-SEAL-1.0","manifest_sha256":sha256_file(campaign/"BLIND_MANIFEST.json"),
          "results_sha256":sha256_file(rp),"analysis_sha256":sha256_file(ap),"report_sha256":sha256_file(report),
          "private_mapping_commitment":manifest["private_mapping_sha256"]}
    (campaign/"BLIND_SEAL.json").write_text(json.dumps(seal,indent=2),encoding="utf-8")
    return analysis

def analyze(results,cfg,manifest):
    per={}
    for r in results: per.setdefault(r["anonymous_id"],[]).append(r)
    summaries={}
    for aid,rows in per.items():
        converged=True; reasons=[]
        by={(r["N"],r["core_ratio"],r["sector"]):r for r in rows}
        Ns=sorted(set(r["N"] for r in rows))
        if len(Ns)>=2:
            for cr in sorted(set(r["core_ratio"] for r in rows)):
                for sec in cfg.get("circulation_sectors",["Q0","Q1","Q2","Q3","Q4","Q5","Q6","Q7"]):
                    a=by.get((Ns[-2],cr,sec)); b=by.get((Ns[-1],cr,sec))
                    if a and b:
                        for k in ("rel_eq_residual","farfield_anisotropy_r6","cross_stabilization"):
                            den=max(abs(b[k]),1e-12); d=abs(a[k]-b[k])/den
                            if d>cfg["convergence_rel_tol"]: converged=False; reasons.append(f"{k}:{d:.3g}")
        obj=max((r["objectivity_delta"] for r in rows),default=np.inf)
        if obj>cfg["objectivity_abs_tol"]: converged=False; reasons.append(f"objectivity:{obj:.3g}")
        finite=all(r.get("finite",True) for r in rows)
        if not finite: converged=False; reasons.append("nonfinite_dynamic")
        status="SURVIVES_BLIND_SCREEN" if converged else "INCONCLUSIVE_NUMERICAL"
        # Hard physical failure only when numerics qualify.
        fine=[r for r in rows if r["N"]==max(Ns)]
        if converged and cfg.get("max_shape_drift") is not None and any(r.get("shape_drift",0)>cfg["max_shape_drift"] for r in fine):
            status="FAIL_DYNAMICAL_CONFINEMENT"; reasons.append("shape_drift")
        if converged and any(r.get("linking_drift_max",0)>cfg["max_linking_drift"] for r in fine):
            status="FAIL_TOPOLOGY_PRESERVATION"; reasons.append("linking_drift")
        summaries[aid]={"status":status,"reasons":reasons,"n_records":len(rows),
            "median_rel_eq":float(np.median([r["rel_eq_residual"] for r in fine])),
            "median_cross_stabilization":float(np.median([r["cross_stabilization"] for r in fine])),
            "median_farfield_anisotropy_r6":float(np.median([r["farfield_anisotropy_r6"] for r in fine])),
            "median_shape_drift":None if not any(r.get("shape_drift") is not None for r in fine) else float(np.median([r["shape_drift"] for r in fine if r.get("shape_drift") is not None]))}
    return {"schema":"A054-BLIND-ANALYSIS-1.0","scientific_ready":manifest["scientific_ready"],"summaries":summaries,
            "semantic_identity_read":False,"private_manifest_read":False,
            "policy":"hard gates + metric table; no weighted winner score","backend":backend_name()}

def render_report(a,m):
    lines=["# A054 v0.1.0 — BLIND report","","No semantic identity table was available to this stage.","",
           f"Scientific-ready full tournament: **{a['scientific_ready']}**","","| anonymous | status | rel-eq | cross-stab | far anisotropy | shape drift |","|---|---|---:|---:|---:|---:|"]
    for k,v in sorted(a["summaries"].items()):
        lines.append(f"| `{k}` | {v['status']} | {v['median_rel_eq']:.6g} | {v['median_cross_stabilization']:.6g} | {v['median_farfield_anisotropy_r6']:.6g} | {v['median_shape_drift'] if v['median_shape_drift'] is not None else 'n/a'} |")
    lines += ["","`INCONCLUSIVE_NUMERICAL` is not a physical FAIL. Reveal must not recompute observables."]
    return "\n".join(lines)+"\n"
