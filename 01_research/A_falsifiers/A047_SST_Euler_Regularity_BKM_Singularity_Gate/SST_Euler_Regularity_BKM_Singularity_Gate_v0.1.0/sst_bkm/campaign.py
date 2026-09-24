from __future__ import annotations
import argparse,json,hashlib,os,shutil,sys,time,platform,zipfile
from pathlib import Path
import numpy as np
from .seed import base_trefoil, localized_packet
from .spectral import wave_numbers,dealias_mask,rk4_step
from .diagnostics import diagnostics,blowup_fit

NAME="SST_Euler_Regularity_BKM_Singularity_Gate"
VERSION="v0.1.0"


def dump(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


def case_id(spec):
    return hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:12]


def make_packet_basis(principal):
    p=np.asarray(principal,float); p/=np.linalg.norm(p)
    ref=np.array([1.,0.,0.]) if abs(p[0])<0.8 else np.array([0.,1.,0.])
    a=np.cross(p,ref); a/=np.linalg.norm(a)
    return p,a


def run_one(spec,outdir):
    N=spec["N"]; L=spec["L"]; dt=spec["dt"]; T=spec["T"]
    uh=base_trefoil(N,L,spec["R"],spec["r"],spec["core_sigma"],spec["centerline_samples"])
    d0=diagnostics(uh,L)
    if spec["packet_epsilon"]>0:
        p,a=make_packet_basis(d0["principal_strain_vector"])
        # integer-ish wave number chosen along local principal strain direction
        k0=spec["packet_k"]
        kv=k0*p
        idx=d0["hot_index"]; dx=L/N
        x0=[-0.5*L+(ii+0.5)*dx for ii in idx]
        uh=localized_packet(uh,L,spec["packet_epsilon"],kv,a,x0,spec["packet_sigma"])
    kx,ky,kz,k2=wave_numbers(N,L); mask=dealias_mask(N,kx,ky,kz)
    uh*=mask[None,...]
    rows=[]; bkm=0.0; prev=None; t=0.0; steps=int(round(T/dt))
    sample_every=max(1,spec["sample_every"])
    t0=time.time()
    for step in range(steps+1):
        if step%sample_every==0 or step==steps:
            d=diagnostics(uh,L); d["t"]=float(t)
            if prev is not None:
                bkm += 0.5*(prev["max_omega"]+d["max_omega"])*(d["t"]-prev["t"])
            d["bkm_integral_sampled"]=float(bkm); rows.append(d); prev=d
        if step<steps:
            uh=rk4_step(uh,dt,L,mask); t+=dt
    fit=blowup_fit([r["t"] for r in rows],[r["max_omega"] for r in rows])
    e0=rows[0]["energy"]; e1=rows[-1]["energy"]
    summary={
        "case_id":case_id(spec),"N":N,"dt":dt,"T":T,"runtime_s":time.time()-t0,
        "energy_rel_drift":abs(e1-e0)/max(abs(e0),1e-30),
        "max_div_rms":max(r["div_rms"] for r in rows),
        "omega_growth":max(r["max_omega"] for r in rows)/rows[0]["max_omega"],
        "bkm_integral":rows[-1]["bkm_integral_sampled"],"blowup_fit":fit,
        "numerically_valid":bool(abs(e1-e0)/max(abs(e0),1e-30)<spec["energy_drift_limit"] and max(r["div_rms"] for r in rows)<spec["div_rms_limit"]),
    }
    dump(Path(outdir)/f"case_{summary['case_id']}_timeseries.json",rows)
    dump(Path(outdir)/f"case_{summary['case_id']}_summary.json",summary)
    return summary


def convergence_assessment(summaries,reveal):
    valid=[x for x in summaries if x["numerically_valid"]]
    candidates=[x for x in valid if x["blowup_fit"].get("candidate",False)]
    # Require >=3 candidate runs and cross-resolution T* agreement before escalating.
    tstars=[x["blowup_fit"].get("t_star") for x in candidates if x["blowup_fit"].get("t_star")]
    conv=False; spread=None
    if len(tstars)>=3:
        spread=(max(tstars)-min(tstars))/np.mean(tstars)
        conv=spread<0.10
    verdict="ESCALATE_BKM_CANDIDATE" if conv else "NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW"
    return {"verdict":verdict,"valid_runs":len(valid),"candidate_runs":len(candidates),"tstar_relative_spread":spread,
            "interpretation":"Finite-window numerical gate only; NO_CONVERGED does not prove Euler regularity."}


def create_archives(root,outbase,reveal_dir):
    root=Path(root); outbase=Path(outbase)
    blind_zip=root.parent/f"{NAME}_{VERSION}-outputs_BLIND.zip"
    revealed_zip=root.parent/f"{NAME}_{VERSION}-outputs_REVEALED.zip"
    combined_zip=root.parent/f"{NAME}_{VERSION}-outputs.zip"
    def ztree(zpath,paths):
        with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                p=Path(p)
                if p.is_file(): z.write(p,p.name)
                elif p.exists():
                    for f in p.rglob("*"):
                        if f.is_file(): z.write(f,f.relative_to(root.parent))
    ztree(blind_zip,[outbase/"BLIND"])
    ztree(revealed_zip,[outbase/"BLIND",reveal_dir])
    ztree(combined_zip,[outbase])
    return [str(blind_zip),str(revealed_zip),str(combined_zip)]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/basic.json"); ap.add_argument("--out",default=None); args=ap.parse_args()
    root=Path.cwd(); cfg=json.loads(Path(args.config).read_text())
    outbase=Path(args.out or f"{NAME}_{VERSION}-outputs"); blind=outbase/"BLIND"; reveal=outbase/"REVEALED"
    if outbase.exists(): shutil.rmtree(outbase)
    blind.mkdir(parents=True); reveal.mkdir(parents=True)
    specs=[]; reveal_map={}
    base=cfg["base"]
    for run in cfg["runs"]:
        s={**base,**run}; cid=case_id(s); reveal_map[cid]={"label":run["label"],"packet_epsilon":s["packet_epsilon"],"N":s["N"],"dt":s["dt"]}
        specs.append(s)
    # Strict output blindness: labels, packet amplitudes and SST constants are excluded.
    manifest={"name":NAME,"version":VERSION,"epistemic_status":"prototype numerical falsification gate; not a proof of regularity or singularity",
              "equation":"3D incompressible unforced Euler, periodic pseudo-spectral rotational form",
              "blind_cases":[{"case_id":case_id(s),"N":s["N"],"dt":s["dt"],"T":s["T"]} for s in specs],
              "common_numerics":{"L":base["L"],"R":base["R"],"r":base["r"],"core_sigma":base["core_sigma"],
                                  "centerline_samples":base["centerline_samples"],"sample_every":base["sample_every"],
                                  "energy_drift_limit":base["energy_drift_limit"],"div_rms_limit":base["div_rms_limit"]},
              "platform":{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__}}
    dump(blind/"run_manifest.json",manifest)
    summaries=[]
    for s in specs:
        summaries.append(run_one(s,blind))
    assessment=convergence_assessment(summaries,reveal_map)
    dump(blind/"summary.json",{"assessment":assessment,"runs":summaries})
    dump(reveal/"case_reveal_map.json",reveal_map)
    # SST constants enter only here, after blind verdict.
    v_swirl=1.09384563e6; r_c=1.40897017e-15; rho_f=7.0e-7
    t_c=r_c/v_swirl; omega_c=2*v_swirl/r_c
    dump(reveal/"sst_scale_mapping.json",{
        "v_swirl_m_s":v_swirl,"r_c_m":r_c,"rho_f_kg_m3":rho_f,"t_c_s":t_c,"omega_c_s_inv":omega_c,
        "mapping_note":"Blind solver used none of these values. For optional post-hoc scale interpretation: t = t_tilde*t_c, omega = omega_tilde*omega_c only if the dimensionless normalization is identified with canonical SST scales."
    })
    archives=create_archives(root,outbase,reveal)
    print(json.dumps({"assessment":assessment,"archives":archives,"output":str(outbase)},indent=2))

if __name__=="__main__": main()
