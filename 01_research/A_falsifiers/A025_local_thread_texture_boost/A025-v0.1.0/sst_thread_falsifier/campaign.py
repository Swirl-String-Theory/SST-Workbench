from __future__ import annotations
import csv, hashlib, json, os, platform, secrets, sys, time
from pathlib import Path
import numpy as np
from .io import discover_dataset, load_components
from .geometry import resample_components, radius_gyration, kabsch_rms, metrics, random_rotation
from .backgrounds import zero, uniform_boost, point_source_radial, director_affine
from .native_ext.core import biot_savart, backend_name
from .constants import SST_CANONICAL


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)


def _sha_bytes(b): return hashlib.sha256(b).hexdigest()
def _sha_file(p): return _sha_bytes(Path(p).read_bytes())
def _write_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")


def _unit(rng):
    x=rng.normal(size=3); n=np.linalg.norm(x)
    return x/(n if n else 1.0)


def _geom_velocity_scale(gamma, rg):
    return abs(float(gamma))/(4*np.pi*max(float(rg),1e-15))


def _case_payload(points, offsets, bg, dt, core_radius, gamma, source_file_hash):
    return dict(points=np.asarray(points,np.float64), offsets=np.asarray(offsets,np.int64),
                background=np.asarray(bg,np.float64), dt=np.float64(dt),
                core_radius=np.float64(core_radius), gamma=np.float64(gamma),
                source_file_hash=np.asarray(source_file_hash))


def prepare_blind(config, dataset, out_dir):
    out=Path(out_dir); blind=out/"blind"; cases_dir=blind/"cases"; secret_dir=out/"secret"
    cases_dir.mkdir(parents=True,exist_ok=True); secret_dir.mkdir(parents=True,exist_ok=True)
    seed=int(config["blind_seed"])
    rng=np.random.default_rng(seed)
    files=discover_dataset(dataset,int(config.get("max_files",0)))
    if not files: raise RuntimeError(f"no supported geometry files under {dataset}")
    precommit={
        "package_version":"0.1.0", "created_unix":time.time(),
        "config":config, "config_sha256":_sha_bytes(_canonical(config).encode()),
        "dataset_root":str(Path(dataset).resolve()),
        "dataset_files":[{"path":str(p),"sha256":_sha_file(p)} for p in files],
        "epistemic_status":{
            "uniform_boost_gate":"STRUCTURAL_NULL",
            "radial_source_flow":"CONDITIONAL_BRIDGE",
            "director_affine":"CONDITIONAL_BRIDGE",
            "claim":"Passing bridge gates is not a derivation of SST or Lorentz symmetry."
        },
        "sst_canonical_constants":SST_CANONICAL,
    }
    _write_json(out/"precommit.json",precommit)

    case_records=[]; group_records=[]; secret_map={"datasets":{},"groups":{}}
    case_serial=0; group_serial=0
    nres=int(config["resample_n"]); gamma=float(config.get("gamma",1.0))
    eps=float(config["texture_ratio"]); boost_ratio=float(config["boost_ratio"])
    dt_frac=float(config["dt_fraction"]); source_D=float(config["source_distance_rg"])
    dir_D=float(config.get("director_ratio",eps)); core_ds=float(config["core_radius_ds"])
    low_factor=float(config.get("linearity_low_factor",0.5))
    translate_rg=float(config.get("covariance_translation_rg",7.0))

    def new_case(dataset_key, role, P, O, bg, dt, core, src_hash):
        nonlocal case_serial
        case_serial+=1
        cid=f"C{case_serial:06d}"
        fn=cases_dir/f"{cid}.npz"
        np.savez_compressed(fn,**_case_payload(P,O,bg,dt,core,gamma,src_hash))
        case_records.append({"case_id":cid,"file":str(fn.relative_to(out)),"sha256":_sha_file(fn),"dataset_key":dataset_key})
        secret_map["datasets"].setdefault(dataset_key,{"roles":{}})["roles"][role]=cid
        return cid
    def new_group(dataset_key, role, case_ids, expectation):
        nonlocal group_serial
        group_serial+=1
        gid=f"G{group_serial:06d}"
        group_records.append({"group_id":gid,"case_ids":list(case_ids),"expectation":expectation,"dataset_key":dataset_key})
        secret_map["groups"][gid]="%s:%s"%(dataset_key,role)
        return gid

    accepted=0; skipped=[]
    for fi,p in enumerate(files):
        try:
            comps=load_components(p)
            P,O=resample_components(comps,nres)
            rg=radius_gyration(P)
            if not np.isfinite(rg) or rg<=0: raise ValueError("invalid Rg")
            seg=[]
            for a,b in zip(O[:-1],O[1:]):
                q=P[a:b]; seg.extend(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1).tolist())
            ds=float(np.median(seg)); core=max(core_ds*ds,1e-12*rg)
            u0=_geom_velocity_scale(gamma,rg); dt=dt_frac*rg/max(u0,1e-15)
            c=P.mean(axis=0); n=_unit(rng); bdir=_unit(rng)
            src=c+source_D*rg*n
            amp=eps*u0
            base_bg=zero(P)
            radial_bg=point_source_radial(P,src,amp,rg,float(config.get("source_regularization_rg",0.05)))
            radial_neg_bg=point_source_radial(P,src,-amp,rg,float(config.get("source_regularization_rg",0.05)))
            radial_low_bg=point_source_radial(P,src,low_factor*amp,rg,float(config.get("source_regularization_rg",0.05)))
            director_bg=director_affine(P,n,dir_D*u0,rg)
            boost_bg=uniform_boost(P,bdir,boost_ratio*u0)
            key=f"D{accepted:04d}"
            src_hash=_sha_file(p)
            secret_map["datasets"][key]={"source_path":str(p),"source_sha256":src_hash,"roles":{},"rg_input_units":rg,"u_geom_input_units_per_time":u0,"dt_input_time":dt,"source_direction":n.tolist(),"boost_direction":bdir.tolist()}
            c_base=new_case(key,"base",P,O,base_bg,dt,core,src_hash)
            c_zero=new_case(key,"zero",P,O,base_bg.copy(),dt,core,src_hash)
            c_boost=new_case(key,"boost",P,O,boost_bg,dt,core,src_hash)
            c_rad=new_case(key,"radial_plus",P,O,radial_bg,dt,core,src_hash)
            c_radneg=new_case(key,"radial_minus",P,O,radial_neg_bg,dt,core,src_hash)
            c_radlow=new_case(key,"radial_low",P,O,radial_low_bg,dt,core,src_hash)
            c_dir=new_case(key,"director",P,O,director_bg,dt,core,src_hash)
            # Rigid translation covariance of the same radial source-generated texture.
            t=translate_rg*rg*_unit(rng)
            Pt=P+t; srct=src+t
            bg_t=point_source_radial(Pt,srct,amp,rg,float(config.get("source_regularization_rg",0.05)))
            c_trans=new_case(key,"radial_translated",Pt,O,bg_t,dt,core,src_hash)
            # Rigid rotation covariance around centroid, including source and vector background.
            R=random_rotation(rng)
            Pr=(P-c)@R.T+c
            srcr=(src-c)@R.T+c
            bg_r=point_source_radial(Pr,srcr,amp,rg,float(config.get("source_regularization_rg",0.05)))
            c_rot=new_case(key,"radial_rotated",Pr,O,bg_r,dt,core,src_hash)
            # Generic pair types are intentionally semantically opaque until unblinding.
            new_group(key,"zero_recovery",[c_base,c_zero],"null")
            new_group(key,"uniform_boost_null",[c_base,c_boost],"null")
            new_group(key,"radial_response",[c_base,c_rad],"response")
            new_group(key,"director_response",[c_base,c_dir],"response")
            new_group(key,"translation_covariance",[c_rad,c_trans],"null")
            new_group(key,"rotation_covariance",[c_rad,c_rot],"null")
            new_group(key,"radial_sign_pair",[c_rad,c_radneg],"diagnostic")
            new_group(key,"radial_low_pair",[c_base,c_radlow],"response")
            accepted+=1
        except Exception as e:
            skipped.append({"path":str(p),"reason":repr(e)})
    if accepted==0: raise RuntimeError("all dataset files were rejected; inspect parser/report")
    rng.shuffle(case_records); rng.shuffle(group_records)
    blind_manifest={"cases":case_records,"groups":group_records,"accepted_datasets":accepted,"skipped":skipped}
    _write_json(blind/"manifest.json",blind_manifest)
    salt=secrets.token_hex(32)
    secret_map["salt"]=salt
    commitment=_sha_bytes((salt+_canonical({k:v for k,v in secret_map.items() if k!="salt"})).encode())
    _write_json(secret_dir/"semantic_manifest.json",secret_map)
    _write_json(out/"blind_commitment.json",{"semantic_sha256":commitment,"blind_manifest_sha256":_sha_file(blind/"manifest.json"),"algorithm":"sha256(salt || canonical_semantic_manifest_without_salt)"})
    return blind_manifest


def run_blind(config,out_dir,force_python=False,skip_build=False):
    out=Path(out_dir); manifest_path=out/"blind/manifest.json"
    commitment=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    if _sha_file(manifest_path) != commitment["blind_manifest_sha256"]: raise RuntimeError("blind manifest hash mismatch")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    result_dir=out/"blind/results"; result_dir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for rec in manifest["cases"]:
        case_path=out/rec["file"]
        if _sha_file(case_path) != rec["sha256"]: raise RuntimeError(f"blinded case hash mismatch: {rec['case_id']}")
        z=np.load(case_path,allow_pickle=False)
        P=np.asarray(z["points"],float); O=np.asarray(z["offsets"],np.int64); bg=np.asarray(z["background"],float)
        dt=float(z["dt"]); core=float(z["core_radius"]); gamma=float(z["gamma"])
        v=biot_savart(P,O,gamma,core,force_python=force_python,skip_build=skip_build)
        x1=P+dt*(v+bg)
        m0=metrics(P,O); m1=metrics(x1,O)
        rr={"case_id":rec["case_id"],"dataset_key":rec["dataset_key"],"backend":backend_name() if not force_python else "python",
            "x1_file":f"blind/results/{rec['case_id']}_x1.npy","rg0":m0["rg"],"metrics0":m0,"metrics1":m1,
            "mean_background_speed":float(np.mean(np.linalg.norm(bg,axis=1))),"rms_centered_background_speed":float(np.sqrt(np.mean(np.sum((bg-bg.mean(axis=0))**2,axis=1))))}
        np.save(out/rr["x1_file"],x1)
        _write_json(result_dir/f"{rec['case_id']}.json",rr); rows.append(rr)
    _write_json(out/"blind_results.json",{"backend":backend_name() if not force_python else "python","cases":rows})
    return rows


def score_blind(config,out_dir):
    out=Path(out_dir); manifest=json.loads((out/"blind/manifest.json").read_text(encoding="utf-8"))
    recs={x["case_id"]:x for x in json.loads((out/"blind_results.json").read_text(encoding="utf-8"))["cases"]}
    scores=[]
    for g in manifest["groups"]:
        if len(g["case_ids"])!=2: continue
        a,b=g["case_ids"]; A=np.load(out/recs[a]["x1_file"]); B=np.load(out/recs[b]["x1_file"])
        rg=max(float(recs[a]["rg0"]),1e-15)
        s=kabsch_rms(A,B)/rg
        if g["expectation"]=="null":
            status="PASS" if s <= float(config["null_shape_rms_tol_rg"]) else "FAIL"
        elif g["expectation"]=="response":
            status="PASS" if s >= float(config["min_texture_response_rg"]) else "FAIL"
        else: status="DIAGNOSTIC"
        scores.append({"group_id":g["group_id"],"dataset_key":g["dataset_key"],"expectation":g["expectation"],"shape_rms_over_rg":s,"blinded_status":status})
    _write_json(out/"blind_score.json",{"scores":scores,"thresholds":{"null_shape_rms_tol_rg":config["null_shape_rms_tol_rg"],"min_texture_response_rg":config["min_texture_response_rg"]}})
    return scores


def unblind(config,out_dir):
    out=Path(out_dir)
    secret_map=json.loads((out/"secret/semantic_manifest.json").read_text(encoding="utf-8"))
    commitment_obj=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    commitment=commitment_obj["semantic_sha256"]
    if _sha_file(out/"blind/manifest.json") != commitment_obj["blind_manifest_sha256"]: raise RuntimeError("blind manifest hash mismatch during unblind")
    salt=secret_map["salt"]
    calc=_sha_bytes((salt+_canonical({k:v for k,v in secret_map.items() if k!="salt"})).encode())
    if calc!=commitment: raise RuntimeError("blind semantic commitment mismatch")
    scores={x["group_id"]:x for x in json.loads((out/"blind_score.json").read_text(encoding="utf-8"))["scores"]}
    role_scores={}
    for gid,semantic in secret_map["groups"].items():
        dataset_key,role=semantic.split(":",1)
        role_scores.setdefault(dataset_key,{})[role]=scores[gid]
    dataset_reports=[]
    hard_roles=["zero_recovery","uniform_boost_null","translation_covariance","rotation_covariance"]
    for key,rs in role_scores.items():
        hard_pass=all(rs[r]["blinded_status"]=="PASS" for r in hard_roles)
        rad=rs["radial_response"]["shape_rms_over_rg"]
        radneg_pair=rs["radial_sign_pair"]["shape_rms_over_rg"]
        low=rs["radial_low_pair"]["shape_rms_over_rg"]
        # For +/- radial, distance between + and - should be ~2 times baseline->plus at one-step order.
        sign_ratio=radneg_pair/max(rad,1e-300)
        expected_sign=2.0
        sign_ok=abs(sign_ratio-expected_sign) <= float(config["linearity_ratio_tol"])
        expected_hi_low=1.0/max(float(config.get("linearity_low_factor",0.5)),1e-15)
        hi_low=rad/max(low,1e-300)
        lin_ok=abs(hi_low-expected_hi_low) <= float(config["linearity_ratio_tol"])
        dataset_reports.append({
            "dataset_key":key,
            "source_path":secret_map["datasets"][key]["source_path"],
            "hard_structural_status":"PASS" if hard_pass else "FAIL",
            "gates":{
                "G0_zero_recovery":rs["zero_recovery"],
                "G1_uniform_boost_null":rs["uniform_boost_null"],
                "G2_translation_covariance":rs["translation_covariance"],
                "G3_rotation_covariance":rs["rotation_covariance"],
                "G4_radial_texture_response":{"status":rs["radial_response"]["blinded_status"],"epistemic":"CONDITIONAL_BRIDGE",**rs["radial_response"]},
                "G5_director_texture_response":{"status":rs["director_response"]["blinded_status"],"epistemic":"CONDITIONAL_BRIDGE",**rs["director_response"]},
                "G6_radial_sign_symmetry":{"status":"PASS" if sign_ok else "FAIL","ratio":sign_ratio,"expected":expected_sign,"tolerance":config["linearity_ratio_tol"],"epistemic":"NUMERICAL_BRIDGE_CHECK"},
                "G7_radial_amplitude_linearity":{"status":"PASS" if lin_ok else "FAIL","ratio":hi_low,"expected":expected_hi_low,"tolerance":config["linearity_ratio_tol"],"epistemic":"NUMERICAL_BRIDGE_CHECK"},
            }
        })
    overall="PASS" if all(d["hard_structural_status"]=="PASS" for d in dataset_reports) else "FAIL"
    report={
        "commitment_verified":True,"overall_structural_status":overall,
        "interpretation":"A structural PASS means the numerical implementation respects common-boost nullity and rigid covariance. Texture-response gates test explicit conditional background couplings; they do not establish that SST derives those couplings.",
        "datasets":dataset_reports,
        "provenance":{"python":sys.version,"platform":platform.platform(),"backend":json.loads((out/"blind_results.json").read_text())["backend"]},
        "sst_canonical_constants":SST_CANONICAL,
    }
    _write_json(out/"unblinded_report.json",report)
    with (out/"summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["dataset_key","source_path","structural_status","boost_null_rms_rg","radial_response_rms_rg","director_response_rms_rg","linearity_ratio"])
        for d in dataset_reports:
            g=d["gates"]; w.writerow([d["dataset_key"],d["source_path"],d["hard_structural_status"],g["G1_uniform_boost_null"]["shape_rms_over_rg"],g["G4_radial_texture_response"]["shape_rms_over_rg"],g["G5_director_texture_response"]["shape_rms_over_rg"],g["G7_radial_amplitude_linearity"]["ratio"]])
    return report


def run_full(config_path,dataset,out_dir,force_python=False,skip_build=False):
    config=json.loads(Path(config_path).read_text(encoding="utf-8"))
    prepare_blind(config,dataset,out_dir)
    run_blind(config,out_dir,force_python,skip_build)
    score_blind(config,out_dir)
    return unblind(config,out_dir)
