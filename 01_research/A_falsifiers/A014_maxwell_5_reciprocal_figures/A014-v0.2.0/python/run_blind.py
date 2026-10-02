from __future__ import annotations
import argparse,json,shutil,sys,time
from pathlib import Path
import numpy as np
from scipy.sparse import save_npz
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(Path(__file__).resolve().parent))
from maxwell5_native import analyze_geometry as native_analyze, backend_status
from sst_reciprocal.io import load_json,dump_json,load_xyz,flatten_components,native_to_sparse,write_records,read_csv_records
from sst_reciprocal.geometry import assemble_explicit
from sst_reciprocal.gates import analyze_matrix,classify
from sst_reciprocal.linear import gram_spectral,nnls_equilibrium
from sst_reciprocal.convergence import hausdorff_contact_map

DEFAULT_CFG={"sv_rel_tol":1e-9,"chi_kkt_pass":5e-3,"chi_kkt_warn":1e-2,"local_closure_pass":1e-2,"local_closure_warn":5e-2,"sigma_ratio_warn":1e-6,
 "contact_tolerance_fraction":1e-4,"kink_tolerance_fraction":0.015,"local_exclusion_fraction":0.02,"lambda_positive_tol":1e-10,"duplicate_cosine_tol":1e-8,
 "self_stress_lp_samples":16,"projection_count":12,"random_seed":2401864,"refuse_inference_roles":["vortexlab-uniform","uniform-n300","downstream-resample"],
 "allow_derived_contacts_on_resampled":False,"robustness_contact_tolerances":[],"robustness_noise_fractions":[],"robustness_trials_per_noise":0,"robustness_trigger_sigma_ratio":1e-4}

def _native_matrix(P,counts,case,cfg,threads,require_native,contact_tol=None):
    result=native_analyze(P,np.asarray(counts,np.int64),radius=float(case.get("radius") or -1.0),contact_tol=float(cfg["contact_tolerance_fraction"] if contact_tol is None else contact_tol),
                          kink_tol=float(cfg["kink_tolerance_fraction"]),local_exclusion_frac=float(cfg["local_exclusion_fraction"]),threads=int(threads),require_native=require_native)
    A,b=native_to_sparse(result); return A,b,[dict(x) for x in result["contacts"]],[dict(x) for x in result["kinks"]],np.full(A.shape[1],np.nan),dict(result["metrics"])

def _save_native(case_out,A,b,contacts,kinks,native_metrics):
    nd=case_out/"native"; nd.mkdir(parents=True,exist_ok=True); save_npz(nd/"A.npz",A); np.save(nd/"b_length_gradient.npy",b); write_records(nd/"contacts.csv",contacts); write_records(nd/"kinks.csv",kinks); dump_json(nd/"native_metrics.json",native_metrics)

def _quick(A,b,cfg):
    sv,_,_,_=gram_spectral(A,cfg["sv_rel_tol"]); _,_,chi,_=nnls_equilibrium(A,b); ratio=sv["sigma_min_positive"]/(sv["sigma_max"] or 1.0)
    return {"rank":sv["rank"],"right_nullity":sv["right_nullity"],"sigma_ratio":ratio,"chi_kkt":chi,"columns":A.shape[1]}

def _robustness(P,counts,case,cfg,threads,require_native,baseline):
    out={"analysis_level":cfg.get("analysis_level","basic"),"contact_tolerance_sweep":[],"coordinate_perturbation":[]}
    for tol in cfg.get("robustness_contact_tolerances",[]):
        A,b,C,K,_,nm=_native_matrix(P,counts,case,cfg,threads,require_native,contact_tol=float(tol))
        out["contact_tolerance_sweep"].append({"contact_tolerance_fraction":float(tol),"active_strut_count":len(C),"active_kink_count":len(K),"matrix_columns":A.shape[1]})
    ratio=baseline["svd"]["sigma_min_positive"]/(baseline["svd"]["sigma_max"] or 1.0)
    trigger=float(cfg.get("robustness_trigger_sigma_ratio",1e-4))
    if not cfg.get("robustness_noise_fractions") or ratio>=trigger:
        out["coordinate_perturbation_status"]="SKIPPED_NOT_NEAR_SINGULAR" if cfg.get("robustness_noise_fractions") else "DISABLED"
        out["coordinate_perturbation_trigger_sigma_ratio"]=trigger
        return out
    rng=np.random.default_rng(int(cfg.get("random_seed",2401864))); radius=float(case.get("radius") or 1.0); trials=int(cfg.get("robustness_trials_per_noise",3))
    for frac in cfg.get("robustness_noise_fractions",[]):
        for trial in range(trials):
            noise=rng.normal(size=P.shape); norms=np.linalg.norm(noise,axis=1,keepdims=True); noise=noise/np.where(norms>0,norms,1.0); Pp=P+noise*(float(frac)*radius)
            A,b,C,K,_,nm=_native_matrix(Pp,counts,case,cfg,threads,require_native); q=_quick(A,b,cfg); q.update({"noise_fraction_of_radius":float(frac),"trial":trial,"active_strut_count":len(C),"active_kink_count":len(K)}); out["coordinate_perturbation"].append(q)
    out["coordinate_perturbation_status"]="RUN"
    return out

def run_case(root,case,cfg,threads,require_native,result_root):
    cid=case["case_id"]; case_out=result_root/cid; case_out.mkdir(parents=True,exist_ok=True); role=str(case.get("source_role","unknown")).lower(); has_contact=bool(case.get("contact_sidecar"))
    refused=(not has_contact) and any(tok in role for tok in cfg.get("refuse_inference_roles",[])) and not cfg.get("allow_derived_contacts_on_resampled",False)
    if refused:
        m={"case_id":cid,"status":"REFUSED_CONTACT_INFERENCE_ON_RESAMPLED_GEOMETRY","source_role":case.get("source_role"),"reason":"Use original constrained Ridgerunner geometry or explicit contacts."}; dump_json(case_out/"metrics.json",m); return m
    inp=(root/case["path"]).resolve(); counts=case.get("component_counts")
    comps=load_xyz(inp,counts); P=flatten_components(comps); counts=[len(c) for c in comps]; t0=time.time()
    try:
        if not bool(case.get("geometry_qc_pass",True)) and not (case.get("contact_sidecar") or case.get("kink_sidecar")):
            A,b,contacts,kinks,supplied,native_metrics=_native_matrix(P,counts,case,cfg,threads,require_native)
            _save_native(case_out,A,b,contacts,kinks,native_metrics)
            m={"case_id":cid,"group_id":case["group_id"],"resolution":case.get("resolution"),"component_counts":counts,"source_role":case.get("source_role"),
               "geometry_status":case.get("geometry_status"),"input_sha256":case["sha256"],"native":native_metrics,"elapsed_s":time.time()-t0,
               "status":"GEOMETRY_QC_REFUSED_EQUILIBRIUM","gates":{"geometry_provenance_gate":"REFUSED"},
               "reason":"Ridgerunner residual exceeds the preregistered geometry-QC limit; contact inventory is recorded, but equilibrium/rank/self-stress is not interpreted."}
            dump_json(case_out/"metrics.json",m); return m
        if case.get("contact_sidecar") or case.get("kink_sidecar"):
            cp=str((root/case["contact_sidecar"]).resolve()) if case.get("contact_sidecar") else None; kp=str((root/case["kink_sidecar"]).resolve()) if case.get("kink_sidecar") else None
            A,b,contacts,kinks,supplied,native_metrics=assemble_explicit(P,counts,cp,kp)
        else:
            A,b,contacts,kinks,supplied,native_metrics=_native_matrix(P,counts,case,cfg,threads,require_native)
        _save_native(case_out,A,b,contacts,kinks,native_metrics)
        metrics=analyze_matrix(A,b,P,cfg)
        if len(supplied)==A.shape[1] and A.shape[1] and np.all(np.isfinite(supplied)):
            rr=A@supplied-b; chi=float(np.linalg.norm(rr)/(np.linalg.norm(b)+1e-300)); metrics["supplied_multiplier_audit"]={"status":"COMPLETE","chi_kkt":chi,"all_nonnegative":bool(np.all(supplied>=-cfg.get("lambda_positive_tol",1e-10))),"min_multiplier":float(np.min(supplied)),"max_multiplier":float(np.max(supplied))}
        elif len(supplied) and np.any(np.isfinite(supplied)): metrics["supplied_multiplier_audit"]={"status":"PARTIAL_NOT_DECISIVE","known":int(np.count_nonzero(np.isfinite(supplied))),"total":int(len(supplied))}
        else: metrics["supplied_multiplier_audit"]={"status":"NOT_AVAILABLE"}
        metrics.update({"case_id":cid,"group_id":case["group_id"],"resolution":case.get("resolution"),"component_counts":counts,"source_role":case.get("source_role"),"geometry_status":case.get("geometry_status"),"input_sha256":case["sha256"],"native":native_metrics,"elapsed_s":time.time()-t0,"status":"OK"})
        metrics["gates"]=classify(metrics,cfg,bool(case.get("complete_mechanical_model",False)))
        metrics["gates"]["geometry_provenance_gate"]="WARN" if "above-0.05" in str(case.get("geometry_status","")) else "PASS"
        fs=case.get("physical_force_scale_N")
        if fs is None: metrics["physical_reciprocal_face_areas"]={"status":"NOT_APPLICABLE_NO_PREREGISTERED_FORCE_SCALE","guard":"Length-KKT multipliers are not silently reinterpreted as newtons."}
        else:
            Pi=metrics["area_force_identity"]["Pi_star_Pa"]; lam=np.asarray(metrics["nnls"]["lambda"])*float(fs); metrics["physical_reciprocal_face_areas"]={"status":"COMPUTED_FROM_DECLARED_FORCE_SCALE","force_scale_N":float(fs),"areas_m2":[float(x/Pi) for x in lam],"normalized_areas_A_over_Ac":[float(x/metrics["area_force_identity"]["F_swirl_max_N"]) for x in lam]}
        if cfg.get("analysis_level")=="extended": metrics["robustness"]=_robustness(P,counts,case,cfg,threads,require_native,metrics)
        dump_json(case_out/"metrics.json",metrics); return metrics
    except Exception as exc:
        m={"case_id":cid,"status":"CASE_ERROR","error":repr(exc),"elapsed_s":time.time()-t0}; dump_json(case_out/"metrics.json",m); return m

def contacts_for(case_dir):
    return [(float(r["s_norm"]),float(r["t_norm"])) for r in read_csv_records(case_dir/"native"/"contacts.csv")]

def add_convergence(result_root,results,cfg):
    groups={}
    for r in results:
        if r.get("status")=="OK": groups.setdefault(r["group_id"],[]).append(r)
    summary={}
    for gid,rs in groups.items():
        rs.sort(key=lambda x:(x.get("resolution") is None,x.get("resolution") or 0)); pairs=[]
        for a,b in zip(rs,rs[1:]):
            d=hausdorff_contact_map(contacts_for(result_root/a["case_id"]),contacts_for(result_root/b["case_id"])); gate="PASS" if d<=cfg.get("contact_map_hausdorff_pass",5e-3) else ("WARN" if d<=cfg.get("contact_map_hausdorff_warn",2e-2) else "FAIL")
            pairs.append({"case_a":a["case_id"],"case_b":b["case_id"],"contact_map_hausdorff":d,"contact_map_gate":gate,"rank_a":a["svd"]["rank"],"rank_b":b["svd"]["rank"]})
        summary[gid]={"ordered_case_ids":[r["case_id"] for r in rs],"pairs":pairs}
    dump_json(result_root/"convergence.json",summary); return summary

def main():
    ap=argparse.ArgumentParser(description="Run blinded 5_Maxwell reciprocal-stress campaign."); ap.add_argument("campaign"); ap.add_argument("--out",default=None); ap.add_argument("--threads",type=int,default=1); ap.add_argument("--require-native",action="store_true")
    args=ap.parse_args(); root=Path(args.campaign).resolve(); manifest=load_json(root/"blind_manifest.json")
    for bad in (root/"private_blind_key.json",root/"private_key.json"):
        if bad.exists(): raise RuntimeError(f"Refusing blind run: private mapping present inside campaign: {bad}")
    cfg=DEFAULT_CFG.copy(); cfg.update(manifest.get("preregistration") or {}); out=Path(args.out).resolve() if args.out else root/"results"; out.mkdir(parents=True,exist_ok=True); dump_json(out/"frozen_preregistration.json",cfg)
    stat=backend_status(); print(f"[5_Maxwell] backend={stat['backend']} threads={args.threads} cases={len(manifest['cases'])}")
    if args.require_native and not stat["available"]: raise RuntimeError("Native backend required; run 5_run_install.cmd")
    results=[]
    for i,case in enumerate(manifest["cases"],1): print(f"[5_Maxwell {i}/{len(manifest['cases'])}] {case['case_id']}"); results.append(run_case(root,case,cfg,args.threads,args.require_native,out))
    conv=add_convergence(out,results,cfg)
    agg={"package":"5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0","preset":manifest.get("preset"),"case_count":len(results),"ok_count":sum(r.get("status")=="OK" for r in results),"error_count":sum(r.get("status") not in ("OK","GEOMETRY_QC_REFUSED_EQUILIBRIUM") for r in results),"geometry_qc_refused_count":sum(r.get("status")=="GEOMETRY_QC_REFUSED_EQUILIBRIUM" for r in results),
         "equilibrium_pass":sum(r.get("gates",{}).get("equilibrium_gate")=="PASS" for r in results),"equilibrium_warn":sum(r.get("gates",{}).get("equilibrium_gate")=="WARN" for r in results),"equilibrium_fail":sum(r.get("gates",{}).get("equilibrium_gate")=="FAIL" for r in results),
         "near_singular_warn_count":sum(r.get("gates",{}).get("near_singular_gate")=="WARN" for r in results),"positive_self_stress_count":sum(r.get("positive_self_stress",{}).get("feasible",False) for r in results),"group_count":len(conv),"backend":stat,"threads":args.threads}
    dump_json(out/"blind_summary.json",agg); print(json.dumps(agg,indent=2))

if __name__=="__main__": main()
