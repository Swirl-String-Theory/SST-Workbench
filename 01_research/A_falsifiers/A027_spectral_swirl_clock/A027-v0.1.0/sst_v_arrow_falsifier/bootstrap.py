from __future__ import annotations
import numpy as np
from .models import fit_weighted_linear


def bootstrap_linear_speed(df, reps=2000, seed=0):
    rng=np.random.default_rng(seed)
    x=df.abs_k_rad_m.to_numpy(float); y=df.omega_rad_s.to_numpy(float); p=df.power.to_numpy(float)
    n=len(df); vals=[]
    for _ in range(reps):
        idx=rng.integers(0,n,n)
        xx=x[idx]; yy=y[idx]; pp=p[idx]
        if np.ptp(xx)<=0: continue
        b,_,_=fit_weighted_linear(xx,yy,pp,[np.ones_like(xx),xx])
        if np.isfinite(b[1]) and b[1]>0: vals.append(float(b[1]))
    if len(vals)<max(100,reps//10):
        raise RuntimeError("Bootstrap failed: insufficient non-degenerate resamples")
    a=np.asarray(vals)
    return {"median_m_s":float(np.median(a)),"ci95_m_s":[float(np.quantile(a,.025)),float(np.quantile(a,.975))],"std_m_s":float(np.std(a,ddof=1)),"n":len(a)}
