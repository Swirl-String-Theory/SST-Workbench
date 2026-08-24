from __future__ import annotations
import numpy as np

def streamtube_null(rho: float, u0: float, depth: float=0.55, n: int=2048) -> dict:
    """Synthetic incompressible Bernoulli constriction null: A u = const, p+rho u^2/2 = const."""
    x=np.linspace(-4.0,4.0,int(n)); A=1.0-float(depth)*np.exp(-x*x); Q=float(u0)
    u=Q/A; p=0.5*float(rho)*(u0*u0-u*u); head=p+0.5*float(rho)*u*u
    rel=float(np.ptp(head)/max(abs(float(np.mean(head))),1e-300))
    return {"constriction_head_rel_ptp":rel,"u_ratio_max":float(np.max(u)/u0),"area_ratio_min":float(np.min(A)),"ok":bool(rel<1e-12)}
