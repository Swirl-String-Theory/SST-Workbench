from __future__ import annotations
import csv,json,math,time
from pathlib import Path
import numpy as np
from .constants import R_C,RHO_F,GAMMA_CANON,TAU_C,V_SWIRL
from .geometry import resample_closed,physicalize_thickness_to_rc,perturb_curve,affine_constriction,impulse
from .dynamics import integrate
from .metrics import signed_projection,dominant_frequency,envelope_gamma,kelvin_window_metrics,energy_metrics
from .constriction import streamtube_null


def _write_csv(path,rows):
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def _trajectory_metrics(base,pert,seed_disp):
    n=min(len(base["frames"]),len(pert["frames"])); a=[];r=[]
    for i in range(n):
        aa,rr=signed_projection(pert["frames"][i],base["frames"][i],seed_disp);a.append(aa);r.append(rr)
    t=base["times"][:n]; a=np.asarray(a); r=np.asarray(r)
    omega,fmethod,fscore=dominant_frequency(t,a); gamma=envelope_gamma(t,a); km=kelvin_window_metrics(t,a)
    out={"omega_ring_s-1":omega,"frequency_method":fmethod,"frequency_peak_fraction":fscore,"omega_tau":omega*TAU_C if np.isfinite(omega) else float("nan"),"gamma_s-1":gamma,"gamma_tau":gamma*TAU_C if np.isfinite(gamma) else float("nan"),"shape_rms_max":float(np.max(r)),**km}
    out["gamma_times_TK"] = gamma*km["T_K_100_s"] if np.isfinite(gamma) and np.isfinite(km["T_K_100_s"]) else float("nan")
    return out


def run_campaign(campaign_dir: str|Path, backend="auto", allow_sycl_cpu=False):
    cdir=Path(campaign_dir).resolve(); frozen=json.loads((cdir/"frozen_protocol.json").read_text()); cfg=frozen["config"]
    from .blind import canonical_hash
    if canonical_hash(cfg)!=frozen.get("config_sha256"):
        raise RuntimeError("G0 protocol hash mismatch: frozen config was modified after blinding")
    public=json.loads((cdir/"blind_manifest.public.json").read_text()); rows=[]; traces={}
    null=streamtube_null(RHO_F,V_SWIRL,cfg.get("constriction_streamtube_depth",0.55))
    for item in public:
        sid=item["sample_id"]; raw=np.load(cdir/"blinded_inputs"/f"{sid}.npy")
        for N in cfg["resolutions"]:
            geom=resample_closed(raw,int(N)); phys,scale_meta=physicalize_thickness_to_rc(geom,R_C,cfg.get("exclude_fraction",0.03))
            dyn_cfg={"rho_kg_m3":RHO_F,"gamma_m2_s":GAMMA_CANON,"core_m":R_C,"cfl":cfg["cfl"],"dt_tau":cfg["dt_tau"],"t_end_tau":cfg["t_end_tau"],"max_steps":cfg["max_steps"],"sample_stride":cfg["sample_stride"]}
            base=integrate(phys,dyn_cfg,backend,allow_sycl_cpu,record_geometry=True)
            bem=energy_metrics(base["H"]); I0=base["I"][0]; I_scale=max(np.linalg.norm(I0), RHO_F*abs(GAMMA_CANON)*scale_meta["physical_length_m"]**2, 1e-300); Id=np.linalg.norm(base["I"]-I0,axis=1)/I_scale
            common={"sample_id":sid,"resolution":int(N),"run_kind":"baseline","G0_blind_protocol":"PASS",**scale_meta,**bem,"impulse_rel_max":float(np.max(Id)),"dt_tau":base["dt_s"]/TAU_C,"steps":base["steps"],"backend":base["backend_info"].get("backend",backend),**null}
            rows.append(common)
            traces[f"{sid}_N{N}_baseline"]={"t_tau":(base["times"]/TAU_C).tolist(),"H_J":base["H"].tolist()}
            for spec in cfg["perturbations"]:
                amp=float(spec["amplitude_rc"])*R_C
                pp=perturb_curve(phys,int(spec["mode"]),amp,str(spec.get("kind","normal")))
                seed=pp-phys
                tr=integrate(pp,dyn_cfg,backend,allow_sycl_cpu,record_geometry=True)
                em=energy_metrics(tr["H"]); tm=_trajectory_metrics(base,tr,seed)
                row={"sample_id":sid,"resolution":int(N),"G0_blind_protocol":"PASS","run_kind":f"perturb_{spec.get('kind','normal')}_m{spec['mode']}_a{spec['amplitude_rc']}rc","perturb_kind":str(spec.get("kind","normal")),"perturb_mode":int(spec["mode"]),"amplitude_rc":float(spec["amplitude_rc"]),**scale_meta,**em,**tm,"dt_tau":tr["dt_s"]/TAU_C,"steps":tr["steps"],"backend":tr["backend_info"].get("backend",backend),**null}
                rows.append(row)
                traces[f"{sid}_N{N}_{row['run_kind']}"]={"t_tau":(base["times"][:len(tr["times"])]/TAU_C).tolist(),"H_J":tr["H"].tolist()}
            if cfg.get("run_constriction_release",True):
                cp=affine_constriction(phys,float(cfg.get("constriction_eta",0.03))); seed=cp-phys
                tr=integrate(cp,dyn_cfg,backend,allow_sycl_cpu,record_geometry=True); em=energy_metrics(tr["H"]); tm=_trajectory_metrics(base,tr,seed)
                rows.append({"sample_id":sid,"resolution":int(N),"G0_blind_protocol":"PASS","run_kind":"constriction_release","perturb_kind":"constriction","perturb_mode":0,"amplitude_rc":float("nan"),**scale_meta,**em,**tm,"dt_tau":tr["dt_s"]/TAU_C,"steps":tr["steps"],"backend":tr["backend_info"].get("backend",backend),**null})
    # Blind gate evaluation, before source names are restored.
    tol=float(cfg["energy_tol_rel"]); impulse_tol=float(cfg["impulse_tol_rel"])
    for r in rows:
        r["G2_energy_no_loss"]="PASS" if r["energy_rel_maxabs"]<=tol and r["energy_rel_min"]>=-tol else "FAIL"
        r["G1_impulse"]=("NA" if "impulse_rel_max" not in r else ("PASS" if r["impulse_rel_max"]<=impulse_tol else "FAIL"))
        r["G5_constriction_null"]="PASS" if r["constriction_head_rel_ptp"]<1e-12 else "FAIL"
        r["G5_constriction_release_no_loss"]=(r["G2_energy_no_loss"] if r.get("run_kind")=="constriction_release" else "NA")
        tk=r.get("T_K_100_s",float("nan")); t75=r.get("T_K_75_s",float("nan"))
        if np.isfinite(tk) and np.isfinite(t75) and tk>0:
            r["G4_kelvin_duration"]="PASS" if abs(tk-t75)/tk <= float(cfg["kelvin_window_tol_rel"]) else "PERSISTENT_OR_UNRESOLVED"
        else:r["G4_kelvin_duration"]="NA"
        r["G3_sign_symmetry"]="NA"
        r["G6_resolution_convergence"]="NA"
        r["blind_pass"] = r["G2_energy_no_loss"]=="PASS" and r["G5_constriction_null"]=="PASS"

    # G3: +epsilon / -epsilon frequency symmetry, evaluated without source labels.
    sign_tol=float(cfg.get("omega_sign_tol_rel",0.15))
    for r in rows:
        if not str(r.get("run_kind","")).startswith("perturb_") or not np.isfinite(r.get("omega_ring_s-1",float("nan"))):
            continue
        mates=[m for m in rows if m.get("sample_id")==r.get("sample_id") and m.get("resolution")==r.get("resolution") and m.get("perturb_kind")==r.get("perturb_kind") and m.get("perturb_mode")==r.get("perturb_mode") and np.isfinite(m.get("amplitude_rc",float("nan"))) and np.isclose(m.get("amplitude_rc"),-r.get("amplitude_rc")) and np.isfinite(m.get("omega_ring_s-1",float("nan")))]
        if mates:
            w1=abs(float(r["omega_ring_s-1"]));w2=abs(float(mates[0]["omega_ring_s-1"]));rel=abs(w1-w2)/max(w1,w2,1e-300);r["omega_sign_rel_diff"]=rel;r["G3_sign_symmetry"]="PASS" if rel<=sign_tol else "FAIL"

    # G6: high-resolution observables should not diverge. We test energy drift and, where resolved, frequency.
    conv_tol=float(cfg.get("resolution_convergence_tol_rel",0.15))
    groups={}
    for r in rows:
        key=(r.get("sample_id"),r.get("run_kind"));groups.setdefault(key,[]).append(r)
    for g in groups.values():
        g.sort(key=lambda x:int(x["resolution"]))
        if len(g)<2: continue
        for idx in range(1,len(g)):
            lo,hi=g[idx-1],g[idx]
            e_lo=float(lo["energy_rel_maxabs"]);e_hi=float(hi["energy_rel_maxabs"]);ok_e=e_hi<=max(e_lo*(1.0+conv_tol),float(cfg["energy_tol_rel"]))
            w_lo=float(lo.get("omega_ring_s-1",float("nan")));w_hi=float(hi.get("omega_ring_s-1",float("nan")))
            if np.isfinite(w_lo) and np.isfinite(w_hi):
                ok_w=abs(w_hi-w_lo)/max(abs(w_hi),abs(w_lo),1e-300)<=conv_tol
            else: ok_w=True
            hi["G6_resolution_convergence"]="PASS" if ok_e and ok_w else "FAIL"
            hi["blind_pass"] = bool(hi["blind_pass"] and hi["G6_resolution_convergence"]!="FAIL" and hi.get("G3_sign_symmetry")!="FAIL")

    # Final blind verdict: unresolved ringdown is reported, not forced to fail; resolved failed symmetries do fail.
    for r in rows:
        if r.get("G1_impulse")=="FAIL" or r.get("G3_sign_symmetry")=="FAIL" or r.get("G6_resolution_convergence")=="FAIL":
            r["blind_pass"]=False

    (cdir/"results_blind.json").write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")
    (cdir/"traces_blind.json").write_text(json.dumps(traces,indent=2),encoding="utf-8")
    _write_csv(cdir/"results_blind.csv",rows)
    return rows


def unblind(campaign_dir: str|Path):
    cdir=Path(campaign_dir).resolve(); rows=json.loads((cdir/"results_blind.json").read_text()); private=json.loads((cdir/"blind_manifest.private.json").read_text()); mapping={x["sample_id"]:x for x in private}
    out=[]
    for r in rows:
        m=mapping[r["sample_id"]]; out.append({**r,"source_rel":m["source_rel"],"source_sha256":m["sha256"]})
    (cdir/"results_unblinded.json").write_text(json.dumps(out,indent=2,default=str),encoding="utf-8"); _write_csv(cdir/"results_unblinded.csv",out)
    summary={"n_rows":len(out),"n_samples":len(set(r["sample_id"] for r in out)),"blind_pass_rows":sum(bool(r.get("blind_pass")) for r in out),"failed_energy_rows":sum(r.get("G2_energy_no_loss")=="FAIL" for r in out)}
    (cdir/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return summary
