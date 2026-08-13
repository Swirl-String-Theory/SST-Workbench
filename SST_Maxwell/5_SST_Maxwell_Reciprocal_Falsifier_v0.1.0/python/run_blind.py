from __future__ import annotations
import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sst_reciprocal.io import load_json, dump_json, load_xyz, flatten_components, load_native_matrix, read_csv_records
from sst_reciprocal.gates import analyze_matrix, classify
from sst_reciprocal.convergence import hausdorff_contact_map

DEFAULT_CFG={
 "sv_rel_tol":1e-9,"chi_kkt_pass":5e-3,"chi_kkt_warn":1e-2,
 "local_closure_pass":1e-2,"local_closure_warn":5e-2,
 "sigma_ratio_warn":1e-6,"contact_tolerance_fraction":0.015,"kink_tolerance_fraction":0.015,"local_exclusion_fraction":0.02,
 "lambda_positive_tol":1e-10,"duplicate_cosine_tol":1e-8,"self_stress_lp_samples":16,
 "contact_map_hausdorff_pass":5e-3,"contact_map_hausdorff_warn":2e-2,
 "random_seed":2401864,
 "refuse_inference_roles":["vortexlab-uniform","uniform-n300","downstream-resample"],
 "allow_derived_contacts_on_resampled":False
}

def find_native(root:Path, explicit:str|None):
    if explicit:
        p=Path(explicit); return p
    cand=[root/"build"/"sst_reciprocal_core",root/"build"/"Release"/"sst_reciprocal_core.exe",root/"build"/"sst_reciprocal_core.exe"]
    for p in cand:
        if p.exists(): return p
    raise FileNotFoundError("native core not found; run build_native first or pass --native")

def run_case(root,case,cfg,native,result_root):
    cid=case["case_id"]; case_out=result_root/cid; native_out=case_out/"native"; native_out.mkdir(parents=True,exist_ok=True)
    role=str(case.get("source_role","unknown")).lower()
    has_contact_sidecar=bool(case.get("contact_sidecar"))
    refused=(not has_contact_sidecar) and any(tok in role for tok in cfg.get("refuse_inference_roles",[])) and not cfg.get("allow_derived_contacts_on_resampled",False)
    if refused:
        m={"case_id":cid,"status":"REFUSED_CONTACT_INFERENCE_ON_RESAMPLED_GEOMETRY","source_role":case.get("source_role"),
           "reason":"Contact/KKT audit must use the original constrained Ridgerunner audit geometry or an explicit contact sidecar; downstream uniform resampling is not silently promoted."}
        dump_json(case_out/"metrics.json",m); return m
    inp=(root/case["path"]).resolve()
    cmd=[str(native),"--input",str(inp),"--out",str(native_out),"--contact-tol",str(cfg["contact_tolerance_fraction"]),"--kink-tol",str(cfg["kink_tolerance_fraction"]),"--local-exclusion-frac",str(cfg["local_exclusion_fraction"])]
    if case.get("radius") is not None: cmd += ["--radius",str(case["radius"])]
    if case.get("contact_sidecar"): cmd += ["--contacts-sidecar",str((root/case["contact_sidecar"]).resolve())]
    if case.get("kink_sidecar"): cmd += ["--kinks-sidecar",str((root/case["kink_sidecar"]).resolve())]
    t=time.time(); proc=subprocess.run(cmd,capture_output=True,text=True)
    if proc.returncode!=0:
        m={"case_id":cid,"status":"NATIVE_ERROR","stdout":proc.stdout,"stderr":proc.stderr,"command":cmd}; dump_json(case_out/"metrics.json",m); return m
    A,b=load_native_matrix(native_out); comps=load_xyz(inp); points=flatten_components(comps)
    metrics=analyze_matrix(A,b,points,cfg)
    # Independent audit of solver-supplied KKT multipliers, when the sidecars provide them.
    mult=np.full(A.shape[1],np.nan,dtype=float)
    for fn in ("contacts.csv","kinks.csv"):
        for row in read_csv_records(native_out/fn):
            v=row.get("supplied_multiplier","")
            if v not in (None,""):
                mult[int(row["column"])]=float(v)
    known=np.isfinite(mult)
    if A.shape[1] and np.all(known):
        rr=A@mult-b; chi=float(np.linalg.norm(rr)/(np.linalg.norm(b)+1e-300))
        metrics["supplied_multiplier_audit"]={"status":"COMPLETE","chi_kkt":chi,"all_nonnegative":bool(np.all(mult>=-cfg.get("lambda_positive_tol",1e-10))),"min_multiplier":float(np.min(mult)),"max_multiplier":float(np.max(mult))}
    elif np.any(known):
        metrics["supplied_multiplier_audit"]={"status":"PARTIAL_NOT_DECISIVE","known":int(np.count_nonzero(known)),"total":int(len(mult)),"all_known_nonnegative":bool(np.all(mult[known]>=-cfg.get("lambda_positive_tol",1e-10)))}
    else:
        metrics["supplied_multiplier_audit"]={"status":"NOT_AVAILABLE"}
    native_metrics=load_json(native_out/"native_metrics.json")
    metrics.update({"case_id":cid,"group_id":case["group_id"],"resolution":case.get("resolution"),"source_role":case.get("source_role"),
                    "geometry_status":case.get("geometry_status"),"input_sha256":case["sha256"],"native":native_metrics,
                    "elapsed_s":time.time()-t,"status":"OK"})
    metrics["gates"]=classify(metrics,cfg,bool(case.get("complete_mechanical_model",False)))
    # Physical face-area mapping is allowed only if a physical force scale was declared before unblinding.
    fs=case.get("physical_force_scale_N")
    if fs is None:
        metrics["physical_reciprocal_face_areas"]={"status":"NOT_APPLICABLE_NO_PREREGISTERED_FORCE_SCALE",
          "guard":"NNLS multipliers for length minimization are not silently reinterpreted as newtons."}
    else:
        Pi=metrics["area_force_identity"]["Pi_star_Pa"]
        lam=np.asarray(metrics["nnls"]["lambda"])*float(fs)
        metrics["physical_reciprocal_face_areas"]={"status":"COMPUTED_FROM_DECLARED_FORCE_SCALE","force_scale_N":float(fs),
          "areas_m2":[float(x/Pi) for x in lam],"normalized_areas_A_over_Ac":[float(x/metrics["area_force_identity"]["F_swirl_max_N"]) for x in lam]}
    dump_json(case_out/"metrics.json",metrics)
    return metrics

def contacts_for(case_dir):
    rows=read_csv_records(case_dir/"native"/"contacts.csv")
    return [(float(r["s_norm"]),float(r["t_norm"])) for r in rows]

def add_convergence(result_root,results,cfg):
    groups={}
    for r in results:
        if r.get("status")!="OK": continue
        groups.setdefault(r["group_id"],[]).append(r)
    summary={}
    for gid,rs in groups.items():
        rs.sort(key=lambda x:(x.get("resolution") is None, x.get("resolution") or 0))
        pairs=[]
        for a,b in zip(rs,rs[1:]):
            d=hausdorff_contact_map(contacts_for(result_root/a["case_id"]),contacts_for(result_root/b["case_id"]))
            if d<=cfg["contact_map_hausdorff_pass"]: gate="PASS"
            elif d<=cfg["contact_map_hausdorff_warn"]: gate="WARN"
            else: gate="FAIL"
            sa=a["svd"]; sb=b["svd"]
            pairs.append({"case_a":a["case_id"],"case_b":b["case_id"],"resolution_a":a.get("resolution"),"resolution_b":b.get("resolution"),
                          "contact_map_hausdorff":d,"contact_map_gate":gate,
                          "rank_a":sa["rank"],"rank_b":sb["rank"],"sigma_ratio_a":sa["sigma_min_positive"]/(sa["sigma_max"] or 1),
                          "sigma_ratio_b":sb["sigma_min_positive"]/(sb["sigma_max"] or 1),
                          "positive_self_stress_a":a["positive_self_stress"]["feasible"],"positive_self_stress_b":b["positive_self_stress"]["feasible"]})
        summary[gid]={"ordered_case_ids":[r["case_id"] for r in rs],"pairs":pairs}
    dump_json(result_root/"convergence.json",summary); return summary

def main():
    ap=argparse.ArgumentParser(description="Run the preregistered Maxwell-SST reciprocal-stress falsifier without case identities.")
    ap.add_argument("campaign",help="blind campaign directory")
    ap.add_argument("--native")
    ap.add_argument("--out",default=None)
    args=ap.parse_args(); root=Path(args.campaign).resolve(); manifest=load_json(root/"blind_manifest.json")
    # Refuse accidental unblinding material in the run directory.
    for bad in [root/"private_blind_key.json",root/"private_key.json"]:
        if bad.exists(): raise RuntimeError(f"Refusing blind run because private mapping is present: {bad}")
    cfg=DEFAULT_CFG.copy(); cfg.update(manifest.get("preregistration") or {})
    native=find_native(Path(__file__).resolve().parents[1],args.native)
    out=Path(args.out).resolve() if args.out else root/"results"; out.mkdir(parents=True,exist_ok=True)
    dump_json(out/"frozen_preregistration.json",cfg)
    results=[]
    for case in manifest["cases"]:
        print(f"[{case['case_id']}] running")
        results.append(run_case(root,case,cfg,native,out))
    conv=add_convergence(out,results,cfg)
    aggregate={"case_count":len(results),"ok_count":sum(r.get("status")=="OK" for r in results),
               "fail_equilibrium_count":sum(r.get("gates",{}).get("equilibrium_gate")=="FAIL" for r in results),
               "near_singular_warn_count":sum(r.get("gates",{}).get("near_singular_gate")=="WARN" for r in results),
               "positive_self_stress_count":sum(r.get("positive_self_stress",{}).get("feasible",False) for r in results),
               "group_count":len(conv)}
    dump_json(out/"blind_summary.json",aggregate)
    print(json.dumps(aggregate,indent=2))

if __name__=="__main__": main()
