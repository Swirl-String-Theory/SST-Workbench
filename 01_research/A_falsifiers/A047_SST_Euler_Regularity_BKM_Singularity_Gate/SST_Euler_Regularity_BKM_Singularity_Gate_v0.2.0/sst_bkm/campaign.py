from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, secrets, shutil, sys, time, zipfile
from pathlib import Path
import numpy as np
from .seed import base_centerline, localized_packet
from .spectral import wave_numbers,dealias_mask,rk4_step
from .diagnostics import diagnostics,blowup_fit
from .pklsa import (trefoil_candidates,select_variants,load_centerline,canonicalize_centerline,
                    verify_trefoil_bundle,EXPECTED_BUNDLE_SHA256)

NAME="SST_Euler_Regularity_BKM_Singularity_Gate"
VERSION="v0.2.0"

def dump(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")

def blind_token(secret:bytes,text:str,n=16):
    return hashlib.sha256(secret+text.encode("utf-8")).hexdigest()[:n]

def make_packet_basis(principal):
    p=np.asarray(principal,float); p/=np.linalg.norm(p)
    ref=np.array([1.,0.,0.]) if abs(p[0])<0.8 else np.array([0.,1.,0.])
    a=np.cross(p,ref); a/=np.linalg.norm(a); return p,a

def run_one(centerline,spec,case_id,outdir):
    N=spec["N"]; L=spec["L"]; dt=spec["dt"]; T=spec["T"]
    uh=base_centerline(centerline,N,L,spec["core_sigma"])
    d0=diagnostics(uh,L)
    if spec.get("packet_epsilon",0.0)>0:
        p,a=make_packet_basis(d0["principal_strain_vector"]); kv=spec["packet_k"]*p
        idx=d0["hot_index"]; dx=L/N; x0=[-0.5*L+(ii+0.5)*dx for ii in idx]
        uh=localized_packet(uh,L,spec["packet_epsilon"],kv,a,x0,spec["packet_sigma"])
    kx,ky,kz,k2=wave_numbers(N,L); mask=dealias_mask(N,kx,ky,kz); uh*=mask[None,...]
    rows=[]; bkm=0.0; prev=None; t=0.0; steps=int(round(T/dt)); sample_every=max(1,spec["sample_every"]); t0=time.time()
    for step in range(steps+1):
        if step%sample_every==0 or step==steps:
            d=diagnostics(uh,L); d["t"]=float(t)
            if prev is not None: bkm += 0.5*(prev["max_omega"]+d["max_omega"])*(d["t"]-prev["t"])
            d["bkm_integral_sampled"]=float(bkm); rows.append(d); prev=d
        if step<steps: uh=rk4_step(uh,dt,L,mask); t+=dt
    fit=blowup_fit([r["t"] for r in rows],[r["max_omega"] for r in rows])
    e0,e1=rows[0]["energy"],rows[-1]["energy"]
    summary={
        "case_id":case_id,"geometry_id":spec["geometry_id"],"profile_id":spec["profile_id"],"N":N,"dt":dt,"T":T,"runtime_s":time.time()-t0,
        "energy_rel_drift":abs(e1-e0)/max(abs(e0),1e-30),"max_div_rms":max(r["div_rms"] for r in rows),
        "omega_growth":max(r["max_omega"] for r in rows)/rows[0]["max_omega"],"bkm_integral":rows[-1]["bkm_integral_sampled"],
        "blowup_fit":fit,
    }
    summary["numerically_valid"]=bool(summary["energy_rel_drift"]<spec["energy_drift_limit"] and summary["max_div_rms"]<spec["div_rms_limit"])
    dump(Path(outdir)/f"case_{case_id}_timeseries.json",rows); dump(Path(outdir)/f"case_{case_id}_summary.json",summary)
    return summary

def convergence_assessment(summaries):
    # Critical v0.2.0 change: convergence is assessed only within replays of the SAME geometry.
    by_geometry={}
    for s in summaries: by_geometry.setdefault(s["geometry_id"],[]).append(s)
    geometry_results=[]; escalated=[]
    for gid,rows in sorted(by_geometry.items()):
        valid=[x for x in rows if x["numerically_valid"]]
        candidates=[x for x in valid if x["blowup_fit"].get("candidate",False)]
        tstars=[x["blowup_fit"].get("t_star") for x in candidates if x["blowup_fit"].get("t_star")]
        distinct_N=len({x["N"] for x in candidates}); spread=None; conv=False
        if len(tstars)>=3 and distinct_N>=3:
            spread=(max(tstars)-min(tstars))/np.mean(tstars); conv=spread<0.10
        row={"geometry_id":gid,"valid_replays":len(valid),"candidate_replays":len(candidates),"candidate_distinct_N":distinct_N,
             "tstar_relative_spread":None if spread is None else float(spread),"converged_candidate":bool(conv)}
        geometry_results.append(row)
        if conv: escalated.append(gid)
    return {
        "verdict":"ESCALATE_BKM_CANDIDATE" if escalated else "NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW",
        "geometry_count":len(by_geometry),"valid_runs":sum(x["numerically_valid"] for x in summaries),
        "candidate_runs":sum(bool(x["numerically_valid"] and x["blowup_fit"].get("candidate",False)) for x in summaries),
        "escalated_geometry_ids":escalated,"per_geometry":geometry_results,
        "interpretation":"Finite-window numerical gate only. Distinct PKLSA shapes never count as resolution replications of one another. NO_CONVERGED does not prove Euler regularity."
    }

def write_summary_csv(path,summaries):
    fields=["case_id","geometry_id","profile_id","N","dt","T","runtime_s","energy_rel_drift","max_div_rms","omega_growth","bkm_integral","numerically_valid"]
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader();
        for s in summaries: w.writerow({k:s.get(k) for k in fields})

def create_archives(root,outbase,reveal_dir):
    root=Path(root); outbase=Path(outbase)
    blind_zip=root.parent/f"{NAME}_{VERSION}-outputs_BLIND.zip"; revealed_zip=root.parent/f"{NAME}_{VERSION}-outputs_REVEALED.zip"; combined_zip=root.parent/f"{NAME}_{VERSION}-outputs.zip"
    def ztree(zpath,paths):
        with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                p=Path(p)
                if p.is_file(): z.write(p,p.name)
                elif p.exists():
                    for f in p.rglob("*"):
                        if f.is_file(): z.write(f,f.relative_to(root.parent))
    ztree(blind_zip,[outbase/"BLIND"]); ztree(revealed_zip,[outbase/"BLIND",reveal_dir]); ztree(combined_zip,[outbase])
    return [str(blind_zip),str(revealed_zip),str(combined_zip)]

def resolve_pklsa_root(arg):
    value=arg or os.environ.get("SST_PKLSA_ROOT")
    if not value: raise SystemExit("PKLSA root required: pass --pklsa-root PATH or set SST_PKLSA_ROOT")
    return Path(value).expanduser().resolve()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/pklsa_basic.json"); ap.add_argument("--pklsa-root",default=None); ap.add_argument("--out",default=None); ap.add_argument("--no-archives",action="store_true"); args=ap.parse_args()
    root=Path.cwd(); cfg=json.loads(Path(args.config).read_text()); pkroot=resolve_pklsa_root(args.pklsa_root)
    # Fail closed before any PDE work.
    rows=trefoil_candidates(pkroot,require_full_census=True); bundle=verify_trefoil_bundle(pkroot,strict_hash=cfg["dataset"].get("strict_bundle_hash",True))
    rows=select_variants(rows,cfg["dataset"].get("variants","all"))
    outbase=Path(args.out or f"{NAME}_{VERSION}-outputs"); blind=outbase/"BLIND"; reveal=outbase/"REVEALED"
    if outbase.exists(): shutil.rmtree(outbase)
    blind.mkdir(parents=True); reveal.mkdir(parents=True)
    secret=secrets.token_bytes(32); base=cfg["base"]; profiles=cfg["profiles"]
    prepared=[]; reveal_map={}; census=[]
    for row in rows:
        raw=load_centerline(pkroot,row)
        centerline,cmeta=canonicalize_centerline(raw,base["centerline_samples"],base["target_rms_radius"])
        gid="geom_"+blind_token(secret,row.candidate_id,16)
        census.append({"geometry_id":gid,"component_count":row.component_count,"input_points":row.points_per_component,
                       "canonical_coordinate_sha256":cmeta["canonical_coordinate_sha256"]})
        reveal_map[gid]={"candidate_id":row.candidate_id,"family":row.family,"canonical_id":row.canonical_id,"family_index":row.family_index,
                         "variant_index":row.variant_index,"legacy_ptsa_id":row.legacy_ptsa_id,"construction_method":row.construction_method,
                         "source_record":row.source_record,"parameters":row.parameters,"canonicalization":cmeta}
        for profile in profiles:
            spec={**base,**profile,"geometry_id":gid,"profile_id":str(profile["id"])}
            cid="case_"+blind_token(secret,row.candidate_id+"|"+json.dumps(profile,sort_keys=True),16)
            prepared.append((centerline,spec,cid))
            reveal_map.setdefault("cases",{})[cid]={"geometry_id":gid,"candidate_id":row.candidate_id,"profile_id":profile["id"],"N":spec["N"],"dt":spec["dt"],"packet_epsilon":spec.get("packet_epsilon",0.0)}
    manifest={
        "name":NAME,"version":VERSION,"epistemic_status":"PKLSA trefoil population numerical falsification gate; not a proof of regularity or singularity",
        "equation":"3D incompressible unforced Euler, periodic pseudo-spectral rotational form",
        "dataset":{"anonymous_family_count":1,"selected_geometry_count":len(rows),"candidate_dependency_policy":"48 shape cases; one upstream PTSA/PKLSA trefoil population; never 48 independent confirmations",
                   "signed_bundle_sha256":bundle["sha256"],"signed_bundle_contract_sha256_expected":EXPECTED_BUNDLE_SHA256},
        "blind_census":census,
        "blind_cases":[{"case_id":cid,"geometry_id":spec["geometry_id"],"profile_id":spec["profile_id"],"N":spec["N"],"dt":spec["dt"],"T":spec["T"]} for _,spec,cid in prepared],
        "common_numerics":{"L":base["L"],"core_sigma":base["core_sigma"],"target_rms_radius":base["target_rms_radius"],"centerline_samples":base["centerline_samples"],
                           "sample_every":base["sample_every"],"energy_drift_limit":base["energy_drift_limit"],"div_rms_limit":base["div_rms_limit"]},
        "platform":{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__}
    }
    dump(blind/"run_manifest.json",manifest); summaries=[]
    for centerline,spec,cid in prepared: summaries.append(run_one(centerline,spec,cid,blind))
    assessment=convergence_assessment(summaries); dump(blind/"summary.json",{"assessment":assessment,"runs":summaries}); write_summary_csv(blind/"summary.csv",summaries)
    dump(reveal/"case_reveal_map.json",reveal_map)
    dump(reveal/"pklsa_provenance.json",{"pklsa_root":str(pkroot),"bundle":bundle,"selected_variants":[r.variant_index for r in rows],
                                         "dependency_guard":"Trefoil branch is the 48 PTSA v1.0.0 shapes preserved up to similarity; cases are dependent population members, not independent source confirmations."})
    v_swirl=1.09384563e6; r_c=1.40897017e-15; rho_f=7.0e-7; t_c=r_c/v_swirl; omega_c=2*v_swirl/r_c
    dump(reveal/"sst_scale_mapping.json",{"v_swirl_m_s":v_swirl,"r_c_m":r_c,"rho_f_kg_m3":rho_f,"t_c_s":t_c,"omega_c_s_inv":omega_c,
      "mapping_note":"Blind solver used none of these values. Physical mapping remains post-hoc only."})
    archives=[] if args.no_archives else create_archives(root,outbase,reveal)
    print(json.dumps({"assessment":assessment,"archives":archives,"output":str(outbase)},indent=2))
if __name__=="__main__": main()
