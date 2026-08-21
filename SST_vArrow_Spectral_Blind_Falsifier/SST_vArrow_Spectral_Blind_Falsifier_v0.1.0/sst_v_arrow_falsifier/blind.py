from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from .io import load_manifest, resolve_input, load_spectrum_csv, load_trajectory_csv, load_trajectory_npz
from .trajectory import trajectory_to_spectrum
from .models import fit_models, slope_for_cutoff
from .bootstrap import bootstrap_linear_speed
from .utils import load_json, save_json, robust_cv


def _sample_analysis(row, campaign_dir, cfg, outdir):
    p=resolve_input(campaign_dir,row.path)
    typ=str(row.input_type).lower()
    meta={}
    if typ in {"spectrum","spectrum_csv"}:
        spec=load_spectrum_csv(p)
    elif typ in {"trajectory_csv","trajectory"}:
        t,xyz=load_trajectory_csv(p)
        spec,meta=trajectory_to_spectrum(t,xyz,
            min_peak_snr=cfg["spectral"]["min_peak_snr"],
            low_k_fraction=cfg["spectral"]["low_k_fraction"],
            exclude_lowest_omega_bins=cfg["spectral"]["exclude_lowest_omega_bins"])
    elif typ in {"trajectory_npz","npz"}:
        t,xyz=load_trajectory_npz(p)
        spec,meta=trajectory_to_spectrum(t,xyz,
            min_peak_snr=cfg["spectral"]["min_peak_snr"],
            low_k_fraction=cfg["spectral"]["low_k_fraction"],
            exclude_lowest_omega_bins=cfg["spectral"]["exclude_lowest_omega_bins"])
    else:
        raise ValueError(f"Unsupported input_type={row.input_type}")
    if len(spec)<cfg["spectral"]["min_modes"]:
        raise ValueError(f"{row.sample_id}: only {len(spec)} modes; need >= {cfg['spectral']['min_modes']}")
    # Re-apply low-k fraction for supplied spectra.
    cut=np.quantile(spec.abs_k_rad_m,cfg["spectral"]["low_k_fraction"])
    low=spec[spec.abs_k_rad_m<=cut].copy()
    if len(low)<cfg["spectral"]["min_modes"]:
        low=spec.nsmallest(cfg["spectral"]["min_modes"],"abs_k_rad_m").copy()
    rc=None if pd.isna(row.core_radius_m) else float(row.core_radius_m)
    models=fit_models(low,rc)
    boot=bootstrap_linear_speed(low,cfg["fit"]["bootstrap_replicates"],cfg["fit"]["bootstrap_seed"]+abs(hash(str(row.sample_id)))%100000)
    slopes=[]
    for f in cfg["fit"]["cutoff_fractions"]:
        s=slope_for_cutoff(spec,f)
        if s is not None: slopes.append(s)
    slope_cv=robust_cv(slopes)
    bics={k:v["bic"] for k,v in models.items()}
    best=min(bics,key=bics.get)
    lin_bic=bics["linear"]
    linear_within=(lin_bic-bics[best])<=cfg["fit"]["bic_linear_within_best"]
    exponent=models["power"]["params"]["exponent"]
    exponent_ok=abs(exponent-1.0)<=cfg["fit"]["power_exponent_tolerance"]
    a=abs(models["linear"]["params"]["intercept_rad_s"])
    intercept_frac=a/max(float(np.median(low.omega_rad_s)),1e-300)
    gates={
      "positive_speed":models["linear"]["params"]["v_m_s"]>0,
      "linear_model_competitive":bool(linear_within),
      "power_exponent_near_one":bool(exponent_ok),
      "low_k_slope_stable":None if slope_cv is None else bool(slope_cv<=cfg["fit"]["slope_cutoff_cv_max"]),
      "small_intercept":bool(intercept_frac<=cfg["fit"]["intercept_fraction_max"])
    }
    spec_out=outdir/f"spectrum_{row.sample_id}.csv"; spec.to_csv(spec_out,index=False)
    return {
      "sample_id":str(row.sample_id),"family_id":str(row.family_id),"topology_blind_label":str(row.topology),
      "resolution_n":None if pd.isna(row.resolution_n) else int(row.resolution_n),
      "input_file":str(p),"n_modes_total":int(len(spec)),"n_modes_low_k":int(len(low)),"trajectory_meta":meta,
      "models":models,"best_bic_model":best,"bootstrap":boot,"cutoff_slopes_m_s":slopes,
      "slope_cutoff_robust_cv":slope_cv,"intercept_fraction":intercept_frac,"gates":gates
    }


def run_blind(campaign_dir, outdir, config_path):
    campaign_dir=Path(campaign_dir); outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    cfg=load_json(config_path); mf=load_manifest(campaign_dir)
    samples=[]; errors=[]
    for row in mf.itertuples(index=False):
        try: samples.append(_sample_analysis(row,campaign_dir,cfg,outdir))
        except Exception as e: errors.append({"sample_id":str(row.sample_id),"error":str(e)})
    valid=[s for s in samples if all(v is not False for v in s["gates"].values())]
    speeds=[s["bootstrap"]["median_m_s"] for s in valid]
    # Resolution gate: compare two highest resolutions within each nonempty family.
    resolution_checks=[]
    for fam in sorted(set(s["family_id"] for s in samples if s["family_id"])):
        ss=[s for s in samples if s["family_id"]==fam and s["resolution_n"] is not None]
        ss=sorted(ss,key=lambda z:z["resolution_n"])
        if len(ss)>=2:
            a,b=ss[-2:]
            va=a["bootstrap"]["median_m_s"]; vb=b["bootstrap"]["median_m_s"]
            rel=abs(vb-va)/max(abs(vb),1e-300)
            resolution_checks.append({"family_id":fam,"n_pair":[a["resolution_n"],b["resolution_n"]],"relative_difference":rel,"pass":rel<=cfg["fit"]["resolution_rel_diff_max"]})
    resolution_gate=None if not resolution_checks else all(x["pass"] for x in resolution_checks)
    family_cv=robust_cv(speeds)
    family_gate=None if family_cv is None else family_cv<=cfg["fit"]["family_speed_cv_max"]
    if not samples:
        verdict="INSUFFICIENT_DATA"
        pooled=None
    else:
        hard_sample_fail=any(any(v is False for v in s["gates"].values()) for s in samples)
        if hard_sample_fail or resolution_gate is False or family_gate is False:
            verdict="BLIND_REJECTS_UNIVERSAL_LINEAR_SPEED"
        elif len(valid)==0:
            verdict="INSUFFICIENT_DATA"
        else:
            verdict="BLIND_CANDIDATE_LOCKED"
        # pooled bootstrap as inverse-variance weighted mean of valid sample estimates
        if valid:
            vals=np.array([s["bootstrap"]["median_m_s"] for s in valid])
            sig=np.array([max(s["bootstrap"]["std_m_s"],1e-30) for s in valid])
            w=1/sig**2; mu=float(np.sum(w*vals)/np.sum(w)); se=float(np.sqrt(1/np.sum(w)))
            pooled={"estimate_m_s":mu,"ci95_m_s":[mu-1.96*se,mu+1.96*se],"n_samples":len(valid),"method":"inverse_variance_weighted_blind_sample_estimates"}
        else: pooled=None
    report={"schema":"sst-universal-speed-blind-v0.1","blind":True,"config":cfg,"samples":samples,"errors":errors,
            "cross_sample":{"family_speed_robust_cv":family_cv,"family_speed_gate":family_gate,"resolution_checks":resolution_checks,"resolution_gate":resolution_gate},
            "pooled_speed":pooled,"blind_verdict":verdict}
    save_json(outdir/"blind_results.json",report)
    return report
