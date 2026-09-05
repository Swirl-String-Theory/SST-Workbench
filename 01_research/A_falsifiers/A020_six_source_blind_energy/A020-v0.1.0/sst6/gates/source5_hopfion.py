from __future__ import annotations
import math
import numpy as np
from sst6.constants import R_C,RHO_F,GAMMA_0
from sst6.geometry import pack_components, rotation_minimizing_frame, ribbon_twist
from .common import result, prepared, native


def scale_energy(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"])); backend,bname=native(cfg)
    lambdas=np.asarray(cfg.get("lambdas",[1.0,1.05,1.1,1.2,1.35,1.5,1.75,2.0]),float); E=[]
    for lam in lambdas:
        v,o=pack_components([lam*p for p in comps]); E.append(float(backend.regularized_energy(v,o,1.0,2*math.pi,1.0)))
    E=np.asarray(E); j=int(np.argmin(E)); interior=0<j<len(E)-1
    positive_curv=False; second=None
    if interior:
        x=lambdas[j-1:j+2]; y=E[j-1:j+2]; coef=np.polyfit(x,y,2); second=2*float(coef[0]); positive_curv=second>0
    # SI baseline under baseline identification reach=r_c; diagnostic only.
    v0,o0=pack_components([R_C*p for p in comps]); E_si=float(backend.regularized_energy(v0,o0,RHO_F,GAMMA_0,R_C))
    ok=interior and positive_curv
    return result(5,"H5_INTRINSIC_SCALE","Finite-core self-induction alone selects an interior homothetic size minimum with the core radius held fixed.","PRIMARY_RESEARCH_HYPOTHESIS","PASS" if ok else "FAIL",{"backend":bname,"lambda":lambdas.tolist(),"energy_dimensionless":E.tolist(),"argmin_lambda":float(lambdas[j]),"interior_minimum":interior,"second_derivative_proxy":second,"baseline_self_induction_energy_SI_J":E_si},{"interior_minimum_required":True,"positive_second_derivative_required":True},[
        "FAIL falsifies only the stripped self-induction-only self-binding closure; it does not falsify a larger SST functional with independently derived competing terms."
    ])


def calugareanu_ribbon(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"])); backend,bname=native(cfg); eps=float(cfg.get("offset_core",0.12)); rows=[]
    for ci,p in enumerate(comps):
        _,n,_,closure=rotation_minimizing_frame(p); off=p+eps*n
        vv,oo=pack_components([p,off]); lk=float(backend.gauss_linking_components(vv,oo,0,1)); wr=float(backend.gauss_writhe_component(vv,[0,len(p),len(p)+len(off)],0)); tw=float(ribbon_twist(p,n)); resid=abs(lk-(wr+tw))
        rows.append({"component":ci,"Lk_ribbon":lk,"Wr":wr,"Tw":tw,"Wr_plus_Tw":wr+tw,"closure_angle_rad":closure,"residual":resid})
    maxr=max([r["residual"] for r in rows],default=float("inf")); lim=float(cfg.get("residual_max",0.20)); ok=maxr<=lim
    return result(5,"H5_CALUGAREANU_RIBBON","Independent ribbon linking is numerically consistent with Wr+Tw for the closed finite-core framing.","PRIMARY_GEOMETRIC_IDENTITY","PASS" if ok else "FAIL",{"backend":bname,"offset_core":eps,"components":rows,"max_residual":maxr},{"residual_max":lim},[
        "This validates the framed-curve geometry only; it does not by itself identify a field-space Hopf invariant with material self-linking."
    ])
