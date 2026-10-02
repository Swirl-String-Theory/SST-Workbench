from __future__ import annotations
import csv, hashlib, json, math, platform, secrets, sys, time
from pathlib import Path
import numpy as np

from .io import discover_dataset, load_components
from .geometry import (resample_components, radius_gyration, kabsch_rms, metrics, random_rotation,
                       characteristic_segment_length)
from .threads import (fibonacci_directions, secondary_direction, transverse_basis, make_local_thread_bundle,
                      make_radial_source_thread_bundle, combine_bundles, transform_bundle,
                      closure_diagnostics)
from .diagnostics import (field_solenoidal_diagnostics, background_field_relative_difference,
                          minimum_centerline_clearance, segment_uniformity)
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


def _time_schedule(config,P,O,gamma,rg_ref,u0):
    """Constant-Tfinal schedule with optional ds^2 subcycling.

    The outer-step count sets output/reparameterization cadence.  If the ds^2 bound is
    tighter, each outer step is subdivided without changing T_final.
    """
    legacy_fraction=float(config.get("dt_fraction",0.005))*int(config.get("steps",6))
    tf_frac=float(config.get("t_final_fraction",legacy_fraction))
    outer=max(1,int(config.get("outer_steps",config.get("steps",6))))
    tref=max(1,int(config.get("time_refinement_factor",1)))
    t_final=tf_frac*rg_ref/max(u0,1e-300)
    dt_outer=t_final/outer
    ds=characteristic_segment_length(P,O)
    sub=1
    dt_limit=None
    if bool(config.get("use_ds2_subcycling",True)):
        coeff=float(config.get("dt_ds2_coeff",64.0))
        dt_limit=coeff*ds*ds/max(abs(float(gamma)),1e-300)
        sub=max(1,int(math.ceil(dt_outer/max(dt_limit,1e-300))))
    sub*=tref
    dt=dt_outer/sub; steps=outer*sub
    rep_every=sub if bool(config.get("reparameterize_each_outer_step",True)) else 0
    return {"t_final":float(t_final),"dt":float(dt),"steps":int(steps),"outer_steps":int(outer),
            "subcycles":int(sub),"reparameterize_every":int(rep_every),"ds_characteristic":float(ds),
            "dt_ds2_limit":None if dt_limit is None else float(dt_limit),"time_refinement_factor":int(tref)}


def _case_payload(P,O,bundle,boost,sched,knot_core,thread_core,gamma,rg_ref,source_hash):
    return dict(points=np.asarray(P,np.float64),offsets=np.asarray(O,np.int64),
        thread_points=np.asarray(bundle["points"],np.float64),thread_offsets=np.asarray(bundle["offsets"],np.int64),
        thread_gammas=np.asarray(bundle["gammas"],np.float64),boost=np.asarray(boost,np.float64),
        dt=np.float64(sched["dt"]),steps=np.int64(sched["steps"]),t_final=np.float64(sched["t_final"]),
        outer_steps=np.int64(sched["outer_steps"]),subcycles=np.int64(sched["subcycles"]),
        reparameterize_every=np.int64(sched["reparameterize_every"]),ds_characteristic=np.float64(sched["ds_characteristic"]),
        knot_core_radius=np.float64(knot_core),thread_core_radius=np.float64(thread_core),gamma=np.float64(gamma),
        rg_reference=np.float64(rg_ref),source_file_hash=np.asarray(source_hash))


def _load_case(path):
    z=np.load(path,allow_pickle=False); return {k:np.asarray(z[k]) for k in z.files}


def _bundle_from_case(z): return {"points":z["thread_points"],"offsets":z["thread_offsets"],"gammas":z["thread_gammas"]}


def _local_leg_identity_error_from_cases(a,b,nleg):
    pa=np.asarray(a["thread_points"],float); pb=np.asarray(b["thread_points"],float)
    oa=np.asarray(a["thread_offsets"],np.int64); ob=np.asarray(b["thread_offsets"],np.int64)
    ga=np.asarray(a["thread_gammas"],float); gb=np.asarray(b["thread_gammas"],float)
    if len(oa)!=len(ob) or ga.shape!=gb.shape or nleg<=0: return float("inf")
    err=0.0; scale=1.0
    for alo,ahi,blo,bhi in zip(oa[:-1],oa[1:],ob[:-1],ob[1:]):
        if int(ahi-alo)<nleg or int(bhi-blo)<nleg: return float("inf")
        A=pa[int(alo):int(alo)+nleg]; B=pb[int(blo):int(blo)+nleg]
        err=max(err,float(np.max(np.linalg.norm(A-B,axis=1))))
        scale=max(scale,float(np.max(np.linalg.norm(A-A.mean(0),axis=1))))
    gscale=max(float(np.max(np.abs(ga))) if len(ga) else 1.0,1e-300)
    return max(err/scale,float(np.max(np.abs(ga-gb))/gscale) if len(ga) else 0.0)


def prepare_blind(config,dataset,out_dir):
    out=Path(out_dir); blind=out/"blind"; cases_dir=blind/"cases"; secret_dir=out/"secret"
    cases_dir.mkdir(parents=True,exist_ok=True); secret_dir.mkdir(parents=True,exist_ok=True)
    seed=int(config["blind_seed"]); rng=np.random.default_rng(seed)
    files=discover_dataset(dataset,int(config.get("max_files",0)))
    if not files: raise RuntimeError(f"no supported geometry files under {dataset}")

    M=max(1,int(config.get("orientation_count",3)))
    phase=float(rng.uniform(0,2*np.pi)); dirs=fibonacci_directions(M,phase)
    Rhidden=random_rotation(rng); dirs=dirs@Rhidden.T; dirs=dirs[rng.permutation(M)]
    cov_R=random_rotation(rng); cov_tdir=_unit(rng); boost_dir=_unit(rng)
    secondary_phase=float(rng.uniform(0,2*np.pi)); gradient_phase=float(rng.uniform(0,2*np.pi)); return_phase=float(rng.uniform(0,2*np.pi))
    phase_max_rg=float(config.get("lattice_phase_max_rg",0.50))
    phase_uv=[]
    for _ in range(M):
        rr=phase_max_rg*np.sqrt(float(rng.uniform())); aa=float(rng.uniform(0,2*np.pi)); phase_uv.append([rr*np.cos(aa),rr*np.sin(aa)])
    phase_uv=np.asarray(phase_uv,float)
    rr=phase_max_rg*np.sqrt(float(rng.uniform())); aa=float(rng.uniform(0,2*np.pi)); secondary_uv=np.asarray([rr*np.cos(aa),rr*np.sin(aa)],float)

    precommit={"package_version":"0.3.0","created_unix":time.time(),"config":config,
        "config_sha256":_sha_bytes(_canonical(config).encode()),"dataset_root":str(Path(dataset).resolve()),
        "dataset_files":[{"path":str(p),"sha256":_sha_file(p)} for p in files],
        "model_commitment":{
            "background":"explicit closed vortex filaments; locally parallel source bundle plus finite-source-curvature falsifier",
            "field_kernel":"exact straight-segment integral of the Rosenhead-regularized Biot-Savart line kernel",
            "evolution":"classical RK4; nonlinear knot self-field recomputed at all four stages",
            "time":"constant T_final; ds^2 stability subcycling; independent temporal-refinement factor",
            "reparameterization":"uniform polygonal arclength redistribution only after complete outer RK4 steps",
            "boost":"common boost advects knot and complete thread substrate together",
            "core":"fixed core radii relative to resolution-independent reference Rg",
            "density":"circulation-gradient and position/number-density-gradient controls separated at matched total circulation",
            "return_flux":"remote closed return legs; local outgoing legs invariant across return-distance ladder",
            "orientation_control":"same hidden direction + transverse lattice-phase set for every topology"},
        "epistemic_status":{"G0_G6_G11":"STRUCTURAL / NUMERICAL NECESSITY","G7_G10":"CONDITIONAL DYNAMICAL THREAD BRIDGES",
            "clearance":"core overlap makes bridge interpretation INDETERMINATE rather than a PASS/FAIL on SST",
            "claim":"A bridge PASS is not a derivation of SST gravity or an Earth/Sun SI calibration."},
        "sst_canonical_constants":SST_CANONICAL}
    _write_json(out/"precommit.json",precommit)

    case_records=[]; group_records=[]; secret_map={"datasets":{},"groups":{},"orientation_vectors":dirs.tolist(),"lattice_phase_uv_rg":phase_uv.tolist(),"secondary_lattice_phase_uv_rg":secondary_uv.tolist()}
    case_serial=0; group_serial=0
    nres=int(config["resample_n"]); ref_n=max(int(config.get("reference_rg_n",1024)),nres)
    gamma=float(config.get("gamma",1.0)); knot_core_ratio=float(config.get("knot_core_radius_rg",0.05)); thread_core_ratio=float(config.get("thread_core_radius_rg",0.08))
    rings=int(config.get("thread_rings",1)); bundle_radius=float(config.get("bundle_radius_rg",1.5)); half_length=float(config.get("local_half_length_rg",4.0))
    return_base=float(config.get("return_distance_rg",24.0)); return_mid=return_base*float(config.get("return_mid_factor",2.0)); return_far=return_base*float(config.get("return_far_factor",4.0))
    local_leg_points=int(config.get("thread_local_leg_points",64)); remote_leg_points=int(config.get("thread_remote_leg_points",32)); arc_points=int(config.get("thread_arc_points",32))
    primary_ratio=float(config.get("primary_thread_gamma_ratio",0.01)); secondary_ratio=float(config.get("secondary_thread_gamma_ratio",0.005))
    flux_grad=float(config.get("circulation_gradient_strength",config.get("density_gradient_strength",0.6)))
    pos_grad=float(config.get("position_density_gradient_strength",0.35)); secondary_angle=float(config.get("secondary_angle_deg",60.0))
    boost_ratio=float(config.get("boost_ratio",0.5)); translate_rg=float(config.get("covariance_translation_rg",11.0))
    source_ladder=[float(x) for x in config.get("source_distance_ladder_rg",[16.0,32.0,64.0])]
    if len(source_ladder)<2: raise ValueError("source_distance_ladder_rg requires at least two distances")

    def phase_shift(axis,uv,rg):
        e1,e2=transverse_basis(axis); return float(rg)*(float(uv[0])*e1+float(uv[1])*e2)

    def new_case(dataset_key,role,P,O,bundle,boost,sched,kcore,tcore,rg_ref,src_hash):
        nonlocal case_serial
        case_serial+=1; cid=f"C{case_serial:06d}"; fn=cases_dir/f"{cid}.npz"
        np.savez_compressed(fn,**_case_payload(P,O,bundle,boost,sched,kcore,tcore,gamma,rg_ref,src_hash))
        case_records.append({"case_id":cid,"file":str(fn.relative_to(out)),"sha256":_sha_file(fn),"dataset_key":dataset_key})
        secret_map["datasets"].setdefault(dataset_key,{"roles":{}})["roles"][role]=cid; return cid
    def new_group(dataset_key,role,case_ids,expectation):
        nonlocal group_serial
        group_serial+=1; gid=f"G{group_serial:06d}"; group_records.append({"group_id":gid,"case_ids":list(case_ids),"expectation":expectation,"dataset_key":dataset_key})
        secret_map["groups"][gid]=f"{dataset_key}:{role}"; return gid

    accepted=0; skipped=[]
    for p in files:
        try:
            comps=load_components(p); P,O=resample_components(comps,nres); Pref,_=resample_components(comps,ref_n)
            rg_ref=radius_gyration(Pref)
            if not np.isfinite(rg_ref) or rg_ref<=0: raise ValueError("invalid reference Rg")
            c=np.mean(P,axis=0); u0=_geom_velocity_scale(gamma,rg_ref); sched=_time_schedule(config,P,O,gamma,rg_ref,u0)
            kcore=max(knot_core_ratio*rg_ref,1e-15); tcore=max(thread_core_ratio*rg_ref,1e-15); key=f"D{accepted:04d}"; src_hash=_sha_file(p)
            secret_map["datasets"][key]={"source_path":str(p),"source_sha256":src_hash,"roles":{},"rg_reference_input_units":rg_ref,
                "resample_n":nres,"reference_rg_n":ref_n,"u_geom_input_units_per_time":u0,
                "time_schedule":sched,"knot_core_radius_input_units":kcore,"thread_core_radius_input_units":tcore}
            c_self=new_case(key,"self",P,O,_empty_bundle(),np.zeros(3),sched,kcore,tcore,rg_ref,src_hash)
            primary_cases=[]
            for oi,n in enumerate(dirs):
                lshift=phase_shift(n,phase_uv[oi],rg_ref)
                b=make_local_thread_bundle(c,n,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                    return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                    gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,position_gradient_strength=0.0,gradient_phase=gradient_phase,lattice_shift=lshift,return_phase=return_phase+0.37*oi)
                cid=new_case(key,f"primary_o{oi:02d}",P,O,b,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); primary_cases.append(cid)
                new_group(key,f"primary_response_o{oi:02d}",[c_self,cid],"response")
            n0=dirs[0]; shift0=phase_shift(n0,phase_uv[0],rg_ref)
            b0=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_phase=gradient_phase,lattice_shift=shift0,return_phase=return_phase)
            c_primary=primary_cases[0]
            c_dup=new_case(key,"primary_duplicate",P,O,b0,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"repeatability",[c_primary,c_dup],"null")
            U=boost_ratio*u0*boost_dir; c_boost=new_case(key,"common_boost",P,O,b0,U,sched,kcore,tcore,rg_ref,src_hash); new_group(key,"common_boost_null",[c_primary,c_boost],"null")
            t=translate_rg*rg_ref*cov_tdir; bt=transform_bundle(b0,translation=t); c_trans=new_case(key,"translated_system",P+t,O,bt,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"translation_covariance",[c_primary,c_trans],"null")
            Pr=(P-c)@cov_R.T+c; br=transform_bundle(b0,R=cov_R,center=c); c_rot=new_case(key,"rotated_system",Pr,O,br,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"rotation_covariance",[c_primary,c_rot],"null")

            # Separate density mechanisms at matched total circulation.
            bg_flux=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=flux_grad,position_gradient_strength=0.0,gradient_phase=gradient_phase,lattice_shift=shift0,return_phase=return_phase)
            c_flux=new_case(key,"circulation_gradient",P,O,bg_flux,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"circulation_gradient_response",[c_primary,c_flux],"response")
            bg_pos=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_strength=0.0,position_gradient_strength=pos_grad,gradient_phase=gradient_phase,lattice_shift=shift0,return_phase=return_phase)
            c_pos=new_case(key,"position_density_gradient",P,O,bg_pos,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"position_density_gradient_response",[c_primary,c_pos],"response")
            new_group(key,"density_mechanism_difference",[c_flux,c_pos],"diagnostic")

            n2=secondary_direction(n0,secondary_angle,secondary_phase); shift2=phase_shift(n2,secondary_uv,rg_ref)
            b2=make_local_thread_bundle(c,n2,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=secondary_ratio*gamma,gradient_phase=gradient_phase,lattice_shift=shift2,return_phase=return_phase+1.234)
            bc=combine_bundles(b0,b2); c_comb=new_case(key,"primary_plus_secondary",P,O,bc,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); new_group(key,"secondary_superposition_response",[c_primary,c_comb],"response")

            bm=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_mid,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_phase=gradient_phase,lattice_shift=shift0,return_phase=return_phase)
            bf=make_local_thread_bundle(c,n0,rg_ref,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                return_distance_rg=return_far,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                gamma_per_thread=primary_ratio*gamma,gradient_phase=gradient_phase,lattice_shift=shift0,return_phase=return_phase)
            c_mid=new_case(key,"return_mid",P,O,bm,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); c_far=new_case(key,"return_far",P,O,bf,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash)
            new_group(key,"return_mid_far",[c_mid,c_far],"return"); new_group(key,"return_near_mid",[c_primary,c_mid],"diagnostic")

            radial_roles=[]
            for si,D in enumerate(source_ladder):
                rb=make_radial_source_thread_bundle(c,n0,rg_ref,D,rings=rings,bundle_radius_rg=bundle_radius,local_half_length_rg=half_length,
                    return_distance_rg=return_base,local_leg_points=local_leg_points,remote_leg_points=remote_leg_points,arc_points=arc_points,
                    gamma_per_thread=primary_ratio*gamma,lattice_shift=shift0,return_phase=return_phase)
                cid=new_case(key,f"radial_source_{si:02d}",P,O,rb,np.zeros(3),sched,kcore,tcore,rg_ref,src_hash); radial_roles.append(cid)
                new_group(key,f"source_curvature_{si:02d}",[c_primary,cid],"diagnostic")

            secret_map["datasets"][key].update({"orientation_vectors":dirs.tolist(),"boost_vector":U.tolist(),"translation_vector":t.tolist(),
                "secondary_direction_o00":n2.tolist(),"thread_count_primary":int(len(b0["gammas"])),"return_distances_rg":[return_base,return_mid,return_far],
                "source_distance_ladder_rg":source_ladder,"thread_local_leg_points":local_leg_points,"lattice_phase_uv_rg":phase_uv.tolist(),"secondary_lattice_phase_uv_rg":secondary_uv.tolist()})
            accepted+=1
        except Exception as e: skipped.append({"path":str(p),"reason":repr(e)})
    if accepted==0: raise RuntimeError("all dataset files rejected; inspect parser/report")
    rng.shuffle(case_records); rng.shuffle(group_records)
    blind_manifest={"cases":case_records,"groups":group_records,"accepted_datasets":accepted,"skipped":skipped}; _write_json(blind/"manifest.json",blind_manifest)
    salt=secrets.token_hex(32); secret_map["salt"]=salt
    commitment=_sha_bytes((salt+_canonical({k:v for k,v in secret_map.items() if k!="salt"})).encode()); _write_json(secret_dir/"semantic_manifest.json",secret_map)
    _write_json(out/"blind_commitment.json",{"semantic_sha256":commitment,"blind_manifest_sha256":_sha_file(blind/"manifest.json"),"algorithm":"sha256(salt || canonical_semantic_manifest_without_salt)"})
    return blind_manifest


def run_blind(config,out_dir,force_python=False,skip_build=False):
    out=Path(out_dir); manifest_path=out/"blind/manifest.json"; commitment=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    if _sha_file(manifest_path)!=commitment["blind_manifest_sha256"]: raise RuntimeError("blind manifest hash mismatch")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")); result_dir=out/"blind/results"; result_dir.mkdir(parents=True,exist_ok=True); rows=[]
    for idx,rec in enumerate(manifest["cases"],1):
        case_path=out/rec["file"]
        if _sha_file(case_path)!=rec["sha256"]: raise RuntimeError(f"blinded case hash mismatch: {rec['case_id']}")
        z=np.load(case_path,allow_pickle=False); P=np.asarray(z["points"],float); O=np.asarray(z["offsets"],np.int64)
        TP=np.asarray(z["thread_points"],float); TO=np.asarray(z["thread_offsets"],np.int64); TG=np.asarray(z["thread_gammas"],float)
        boost=np.asarray(z["boost"],float); dt=float(z["dt"]); steps=int(z["steps"]); gamma=float(z["gamma"])
        rep=int(z["reparameterize_every"]); kcore=float(z["knot_core_radius"]); tcore=float(z["thread_core_radius"]); rg_ref=float(z["rg_reference"])
        x1=evolve_frozen_background(P,O,gamma,kcore,TP,TO,TG,tcore,dt,steps,boost,rep,force_python=force_python,skip_build=skip_build)
        rr={"case_id":rec["case_id"],"dataset_key":rec["dataset_key"],"backend":"python" if force_python else backend_name(),
            "final_file":f"blind/results/{rec['case_id']}_final.npy","rg_reference":rg_ref,"steps":steps,"dt":dt,"t_final":float(z["t_final"]),
            "outer_steps":int(z["outer_steps"]),"subcycles":int(z["subcycles"]),"reparameterize_every":rep,"metrics0":metrics(P,O),"metrics_final":metrics(x1,O),
            "segment_uniformity_final":segment_uniformity(x1,O),"thread_components":int(max(0,len(TO)-1)),"thread_abs_gamma_sum":float(np.sum(np.abs(TG))),"boost_norm":float(np.linalg.norm(boost))}
        np.save(out/rr["final_file"],x1); _write_json(result_dir/f"{rec['case_id']}.json",rr); rows.append(rr)
        if idx%50==0: print(f"[SST-THREAD] completed {idx}/{len(manifest['cases'])} blinded cases")
    _write_json(out/"blind_results.json",{"backend":"python" if force_python else backend_name(),"cases":rows}); return rows


def score_blind(config,out_dir):
    out=Path(out_dir); manifest=json.loads((out/"blind/manifest.json").read_text(encoding="utf-8")); recs={x["case_id"]:x for x in json.loads((out/"blind_results.json").read_text(encoding="utf-8"))["cases"]}; scores=[]
    for g in manifest["groups"]:
        if len(g["case_ids"])!=2: continue
        a,b=g["case_ids"]; A=np.load(out/recs[a]["final_file"]); B=np.load(out/recs[b]["final_file"]); rg=max(float(recs[a]["rg_reference"]),1e-15); s=kabsch_rms(A,B)/rg; exp=g["expectation"]
        if exp=="null": status="PASS" if s<=float(config["null_shape_rms_tol_rg"]) else "FAIL"
        elif exp=="response": status="PASS" if s>=float(config["min_thread_response_rg"]) else "FAIL"
        elif exp=="return": status="PASS" if s<=float(config["return_flux_shape_tol_rg"]) else "FAIL"
        else: status="DIAGNOSTIC"
        scores.append({"group_id":g["group_id"],"dataset_key":g["dataset_key"],"expectation":exp,"shape_rms_over_rg":float(s),"blinded_status":status})
    _write_json(out/"blind_score.json",{"scores":scores,"thresholds":{"null_shape_rms_tol_rg":config["null_shape_rms_tol_rg"],"min_thread_response_rg":config["min_thread_response_rg"],"return_flux_shape_tol_rg":config["return_flux_shape_tol_rg"]}}); return scores


def _monotonic_nonincreasing(vals,slack):
    return all(float(vals[i+1])<=float(vals[i])*(1.0+float(slack))+1e-300 for i in range(len(vals)-1))


def unblind(config,out_dir,force_python=False,skip_build=False):
    out=Path(out_dir); secret=json.loads((out/"secret/semantic_manifest.json").read_text(encoding="utf-8")); co=json.loads((out/"blind_commitment.json").read_text(encoding="utf-8"))
    salt=secret["salt"]; semantic={k:v for k,v in secret.items() if k!="salt"}
    if _sha_bytes((salt+_canonical(semantic)).encode())!=co["semantic_sha256"]: raise RuntimeError("semantic commitment mismatch")
    scores_raw=json.loads((out/"blind_score.json").read_text(encoding="utf-8"))["scores"]; scores={x["group_id"]:x for x in scores_raw}; role_scores={}
    for gid,semantic_name in secret["groups"].items():
        key,role=semantic_name.split(":",1); role_scores.setdefault(key,{})[role]=scores[gid]
    manifest=json.loads((out/"blind/manifest.json").read_text(encoding="utf-8")); case_rec={x["case_id"]:x for x in manifest["cases"]}; reports=[]

    for key,rs in role_scores.items():
        meta=secret["datasets"][key]; roles=meta["roles"]; primary=_load_case(out/case_rec[roles["primary_o00"]]["file"])
        TP=np.asarray(primary["thread_points"],float); TO=np.asarray(primary["thread_offsets"],np.int64); TG=np.asarray(primary["thread_gammas"],float); P=np.asarray(primary["points"],float); O=np.asarray(primary["offsets"],np.int64)
        rg=float(primary["rg_reference"]); tcore=float(primary["thread_core_radius"]); kcore=float(primary["knot_core_radius"])
        closure=closure_diagnostics(TP,TO); sol=field_solenoidal_diagnostics(np.mean(P,axis=0),rg,TP,TO,TG,tcore,halfwidth_rg=float(config.get("field_probe_halfwidth_rg",0.75)),grid_n=int(config.get("field_probe_grid_n",7)),force_python=force_python,skip_build=skip_build)
        close_ok=(closure["endpoint_count"]==0 and closure["closing_edge_over_neighbor_max"]<=float(config.get("closure_neighbor_ratio_tol",1.25)))
        sol_ok=(sol["normalized_div_vorticity"]<=float(config.get("normalized_div_vorticity_tol",1e-8)))
        clearance=minimum_centerline_clearance(P,O,TP,TO); clearance_ratio=clearance/max(kcore+tcore,1e-300); clearance_ok=clearance_ratio>=float(config.get("min_clearance_core_sum_factor",1.0))

        mid=_load_case(out/case_rec[roles["return_mid"]]["file"]); far=_load_case(out/case_rec[roles["return_far"]]["file"]); bm=_bundle_from_case(mid); bf=_bundle_from_case(far); bp=_bundle_from_case(primary)
        field_rel=background_field_relative_difference(P,bm,bf,tcore,force_python=force_python,skip_build=skip_build); return_shape=rs["return_mid_far"]["shape_rms_over_rg"]
        nleg=int(meta.get("thread_local_leg_points",config.get("thread_local_leg_points",64))); id_nm=_local_leg_identity_error_from_cases(primary,mid,nleg); id_mf=_local_leg_identity_error_from_cases(mid,far,nleg)
        return_ok=(return_shape<=float(config["return_flux_shape_tol_rg"]) and field_rel<=float(config["return_flux_field_relative_tol"]) and max(id_nm,id_mf)<=float(config.get("local_leg_identity_tol",1e-13)))

        orient=[]; oi=0
        while f"primary_response_o{oi:02d}" in rs: orient.append(rs[f"primary_response_o{oi:02d}"]["shape_rms_over_rg"]); oi+=1
        orient=np.asarray(orient,float); frac=float(np.mean(orient>=float(config["min_thread_response_rg"]))) if len(orient) else 0.0
        g7_ok=bool(len(orient) and np.median(orient)>=float(config["min_thread_response_rg"]))
        gf=rs["circulation_gradient_response"]; gp=rs["position_density_gradient_response"]
        gf_ok=gf["shape_rms_over_rg"]>=float(config.get("min_gradient_response_rg",config["min_thread_response_rg"])); gp_ok=gp["shape_rms_over_rg"]>=float(config.get("min_gradient_response_rg",config["min_thread_response_rg"]))
        g9=rs["secondary_superposition_response"]; g9_ok=g9["shape_rms_over_rg"]>=float(config.get("min_secondary_response_rg",config["min_thread_response_rg"])); g10_ok=frac>=float(config.get("min_orientation_response_fraction",0.5))

        # Finite source curvature -> locally parallel limit.
        field_errors=[]; shape_errors=[]; dists=list(meta.get("source_distance_ladder_rg",[]))
        for si,_D in enumerate(dists):
            rz=_load_case(out/case_rec[roles[f"radial_source_{si:02d}"]]["file"]); rb=_bundle_from_case(rz)
            field_errors.append(background_field_relative_difference(P,bp,rb,tcore,force_python=force_python,skip_build=skip_build)); shape_errors.append(rs[f"source_curvature_{si:02d}"]["shape_rms_over_rg"])
        slack=float(config.get("source_limit_monotonic_slack",0.10)); source_ok=bool(field_errors and shape_errors and _monotonic_nonincreasing(field_errors,slack) and _monotonic_nonincreasing(shape_errors,slack) and field_errors[-1]<=float(config.get("source_parallel_field_relative_tol",0.05)) and shape_errors[-1]<=float(config.get("source_parallel_shape_tol_rg",1e-4)))

        structural_roles=["repeatability","common_boost_null","translation_covariance","rotation_covariance"]
        covariance_ok=all(rs[r]["blinded_status"]=="PASS" for r in structural_roles); hard_ok=bool(covariance_ok and close_ok and sol_ok and return_ok and source_ok)
        structural_status="PASS" if hard_ok else "FAIL"
        bridge_raw=bool(g7_ok and gf_ok and gp_ok and g9_ok and g10_ok); bridge_status=("INDETERMINATE" if not clearance_ok else ("PASS" if bridge_raw else "FAIL"))
        gates={
            "G0_repeatability":{"status":rs["repeatability"]["blinded_status"],**rs["repeatability"]},
            "G1_common_boost_null":{"status":rs["common_boost_null"]["blinded_status"],**rs["common_boost_null"]},
            "G2_translation_covariance":{"status":rs["translation_covariance"]["blinded_status"],**rs["translation_covariance"]},
            "G3_rotation_covariance":{"status":rs["rotation_covariance"]["blinded_status"],**rs["rotation_covariance"]},
            "G4_closed_solenoidal_threads":{"status":"PASS" if close_ok and sol_ok else "FAIL","epistemic":"STRUCTURAL_NECESSITY","closure":closure,"field_solenoidal":sol},
            "G5_core_clearance":{"status":"PASS" if clearance_ok else "INDETERMINATE_CORE_OVERLAP","epistemic":"ADMISSIBILITY","minimum_centerline_clearance":clearance,"clearance_over_core_sum":clearance_ratio,"required_factor":config.get("min_clearance_core_sum_factor",1.0)},
            "G6_return_flux_locality":{"status":"PASS" if return_ok else "FAIL","epistemic":"STRUCTURAL_LOCALITY","mid_far_final_shape_rms_over_rg":return_shape,"mid_far_initial_field_relative_l2":field_rel,"near_mid_local_leg_identity_error":id_nm,"mid_far_local_leg_identity_error":id_mf,"shape_tol_rg":config["return_flux_shape_tol_rg"],"field_relative_tol":config["return_flux_field_relative_tol"]},
            "G7_primary_bundle_dynamical_response":{"status":"PASS" if g7_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE","orientation_responses_rms_over_rg":orient.tolist(),"median":float(np.median(orient)) if len(orient) else None,"min":float(np.min(orient)) if len(orient) else None,"max":float(np.max(orient)) if len(orient) else None,"threshold":config["min_thread_response_rg"]},
            "G8_density_mechanism_decomposition":{"status":"PASS" if gf_ok and gp_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE","circulation_gradient":gf,"position_density_gradient":gp,"mechanism_difference":rs["density_mechanism_difference"],"matched_total_circulation":True},
            "G9_primary_secondary_superposition_response":{"status":"PASS" if g9_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE",**g9},
            "G10_orientation_phase_robustness":{"status":"PASS" if g10_ok else "FAIL","epistemic":"CONDITIONAL_DYNAMICAL_THREAD_BRIDGE","passing_fraction":frac,"required_fraction":config.get("min_orientation_response_fraction",0.5),"count":int(len(orient))},
            "G11_finite_source_to_parallel_limit":{"status":"PASS" if source_ok else "FAIL","epistemic":"STRUCTURAL_LOCAL_GEOMETRY","source_distances_rg":dists,"field_relative_errors":field_errors,"final_shape_rms_over_rg":shape_errors,"monotonic_slack":slack,"far_field_tol":config.get("source_parallel_field_relative_tol",0.05),"far_shape_tol_rg":config.get("source_parallel_shape_tol_rg",1e-4)} }
        reports.append({"dataset_key":key,"source_path":meta["source_path"],"structural_status":structural_status,"conditional_bridge_status":bridge_status,"gates":gates,
            "fixed_core":{"rg_reference":meta["rg_reference_input_units"],"knot_core_radius":meta["knot_core_radius_input_units"],"thread_core_radius":meta["thread_core_radius_input_units"],"reference_rg_n":meta["reference_rg_n"]},"time_schedule":meta["time_schedule"]})

    def aggregate(field):
        vals=[r[field] for r in reports]
        if any(v=="FAIL" for v in vals): return "FAIL"
        if any(v.startswith("INDETERMINATE") or v=="INDETERMINATE" for v in vals): return "INDETERMINATE"
        return "PASS"
    overall_struct=aggregate("structural_status"); overall_bridge=aggregate("conditional_bridge_status")
    scientific=(f"STRUCTURAL_{overall_struct}__BRIDGE_{overall_bridge}")
    report={"commitment_verified":True,"overall_structural_status":overall_struct,"overall_conditional_bridge_status":overall_bridge,"scientific_classification":scientific,
        "interpretation":"G0-G6 and G11 test covariance, closed/solenoidal explicit threads, core-clearance admissibility, remote-return locality and the finite-source-to-parallel limit. G7-G10 are conditional dynamical responses. Core overlap makes those responses indeterminate, not supporting evidence.",
        "datasets":reports,"orientation_vectors_hidden_until_unblind":secret.get("orientation_vectors",[]),"provenance":{"python":sys.version,"platform":platform.platform(),"backend":json.loads((out/"blind_results.json").read_text())["backend"]},"sst_canonical_constants":SST_CANONICAL}
    _write_json(out/"unblinded_report.json",report)
    with (out/"summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["dataset_key","source_path","structural_status","bridge_status","boost_null_rms_rg","clearance_over_core_sum","return_shape_rms_rg","return_field_rel","primary_median_response_rg","circulation_gradient_response_rg","position_density_gradient_response_rg","secondary_response_rg","orientation_pass_fraction","source_far_field_rel","source_far_shape_rms_rg"])
        for d in reports:
            g=d["gates"]; w.writerow([d["dataset_key"],d["source_path"],d["structural_status"],d["conditional_bridge_status"],g["G1_common_boost_null"]["shape_rms_over_rg"],g["G5_core_clearance"]["clearance_over_core_sum"],g["G6_return_flux_locality"]["mid_far_final_shape_rms_over_rg"],g["G6_return_flux_locality"]["mid_far_initial_field_relative_l2"],g["G7_primary_bundle_dynamical_response"]["median"],g["G8_density_mechanism_decomposition"]["circulation_gradient"]["shape_rms_over_rg"],g["G8_density_mechanism_decomposition"]["position_density_gradient"]["shape_rms_over_rg"],g["G9_primary_secondary_superposition_response"]["shape_rms_over_rg"],g["G10_orientation_phase_robustness"]["passing_fraction"],g["G11_finite_source_to_parallel_limit"]["field_relative_errors"][-1],g["G11_finite_source_to_parallel_limit"]["final_shape_rms_over_rg"][-1]])
    return report


def run_full(config_path,dataset,out_dir,force_python=False,skip_build=False):
    config=json.loads(Path(config_path).read_text(encoding="utf-8")); prepare_blind(config,dataset,out_dir); run_blind(config,out_dir,force_python,skip_build); score_blind(config,out_dir); return unblind(config,out_dir,force_python,skip_build)
