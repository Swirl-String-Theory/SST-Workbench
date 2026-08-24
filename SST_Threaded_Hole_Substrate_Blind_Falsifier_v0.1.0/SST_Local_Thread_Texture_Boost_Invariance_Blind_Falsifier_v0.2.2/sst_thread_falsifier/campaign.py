from __future__ import annotations
import csv, hashlib, json, platform, secrets, sys, time
from pathlib import Path
import numpy as np

from .io import discover_dataset, load_components
from .geometry import resample_components, radius_gyration, kabsch_rms, metrics, random_rotation
from .threads import (fibonacci_directions, secondary_direction, make_local_thread_bundle,
                      combine_bundles, transform_bundle, closure_diagnostics)
from .diagnostics import field_solenoidal_diagnostics, background_field_relative_difference
from .native_ext.core import evolve_frozen_background, backend_name
from .constants import SST_CANONICAL


def _canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def _sha_bytes(b): return hashlib.sha256(b).hexdigest()
def _sha_file(p): return _sha_bytes(Path(p).read_bytes())
def _write_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def _unit(rng):
    x=rng.normal(size=3); n=float(np.linalg.norm(x)); return x/(n if n else 1.0)

def _geom_velocity_scale(gamma,rg): return abs(float(gamma))/(4*np.pi*max(float(rg),1e-15))
def _empty_bundle(): return {"points":np.zeros((0,3),float),"offsets":np.asarray([0],np.int64),"gammas":np.zeros(0,float)}

def _case_payload(P,O,bundle,boost,dt,steps,knot_core,thread_core,gamma,rg_ref,source_hash):
    return dict(
        points=np.asarray(P,np.float64), offsets=np.asarray(O,np.int64),
        thread_points=np.asarray(bundle["points"],np.float64),
        thread_offsets=np.asarray(bundle["offsets"],np.int64),
        thread_gammas=np.asarray(bundle["gammas"],np.float64),
        boost=np.asarray(boost,np.float64), dt=np.float64(dt), steps=np.int64(steps),
        knot_core_radius=np.float64(knot_core), thread_core_radius=np.float64(thread_core),
        gamma=np.float64(gamma), rg_reference=np.float64(rg_ref), source_file_hash=np.asarray(source_hash)
    )

def _load_case(path):
    z=np.load(path,allow_pickle=False)
    return {k:np.asarray(z[k]) for k in z.files}


def prepare_blind(config,dataset,out_dir):
    out=Path(out_dir); blind=out/"blind"; cases_dir=blind/"cases"; secret_dir=out/"secret"
    cases_dir.mkdir(parents=True,exist_ok=True); secret_dir.mkdir(parents=True,exist_ok=True)
    seed=int(config["blind_seed"]); rng=np.random.default_rng(seed)
    files=discover_dataset(dataset,int(config.get("max_files",0)))
    if not files: raise RuntimeError(f"no supported geometry files under {dataset}")

    # One hidden orientation set is shared across every topology: no orientation confounding.
    M=max(1,int(config.get("orientation_count",3)))
    phase=float(rng.uniform(0,2*np.pi)); dirs=fibonacci_directions(M,phase)
    Rhidden=random_rotation(rng); dirs=dirs@Rhidden.T
    order=rng.permutation(M); dirs=dirs[order]
    cov_R=random_rotation(rng); cov_tdir=_unit(rng); boost_dir=_unit(rng)
    secondary_phase=float(rng.uniform(0,2*np.pi)); gradient_phase=float(rng.uniform(0,2*np.pi)); return_phase=float(rng.uniform(0,2*np.pi))

    precommit={
        "package_version":"0.2.2","created_unix":time.time(),"config":config,
        "config_sha256":_sha_bytes(_canonical(config).encode()),"dataset_root":str(Path(dataset).resolve()),
        "dataset_files":[{"path":str(p),"sha256":_sha_file(p)} for p in files],
        "model_commitment":{
            "background":"explicit closed vortex filaments; local large-source-radius patch",
            "evolution":"multi-step RK2; nonlinear knot self-field recomputed every substep; source-anchored frozen thread geometry",
            "boost":"common boost advects knot and complete thread substrate together",
            "core":"fixed physical/geometric core radius relative to a resolution-independent reference Rg",
            "return_flux":"remote closed return legs; locality tested by moving the return closure outward",
            "orientation_control":"same hidden direction set for every topology",
        },
        "epistemic_status":{
            "G0_G5":"STRUCTURAL / NUMERICAL NECESSITY",
            "G6_G9":"CONDITIONAL DYNAMICAL THREAD BRIDGES",
            "claim":"A bridge PASS is not a derivation of SST gravity or a calibration to Earth/Sun SI scales."
        },
        "sst_canonical_constants":SST_CANONICAL,
    }
    _write_json(out/"precommit.json",precommit)

    case_records=[]; group_records=[]; secret_map={"datasets":{},"groups":{},"orientation_vectors":dirs.tolist()}
    case_serial=0; group_serial=0
    nres=int(config["resample_n"]); ref_n=max(int(config.get("reference_rg_n",1024)),nres)
    gamma=float(config.get("gamma",1.0)); steps=int(config.get("steps",8)); dt_frac=float(config.get("dt_fraction",0.01))
    knot_core_ratio=float(config.get("knot_core_radius_rg",0.04)); thread_core_ratio=float(config.get("thread_core_radius_rg",0.06))
    rings=int(config.get("thread_rings",1)); bundle_radius=float(config.get("bundle_radius_rg",1.5)); half_length=float(config.get("local_half_length_rg",4.0))
    return_base=float(config.get("return_distance_rg",24.0)); return_mid=return_base*float(config.get("return_mid_factor",2.0)); return_far=return_base*float(config.get("return_far_factor",4.0))
    local_leg_points=int(config.get("thread_local_leg_points",64)); remote_leg_points=int(config.get("thread_remote_leg_points",32)); arc_points=int(config.get("thread_arc_points",32))
    primary_ratio=float(config.get("primary_thread_gamma_ratio",0.01)); secondary_ratio=float(config.get("secondary_thread_gamma_ratio",0.005))
    grad_strength=float(config.get("density_gradient_strength",0.6)); secondary_angle=float(config.get("secondary_angle_deg",60.0))
    boost_ratio=float(config.get("boost_ratio",0.5)); translate_rg=float(config.get("covariance_translation_rg",11.0))

    def new_case(dataset_key,role,P,O,bundle,boost,dt,kcore,tcore,rg_ref,src_hash):
        nonlocal case_serial
        case_serial+=1; cid=f"C{case_serial:06d}"; fn=cases_dir/f"{cid}.npz"
        np.savez_compressed(fn,**_case_payload(P,O,bundle,boost,dt,steps,kcore,tcore,gamma,rg_ref,src_hash))
        case_records.append({"case_id":cid,"file":str(fn.relative_to(out)),"sha256":_sha_file(fn),"dataset_key":dataset_key})
        secret_map["datasets"].setdefault(dataset_key,{"roles":{}})["roles"][role]=cid
        return cid
    def new_group(dataset_key,role,case_ids,expectation):
        nonlocal group_serial
        group_serial+=1; gid=f"G{group_serial:06d}"
        group_records.append({"group_id":gid,"case_ids":list(case_ids),"expectation":expectation,"dataset_key":dataset_key})
        secret_map["groups"][gid]=f"{dataset_key}:{role}"; return gid

    accepted=0; skipped=[]
    for p in files:
        try:
            comps=load_components(p)
            P,O=resample_components(comps,nres)
            Pref,_=resample_components(comps,ref_n)
            rg_ref=radius_gyration(Pref)
            if not np.isfinite(rg_ref) or rg_ref<=0: raise ValueError("invalid reference Rg")
            c=np.mean(P,axis=0); u0=_geom_velocity_scale(gamma,rg_ref); dt=dt_frac*rg_ref/max(u0,1e-15)
            kcore=max(knot_core_ratio*rg_ref,1e-15); tcore=max(thread_core_ratio*rg_ref,1e-15)
            key=f"D{accepted:04d}"; src_hash=_sha_file(p)
            secret_map["datasets"][key]={
                "source_path":str(p),"source_sha256":src_hash,"roles":{},"rg_reference_input_units":rg_ref,
                "resample_n":nres,"reference_rg_n":ref_n,"u_geom_input_units_per_time":u0,"dt_input_time":dt,
                "knot_core_radius_input_units":kcore,"thread_core_radius_input_units":tcore,
            }
            c_self=new_case(key,"self",P,O,_empty_bundle(),np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            primary_cases=[]
            for oi,n in enumerate(dirs):
                b=make_local_thread_bundle(c,n,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                    local_half_length_rg=half_length,return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                    gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,gradient_phase=gradient_phase,
                    return_phase=return_phase+0.37*oi)
                cid=new_case(key,f"primary_o{oi:02d}",P,O,b,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
                primary_cases.append(cid); new_group(key,f"primary_response_o{oi:02d}",[c_self,cid],"response")
            # Hard covariance gates use orientation 0.
            n0=dirs[0]
            b0=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                local_half_length_rg=half_length,return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,gradient_phase=gradient_phase,return_phase=return_phase)
            c_primary=primary_cases[0]
            c_dup=new_case(key,"primary_duplicate",P,O,b0,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"repeatability",[c_primary,c_dup],"null")
            U=boost_ratio*u0*boost_dir
            c_boost=new_case(key,"common_boost",P,O,b0,U,dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"common_boost_null",[c_primary,c_boost],"null")
            t=translate_rg*rg_ref*cov_tdir; bt=transform_bundle(b0,translation=t)
            c_trans=new_case(key,"translated_system",P+t,O,bt,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"translation_covariance",[c_primary,c_trans],"null")
            Pr=(P-c)@cov_R.T+c; br=transform_bundle(b0,R=cov_R,center=c)
            c_rot=new_case(key,"rotated_system",Pr,O,br,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"rotation_covariance",[c_primary,c_rot],"null")
            # Density gradient: same closed thread topology, circulation weights vary across the patch.
            bg=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                local_half_length_rg=half_length,return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=grad_strength,gradient_phase=gradient_phase,return_phase=return_phase)
            c_grad=new_case(key,"density_gradient",P,O,bg,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"density_gradient_response",[c_primary,c_grad],"response")
            # Secondary (Sun-like) local bundle at a committed nonparallel angle.
            n2=secondary_direction(n0,secondary_angle,secondary_phase)
            b2=make_local_thread_bundle(c,n2,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                local_half_length_rg=half_length,return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=secondary_ratio*gamma,gradient_strength=0.0,gradient_phase=gradient_phase,
                return_phase=return_phase+1.234)
            bc=combine_bundles(b0,b2)
            c_comb=new_case(key,"primary_plus_secondary",P,O,bc,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"secondary_superposition_response",[c_primary,c_comb],"response")
            # Remote return-flux locality: local outgoing legs unchanged; only closure is moved outward.
            bm=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                local_half_length_rg=half_length,return_distance_rg=return_mid,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,gradient_phase=gradient_phase,return_phase=return_phase)
            bf=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,
                local_half_length_rg=half_length,return_distance_rg=return_far,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,gradient_phase=gradient_phase,return_phase=return_phase)
            c_mid=new_case(key,"return_mid",P,O,bm,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            c_far=new_case(key,"return_far",P,O,bf,np.zeros(3),dt,kcore,tcore,rg_ref,src_hash)
            new_group(key,"return_mid_far",[c_mid,c_far],"return")
            new_group(key,"return_near_mid",[c_primary,c_mid],"diagnostic")
            secret_map["datasets"][key].update({
                "orientation_vectors":dirs.tolist(),"boost_vector":U.tolist(),"translation_vector":t.tolist(),
                "secondary_direction_o00":n2.tolist(),"thread_count_primary":int(len(b0["gammas"])),
                "return_distances_rg":[return_base,return_mid,return_far]
            })
            accepted+=1
        except Exception as e:
            skipped.append({"path":str(p),"reason":repr(e)})
    if accepted==0: raise RuntimeError("all dataset files rejected; inspect parser/report")
    rng.shuffle(case_records); rng.shuffle(group_records)
    blind_manifest={"cases":case_records,"groups":group_records,"accepted_datasets":accepted,"skipped":skipped}
    _write_json(blind/"manifest.json",blind_manifest)
    salt=secrets.token_hex(32); secret_map["salt"]=salt
    commitment=_sha_bytes((salt+_canonical({k:v for k,v in secret_map.items() if k!="salt"})).encode())
    _write_json(secret_dir/"semantic_manifest.json",secret_map)
    _write_json(out/"blind_commitment.json",{
        "semantic_sha256":commitment,"blind_manifest_sha256":_sha_file(blind/"manifest.json"),
        "algorithm":"sha256(salt || canonical_semantic_manifest_without_salt)"})
    return blind_manifest


def run_blind(config,out_dir,force_python=False,skip_build=False):
    out=Path(out_dir); manifest_path=out/"blind/manifest.json"
    commitment=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    if _sha_file(manifest_path)!=commitment["blind_manifest_sha256"]: raise RuntimeError("blind manifest hash mismatch")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")); result_dir=out/"blind/results"; result_dir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for idx,rec in enumerate(manifest["cases"],1):
        case_path=out/rec["file"]
        if _sha_file(case_path)!=rec["sha256"]: raise RuntimeError(f"blinded case hash mismatch: {rec['case_id']}")
        z=np.load(case_path,allow_pickle=False)
        P=np.asarray(z["points"],float); O=np.asarray(z["offsets"],np.int64)
        TP=np.asarray(z["thread_points"],float); TO=np.asarray(z["thread_offsets"],np.int64); TG=np.asarray(z["thread_gammas"],float)
        boost=np.asarray(z["boost"],float); dt=float(z["dt"]); steps=int(z["steps"]); gamma=float(z["gamma"])
        kcore=float(z["knot_core_radius"]); tcore=float(z["thread_core_radius"]); rg_ref=float(z["rg_reference"])
        x1=evolve_frozen_background(P,O,gamma,kcore,TP,TO,TG,tcore,dt,steps,boost,
                                    force_python=force_python,skip_build=skip_build)
        m0=metrics(P,O); m1=metrics(x1,O)
        rr={"case_id":rec["case_id"],"dataset_key":rec["dataset_key"],"backend":"python" if force_python else backend_name(),
            "final_file":f"blind/results/{rec['case_id']}_final.npy","rg_reference":rg_ref,"steps":steps,"dt":dt,
            "metrics0":m0,"metrics_final":m1,"thread_components":int(max(0,len(TO)-1)),
            "thread_abs_gamma_sum":float(np.sum(np.abs(TG))),"boost_norm":float(np.linalg.norm(boost))}
        np.save(out/rr["final_file"],x1); _write_json(result_dir/f"{rec['case_id']}.json",rr); rows.append(rr)
        if idx%50==0: print(f"[SST-THREAD] completed {idx}/{len(manifest['cases'])} blinded cases")
    _write_json(out/"blind_results.json",{"backend":"python" if force_python else backend_name(),"cases":rows})
    return rows


def score_blind(config,out_dir):
    out=Path(out_dir); manifest=json.loads((out/"blind/manifest.json").read_text(encoding="utf-8"))
    recs={x["case_id"]:x for x in json.loads((out/"blind_results.json").read_text(encoding="utf-8"))["cases"]}
    scores=[]
    for g in manifest["groups"]:
        if len(g["case_ids"])!=2: continue
        a,b=g["case_ids"]; A=np.load(out/recs[a]["final_file"]); B=np.load(out/recs[b]["final_file"])
        rg=max(float(recs[a]["rg_reference"]),1e-15); s=kabsch_rms(A,B)/rg
        exp=g["expectation"]
        if exp=="null": status="PASS" if s<=float(config["null_shape_rms_tol_rg"]) else "FAIL"
        elif exp=="response": status="PASS" if s>=float(config["min_thread_response_rg"]) else "FAIL"
        elif exp=="return": status="PASS" if s<=float(config["return_flux_shape_tol_rg"]) else "FAIL"
        else: status="DIAGNOSTIC"
        scores.append({"group_id":g["group_id"],"dataset_key":g["dataset_key"],"expectation":exp,
                       "shape_rms_over_rg":float(s),"blinded_status":status})
    _write_json(out/"blind_score.json",{"scores":scores,"thresholds":{
        "null_shape_rms_tol_rg":config["null_shape_rms_tol_rg"],"min_thread_response_rg":config["min_thread_response_rg"],
        "return_flux_shape_tol_rg":config["return_flux_shape_tol_rg"]}})
    return scores


def unblind(config,out_dir,force_python=False,skip_build=False):
    out=Path(out_dir); secret=json.loads((out/"secret/semantic_manifest.json").read_text(encoding="utf-8"))
    co=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    if _sha_file(out/"blind/manifest.json")!=co["blind_manifest_sha256"]: raise RuntimeError("blind manifest hash mismatch during unblind")
    calc=_sha_bytes((secret["salt"]+_canonical({k:v for k,v in secret.items() if k!="salt"})).encode())
    if calc!=co["semantic_sha256"]: raise RuntimeError("blind semantic commitment mismatch")
    scores={x["group_id"]:x for x in json.loads((out/"blind_score.json").read_text(encoding="utf-8"))["scores"]}
    role_scores={}
    for gid,semantic in secret["groups"].items():
        key,role=semantic.split(":",1); role_scores.setdefault(key,{})[role]=scores[gid]
    manifest=json.loads((out/"blind/manifest.json").read_text(encoding="utf-8")); case_rec={x["case_id"]:x for x in manifest["cases"]}

    reports=[]
    for key,rs in role_scores.items():
        meta=secret["datasets"][key]; roles=meta["roles"]
        primary_id=roles["primary_o00"]; primary_case=_load_case(out/case_rec[primary_id]["file"])
        TP=np.asarray(primary_case["thread_points"],float); TO=np.asarray(primary_case["thread_offsets"],np.int64); TG=np.asarray(primary_case["thread_gammas"],float)
        P=np.asarray(primary_case["points"],float); rg=float(primary_case["rg_reference"]); tcore=float(primary_case["thread_core_radius"])
        closure=closure_diagnostics(TP,TO)
        sol=field_solenoidal_diagnostics(np.mean(P,axis=0),rg,TP,TO,TG,tcore,
            halfwidth_rg=float(config.get("field_probe_halfwidth_rg",0.75)),grid_n=int(config.get("field_probe_grid_n",7)),
            force_python=force_python,skip_build=skip_build)
        close_ok=(closure["endpoint_count"]==0 and closure["closing_edge_over_neighbor_max"]<=float(config.get("closure_neighbor_ratio_tol",1.25)))
        sol_ok=(sol["normalized_div_vorticity"]<=float(config.get("normalized_div_vorticity_tol",1.0e-8)))
        # Return-flux field locality, independent of evolved-shape comparison.
        mid=_load_case(out/case_rec[roles["return_mid"]]["file"]); far=_load_case(out/case_rec[roles["return_far"]]["file"])
        bm={"points":mid["thread_points"],"offsets":mid["thread_offsets"],"gammas":mid["thread_gammas"]}
        bf={"points":far["thread_points"],"offsets":far["thread_offsets"],"gammas":far["thread_gammas"]}
        field_rel=background_field_relative_difference(P,bm,bf,tcore,force_python=force_python,skip_build=skip_build)
        return_shape=rs["return_mid_far"]["shape_rms_over_rg"]
        return_ok=(return_shape<=float(config["return_flux_shape_tol_rg"]) and field_rel<=float(config["return_flux_field_relative_tol"]))

        orient=[]
        oi=0
        while f"primary_response_o{oi:02d}" in rs:
            orient.append(rs[f"primary_response_o{oi:02d}"]["shape_rms_over_rg"]); oi+=1
        orient=np.asarray(orient,float)
        frac=float(np.mean(orient>=float(config["min_thread_response_rg"]))) if len(orient) else 0.0
        g6_ok=bool(len(orient) and np.median(orient)>=float(config["min_thread_response_rg"]))
        g7=rs["density_gradient_response"]; g7_ok=g7["shape_rms_over_rg"]>=float(config.get("min_gradient_response_rg",config["min_thread_response_rg"]))
        g8=rs["secondary_superposition_response"]; g8_ok=g8["shape_rms_over_rg"]>=float(config.get("min_secondary_response_rg",config["min_thread_response_rg"]))
        g9_ok=frac>=float(config.get("min_orientation_response_fraction",0.5))
        structural_roles=["repeatability","common_boost_null","translation_covariance","rotation_covariance"]
        covariance_ok=all(rs[r]["blinded_status"]=="PASS" for r in structural_roles)
        structural_ok=bool(covariance_ok and close_ok and sol_ok and return_ok)
        bridge_ok=bool(g6_ok and g7_ok and g8_ok and g9_ok)
        gates={
            "G0_repeatability":{"status":rs["repeatability"]["blinded_status"],**rs["repeatability"]},
            "G1_common_boost_null":{"status":rs["common_boost_null"]["blinded_status"],**rs["common_boost_null"]},
            "G2_translation_covariance":{"status":rs["translation_covariance"]["blinded_status"],**rs["translation_covariance"]},
            "G3_rotation_covariance":{"status":rs["rotation_covariance"]["blinded_status"],**rs["rotation_covariance"]},
            "G4_closed_solenoidal_threads":{
                "status":"PASS" if close_ok and sol_ok else "FAIL","epistemic":"STRUCTURAL_NECESSITY",
                "closure":closure,"field_solenoidal":sol,
                "thresholds":{"closure_neighbor_ratio_tol":config.get("closure_neighbor_ratio_tol",1.25),
                    "normalized_div_velocity_note":"finite-difference diagnostic near regularized cores; not used as hard gate",
                    "normalized_div_vorticity_tol":config.get("normalized_div_vorticity_tol",1.0e-8)}},
            "G5_return_flux_locality":{
                "status":"PASS" if return_ok else "FAIL","epistemic":"STRUCTURAL_LOCALITY",
                "mid_far_final_shape_rms_over_rg":return_shape,"mid_far_initial_field_relative_l2":field_rel,
                "shape_tol_rg":config["return_flux_shape_tol_rg"],"field_relative_tol":config["return_flux_field_relative_tol"]},
            "G6_primary_bundle_dynamical_response":{
                "status":"PASS" if g6_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE",
                "orientation_responses_rms_over_rg":orient.tolist(),"median":float(np.median(orient)) if len(orient) else None,
                "min":float(np.min(orient)) if len(orient) else None,"max":float(np.max(orient)) if len(orient) else None,
                "threshold":config["min_thread_response_rg"]},
            "G7_density_gradient_differential_response":{"status":"PASS" if g7_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE",**g7,
                "threshold":config.get("min_gradient_response_rg",config["min_thread_response_rg"])},
            "G8_primary_secondary_superposition_response":{"status":"PASS" if g8_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE",**g8,
                "threshold":config.get("min_secondary_response_rg",config["min_thread_response_rg"])},
            "G9_orientation_robustness":{"status":"PASS" if g9_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE",
                "passing_fraction":frac,"required_fraction":config.get("min_orientation_response_fraction",0.5),"count":int(len(orient))},
        }
        reports.append({"dataset_key":key,"source_path":meta["source_path"],"structural_status":"PASS" if structural_ok else "FAIL",
                        "conditional_bridge_status":"PASS" if bridge_ok else "FAIL","gates":gates,
                        "fixed_core":{"rg_reference":meta["rg_reference_input_units"],"knot_core_radius":meta["knot_core_radius_input_units"],
                                      "thread_core_radius":meta["thread_core_radius_input_units"],"reference_rg_n":meta["reference_rg_n"]}})
    overall_struct="PASS" if all(r["structural_status"]=="PASS" for r in reports) else "FAIL"
    overall_bridge="PASS" if all(r["conditional_bridge_status"]=="PASS" for r in reports) else "FAIL"
    report={"commitment_verified":True,"overall_structural_status":overall_struct,"overall_conditional_bridge_status":overall_bridge,
            "scientific_classification":("STRUCTURAL_PASS__BRIDGE_PASS" if overall_struct=="PASS" and overall_bridge=="PASS" else
                "STRUCTURAL_PASS__BRIDGE_FAIL" if overall_struct=="PASS" else "STRUCTURAL_FAIL"),
            "interpretation":"G0-G5 test covariance, closed/solenoidal explicit vortex-thread construction and return-flux locality. G6-G9 are conditional dynamical responses of a committed filament model; they do not calibrate or derive SST gravity.",
            "datasets":reports,"orientation_vectors_hidden_until_unblind":secret.get("orientation_vectors",[]),
            "provenance":{"python":sys.version,"platform":platform.platform(),"backend":json.loads((out/"blind_results.json").read_text())["backend"]},
            "sst_canonical_constants":SST_CANONICAL}
    _write_json(out/"unblinded_report.json",report)
    with (out/"summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["dataset_key","source_path","structural_status","bridge_status","boost_null_rms_rg","return_shape_rms_rg","return_field_rel","primary_median_response_rg","gradient_response_rg","secondary_response_rg","orientation_pass_fraction"])
        for d in reports:
            g=d["gates"]; w.writerow([d["dataset_key"],d["source_path"],d["structural_status"],d["conditional_bridge_status"],
                g["G1_common_boost_null"]["shape_rms_over_rg"],g["G5_return_flux_locality"]["mid_far_final_shape_rms_over_rg"],
                g["G5_return_flux_locality"]["mid_far_initial_field_relative_l2"],g["G6_primary_bundle_dynamical_response"]["median"],
                g["G7_density_gradient_differential_response"]["shape_rms_over_rg"],g["G8_primary_secondary_superposition_response"]["shape_rms_over_rg"],
                g["G9_orientation_robustness"]["passing_fraction"]])
    return report


def run_full(config_path,dataset,out_dir,force_python=False,skip_build=False):
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    prepare_blind(config,dataset,out_dir)
    run_blind(config,out_dir,force_python,skip_build)
    score_blind(config,out_dir)
    return unblind(config,out_dir,force_python,skip_build)
