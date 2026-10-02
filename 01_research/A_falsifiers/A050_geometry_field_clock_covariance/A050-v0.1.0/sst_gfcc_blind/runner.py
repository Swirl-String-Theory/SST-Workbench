from __future__ import annotations
import json, math, shutil, hashlib
from pathlib import Path
import numpy as np
from .geometry import make_curve, curve_metrics
from .filament import evolve_curve
from .field import normalized_velocity_on_grid, pressure_like, divergence_rms, gradient_rms
from .analysis import variance_scaling_scalar, variance_scaling_vector, shuffled_scaling, fit_power, radial_autocorrelation, smooth_periodic, temporal_integrated_variance, fit_temporal
from .io import write_json, write_csv, environment, sha256

def _clean_num(x):
    if isinstance(x, dict): return {k:_clean_num(v) for k,v in x.items()}
    if isinstance(x, list): return [_clean_num(v) for v in x]
    if isinstance(x, (np.floating,float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,int)): return int(x)
    return x

def _sample_indices(total_steps, every):
    a=list(range(0,int(total_steps)+1,int(every)))
    if a[-1]!=int(total_steps): a.append(int(total_steps))
    return a

def run_family(code, cfg, grid_override=None, temporal=True):
    ncurve=int(cfg["curve_points"]); grid=int(grid_override or cfg["grid_n"])
    core=float(cfg["core_ratio"])
    p0=make_curve(code,ncurve,int(cfg["seed"]))
    frames=evolve_curve(p0,core,float(cfg["time_step"]),int(cfg["evolution_steps"]),int(cfg["reparameterize_every"]),int(cfg["field_chunk"]))
    inds=_sample_indices(cfg["evolution_steps"],cfg["sample_every"])
    radii=list(map(int,cfg["window_radii_cells"]))
    # Restrict windows on smaller resolution checks.
    radii=[r for r in radii if r < grid//2]
    rng=np.random.default_rng(int(cfg["seed"])+sum(map(ord,code))+grid)
    rows=[]; vp=[]; vu=[]; vn=[]; divrat=[]; corr=[]; probe_series=[]
    probes=rng.integers(0,grid,size=(int(cfg["probe_count"]),3))
    for s in inds:
        curve=frames[s]
        u,dx=normalized_velocity_on_grid(curve,grid,float(cfg["box_half_extent"]),core,int(cfg["field_chunk"]))
        pr,src=pressure_like(u,dx)
        d=divergence_rms(u,dx); g=gradient_rms(u,dx); ratio=d/max(g,1e-30)
        pscale=variance_scaling_scalar(pr,radii)
        uscale=variance_scaling_vector(u,radii)
        nscale=shuffled_scaling(pr,radii,int(cfg["null_shuffle_repeats"]),rng)
        ac,cl=radial_autocorrelation(pr)
        vp.append(pscale); vu.append(uscale); vn.append(nscale); divrat.append(ratio); corr.append(cl)
        if temporal:
            sm=smooth_periodic(pr,int(cfg["probe_radius_cells"]))
            probe_series.append(np.asarray([sm[tuple(ix)] for ix in probes],float))
        rows.append({"family":code,"grid_n":grid,"step":s,"divergence_ratio":ratio,"pressure_variance":float(np.var(pr)),"source_variance":float(np.var(src)),"corr_length_cells":cl})
    vp=np.mean(np.asarray(vp),axis=0); vu=np.mean(np.asarray(vu),axis=0); vn=np.mean(np.asarray(vn),axis=0)
    fp=fit_power(radii,vp,int(cfg["fit_min_radius_cells"]))
    fu=fit_power(radii,vu,int(cfg["fit_min_radius_cells"]))
    fn=fit_power(radii,vn,int(cfg["fit_min_radius_cells"]))
    tf={"exponent":float('nan'),"r2":float('nan')}
    tv_t=[]; tv_v=[]
    if temporal and len(probe_series)>=4:
        arr=np.asarray(probe_series)
        eff_dt=float(cfg["time_step"])*int(cfg["sample_every"])
        tv_t,tv_v=temporal_integrated_variance(arr,eff_dt)
        tf=fit_temporal(tv_t,tv_v)
    return {
      "family":code,"grid_n":grid,"geometry":curve_metrics(p0),"snapshot_rows":rows,
      "radii":radii,"pressure_scaling":vp.tolist(),"velocity_scaling":vu.tolist(),"null_scaling":vn.tolist(),
      "pressure_fit":fp,"velocity_fit":fu,"null_fit":fn,
      "mean_divergence_ratio":float(np.mean(divrat)),"mean_corr_length_cells":float(np.nanmean(corr)),
      "temporal_fit":tf,"temporal_t":np.asarray(tv_t).tolist(),"temporal_variance":np.asarray(tv_v).tolist()
    }

def run_campaign(config_path, out_dir):
    cfg=json.loads(Path(config_path).read_text(encoding="utf-8"))
    if cfg.get("blind") is not True: raise RuntimeError("blind flag must be true")
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    write_json(out/"config_used.json",cfg); write_json(out/"environment.json",environment())
    fam=[]
    for code in cfg["families"]:
        fam.append(run_family(code,cfg))
    # Resolution check uses the preregistered family only.
    res=[]
    rcfg=cfg.get("resolution_check",{})
    if rcfg.get("enabled"):
        for gn in rcfg["grid_values"]:
            rr=run_family(rcfg["family"],cfg,grid_override=int(gn),temporal=False)
            res.append({"grid_n":int(gn),"pressure_exponent":rr["pressure_fit"]["exponent"],"pressure_r2":rr["pressure_fit"]["r2"]})
    # Blind gates: only generic structure/robustness, no theory-specific target exponent.
    good=[]
    for r in fam:
        fp=r["pressure_fit"]; fn=r["null_fit"]
        ok=(np.isfinite(fp["exponent"]) and np.isfinite(fn["exponent"]) and fp["r2"]>=float(cfg["power_fit_r2_min"]) and (fn["exponent"]-fp["exponent"])>=float(cfg["null_gap_min"]))
        good.append(bool(ok))
    res_ok=True; res_delta=None
    if len(res)>=2:
        vals=[x["pressure_exponent"] for x in res if x["pressure_exponent"] is not None and np.isfinite(x["pressure_exponent"])]
        if len(vals)>=2:
            res_delta=float(max(vals)-min(vals)); res_ok=res_delta<=float(rcfg["max_exponent_delta"])
        else: res_ok=False
    div_ok=all(r["mean_divergence_ratio"]<1e-10 for r in fam)
    family_count=sum(good)
    if not div_ok or not res_ok:
        verdict="NUMERICAL_QUALIFICATION_FAILED"
    elif family_count>=2:
        verdict="CORRELATED_CLOSURE_SCALING_DETECTED"
    else:
        verdict="CORRELATED_CLOSURE_SCALING_NOT_DETECTED"
    summary={
      "stage":"blind_complete","blind":True,"verdict":verdict,
      "qualified_family_count":int(family_count),"family_count":len(fam),
      "divergence_gate":bool(div_ok),"resolution_gate":bool(res_ok),"resolution_exponent_span":res_delta,
      "families":fam,"resolution_check":res,
      "limitations":[
        "Reference campaign uses generated closed curves rather than external production geometry files.",
        "The scalar closure is solved on a periodic finite grid; large-window fits can be box-limited.",
        "Temporal behavior comes from the dimensionless regularized filament evolution used here and is diagnostic, not a calibrated physical clock prediction.",
        "No absolute physical scale or target value is used by the blind verdict."
      ]
    }
    summary=_clean_num(summary)
    write_json(out/"blind_results.json",summary)
    srows=[]; grow=[]; trows=[]
    for r in fam:
        srows.append({"family":r["family"],"grid_n":r["grid_n"],"pressure_exponent":r["pressure_fit"]["exponent"],"pressure_r2":r["pressure_fit"]["r2"],"velocity_exponent":r["velocity_fit"]["exponent"],"velocity_r2":r["velocity_fit"]["r2"],"null_exponent":r["null_fit"]["exponent"],"null_r2":r["null_fit"]["r2"],"temporal_exponent":r["temporal_fit"]["exponent"],"temporal_r2":r["temporal_fit"]["r2"],"mean_divergence_ratio":r["mean_divergence_ratio"],"corr_length_cells":r["mean_corr_length_cells"]})
        grow.append({"family":r["family"],**r["geometry"]})
        trows.extend(r["snapshot_rows"])
    write_csv(out/"scaling_results.csv",srows); write_csv(out/"geometry_metrics.csv",grow); write_csv(out/"snapshot_diagnostics.csv",trows); write_csv(out/"resolution_results.csv",res)
    # Hash the frozen blind result.
    digest=sha256(out/"blind_results.json")
    (out/"blind_results.sha256").write_text(digest+"  blind_results.json\n",encoding="utf-8")
    return summary
