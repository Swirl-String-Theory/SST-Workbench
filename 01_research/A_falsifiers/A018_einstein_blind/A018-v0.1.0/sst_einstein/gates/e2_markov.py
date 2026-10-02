from __future__ import annotations
import numpy as np
from ..geometry import multi_kelvin_ring
from ..simulation import evolve, PhysicalScale
from ..metrics import linear_fit
from ..statistics import acf, decorrelation_lag, msd

GATE="E2"

def run(cfg: dict, scale: PhysicalScale, outdir, rng=None, external_curves=None) -> dict:
    gc=cfg["gates"]["E2"]; n=int(cfg["simulation"]["n_points"]); mode=int(gc.get("mode",2))
    comps=gc.get("components",[[2,0.05,0.1],[3,0.025,0.7],[5,0.015,0.2]])
    p=multi_kelvin_ring(n,1.0,comps)
    sim=evolve(p,cfg,scale,uniform_dimless=(0,0,0),mode=mode,record_points=False)
    e=sim["energy_J"]; drift=float((np.max(e)-np.min(e))/max(abs(e[0]),1e-300))
    q=sim["curvature_mode"]; phase=np.unwrap(np.angle(q)); t=sim["time_s"]
    trend=linear_fit(t,phase); residual=phase-(trend["slope"]*t+trend["intercept"])
    inc=np.diff(residual); th=gc["thresholds"]
    if drift>th["energy_drift_rel_max"]:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Numerical localized-energy drift exceeds the preregistered fidelity ceiling.","energy_drift_rel":drift,"trend":trend,"thresholds":th}
    scale_res=max(float(np.std(phase)),1.0)
    if len(inc)<th["min_increments"] or float(np.std(inc))<th["increment_std_floor"]*scale_res:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Residual phase increments are below the preregistered variability floor.","energy_drift_rel":drift,"trend":trend,"thresholds":th}
    max_lag=min(int(gc.get("max_lag",60)),max(5,len(inc)//4))
    A=acf(inc,max_lag); kc=decorrelation_lag(A,float(th["acf_abs_tol"]),int(th["acf_consecutive"]))
    if kc is None:
        return {"gate":GATE,"verdict":"FAIL","reason":"No persistent decorrelation lag found.","energy_drift_rel":drift,"trend":trend,"acf":A.tolist(),"thresholds":th,
                "falsification_meaning":"The tested Brown/Markov coarse-graining closure is rejected for this deterministic vortex observable."}
    lags,vals=msd(residual,min(max_lag,len(residual)//3)); mask=(lags>=kc)&(vals>0)
    if mask.sum()<5:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Too little post-correlation range for an MSD exponent.","energy_drift_rel":drift,"decorrelation_lag_samples":kc,"acf":A.tolist(),"thresholds":th}
    fit=linear_fit(np.log(lags[mask]),np.log(vals[mask])); alpha=fit["slope"]
    passed=(th["alpha_min"]<=alpha<=th["alpha_max"] and fit["r2"]>=th["msd_loglog_r2_min"])
    return {"gate":GATE,"hypothesis":"After a finite correlation time, residual internal-mode increments admit a Markov/diffusive coarse-graining with MSD proportional to lag.",
            "verdict":"PASS" if passed else "FAIL","energy_drift_rel":drift,"trend":trend,"decorrelation_lag_samples":kc,"decorrelation_time_s":float(kc*np.median(np.diff(t))),
            "acf":A.tolist(),"msd_loglog":{"alpha":float(alpha),"r2":float(fit["r2"])},"thresholds":th,
            "falsification_meaning":"FAIL rejects the Brownian/Markov closure for the selected intrinsic phase observable; it does not reject deterministic vortex dynamics itself."}
