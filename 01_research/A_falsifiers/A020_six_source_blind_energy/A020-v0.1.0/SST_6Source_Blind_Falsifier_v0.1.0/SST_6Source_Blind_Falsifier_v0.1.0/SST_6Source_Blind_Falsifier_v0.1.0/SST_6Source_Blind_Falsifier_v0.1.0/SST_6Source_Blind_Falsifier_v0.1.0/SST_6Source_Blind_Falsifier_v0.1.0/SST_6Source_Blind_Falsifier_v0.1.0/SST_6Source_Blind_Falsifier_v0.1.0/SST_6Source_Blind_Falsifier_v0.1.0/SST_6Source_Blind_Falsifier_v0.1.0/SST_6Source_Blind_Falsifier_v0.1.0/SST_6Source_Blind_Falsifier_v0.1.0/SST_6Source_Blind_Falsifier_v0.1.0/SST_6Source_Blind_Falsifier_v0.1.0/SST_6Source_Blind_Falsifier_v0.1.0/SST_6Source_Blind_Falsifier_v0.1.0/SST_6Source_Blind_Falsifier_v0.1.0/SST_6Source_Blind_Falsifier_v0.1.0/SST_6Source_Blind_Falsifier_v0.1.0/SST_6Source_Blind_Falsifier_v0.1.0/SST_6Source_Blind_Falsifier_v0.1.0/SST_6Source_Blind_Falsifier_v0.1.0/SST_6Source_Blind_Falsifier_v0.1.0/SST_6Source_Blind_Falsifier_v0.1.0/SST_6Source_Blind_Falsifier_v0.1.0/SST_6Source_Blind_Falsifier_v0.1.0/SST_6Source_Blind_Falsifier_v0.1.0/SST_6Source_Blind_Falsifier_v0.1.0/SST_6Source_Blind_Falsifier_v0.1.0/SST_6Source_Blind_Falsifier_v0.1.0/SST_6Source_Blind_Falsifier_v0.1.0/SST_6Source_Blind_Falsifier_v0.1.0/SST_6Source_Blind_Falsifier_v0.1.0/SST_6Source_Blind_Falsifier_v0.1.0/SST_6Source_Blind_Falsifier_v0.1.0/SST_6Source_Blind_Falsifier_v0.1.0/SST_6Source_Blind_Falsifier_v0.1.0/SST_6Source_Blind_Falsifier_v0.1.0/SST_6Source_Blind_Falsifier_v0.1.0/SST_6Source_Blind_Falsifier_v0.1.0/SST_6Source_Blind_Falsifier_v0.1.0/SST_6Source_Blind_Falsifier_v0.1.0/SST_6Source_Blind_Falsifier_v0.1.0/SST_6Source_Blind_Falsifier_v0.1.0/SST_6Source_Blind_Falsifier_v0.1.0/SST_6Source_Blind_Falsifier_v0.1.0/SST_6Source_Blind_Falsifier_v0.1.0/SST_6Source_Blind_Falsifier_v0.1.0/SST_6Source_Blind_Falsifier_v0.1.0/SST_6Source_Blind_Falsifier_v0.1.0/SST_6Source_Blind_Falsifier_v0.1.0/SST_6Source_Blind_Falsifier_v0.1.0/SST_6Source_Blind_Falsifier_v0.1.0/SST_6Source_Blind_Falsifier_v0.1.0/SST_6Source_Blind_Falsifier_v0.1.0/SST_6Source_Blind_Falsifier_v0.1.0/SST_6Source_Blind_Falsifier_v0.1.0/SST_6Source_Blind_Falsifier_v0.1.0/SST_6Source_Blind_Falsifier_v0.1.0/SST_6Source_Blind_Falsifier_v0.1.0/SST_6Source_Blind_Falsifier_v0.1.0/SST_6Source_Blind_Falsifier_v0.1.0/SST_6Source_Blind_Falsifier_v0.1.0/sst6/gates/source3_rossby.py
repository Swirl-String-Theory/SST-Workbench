from __future__ import annotations
import math
import numpy as np
from sst6.geometry import pack_components, dominant_curvature_mode, component_length
from .common import result, prepared, native


def gradient_lock_proxy(dataset,cfg):
    comps,v,offs,_=prepared(dataset,int(cfg["n_per_component"]))
    backend,bname=native(cfg)
    # Conditional analogue only: self-induced advection magnitude + Gaussian-core transverse vorticity gradient.
    u=np.asarray(backend.biot_savart_velocity(v,v,offs,2*math.pi,1.0),float)
    beta_core=4.0/math.e  # |d omega/dr| at r=a for omega=Gamma/(pi a^2) exp(-r^2/a^2), Gamma=2pi,a=1
    rows=[]; k0=0
    for ci,p in enumerate(comps):
        ui=u[k0:k0+len(p)]; k0+=len(p)
        U=float(np.median(np.linalg.norm(ui,axis=1))); dom=dominant_curvature_mode(p,int(cfg.get("max_mode",32))); m=int(dom["mode"]); L=component_length(p)
        if U<=1e-12 or m<=0: continue
        lam_obs=L/m; lam_pred=2*math.pi*math.sqrt(U/beta_core); chi=beta_core*lam_obs*lam_obs/(4*math.pi*math.pi*U)
        rows.append({"component":ci,"U_proxy":U,"beta_eff_proxy":beta_core,"dominant_mode":m,"dominant_power_fraction":dom["power_fraction"],"lambda_observed_core":lam_obs,"lambda_pred_core":lam_pred,"chi_R":chi})
    tol=float(cfg.get("chi_log_tolerance",0.7)); ok=bool(rows) and all(abs(math.log(max(r["chi_R"],1e-300)))<=tol for r in rows)
    return result(3,"R3_GRADIENT_LOCK_PROXY","A Rossby-like selected wavelength k^2=beta_eff/U is compatible with the dominant curvature mode under the declared finite-core proxy.","PROXY_DIAGNOSTIC","PASS" if ok else "FAIL",{"backend":bname,"components":rows},{"abs_log_chi_max":tol},[
        "Excluded from the primary verdict. Rossby potential vorticity is quasi-2D; this uses a declared Gaussian-core proxy and is not a 3D Euler invariant."
    ])
