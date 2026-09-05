from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
from .numerics import deterministic_fraction, scalar_fit_through_origin, nrmse, cosine_median, coefficient_of_variation


def _read(path: Path):
    with path.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    req=["case_id","group","u_x","u_y","u_z","p_x","p_y","p_z","A_x","A_y","A_z"]
    if not rows or any(k not in rows[0] for k in req): raise ValueError("reduced_momentum.csv missing required columns")
    ids=[r["case_id"] for r in rows]; groups=[r["group"] for r in rows]
    def vec(prefix): return np.array([[float(r[f"{prefix}_x"]),float(r[f"{prefix}_y"]),float(r[f"{prefix}_z"])] for r in rows],float)
    return ids,groups,vec("u"),vec("p"),vec("A")


def _relation(name,x,y,ids,groups,seed,train_fraction,g):
    train=np.array([deterministic_fraction(i,seed)<train_fraction for i in ids],bool)
    if np.all(train) or not np.any(train): train[np.arange(len(train))%2==0]=True; train[np.arange(len(train))%2==1]=False
    beta=scalar_fit_through_origin(x[train],y[train]); yhat=beta*x[~train]
    val_nrmse=nrmse(y[~train],yhat); val_cos=cosine_median(x[~train],y[~train])
    slopes=[]
    for grp in sorted(set(groups)):
        sel=np.array([q==grp for q in groups]) & train
        if np.sum(sel)>=2: slopes.append(scalar_fit_through_origin(x[sel],y[sel]))
    cv=coefficient_of_variation(slopes)
    gates=[
      {"name":name+".validation_nrmse","value":val_nrmse,"criterion":f"<= {g['validation_nrmse_max']}","status":"PASS" if val_nrmse<=g["validation_nrmse_max"] else "FAIL"},
      {"name":name+".validation_cosine","value":val_cos,"criterion":f">= {g['validation_cosine_median_min']}","status":"PASS" if val_cos>=g["validation_cosine_median_min"] else "FAIL"},
    ]
    if math.isfinite(cv): gates.append({"name":name+".group_slope_cv","value":cv,"criterion":f"<= {g['group_slope_cv_max']}","status":"PASS" if cv<=g["group_slope_cv_max"] else "FAIL"})
    else: gates.append({"name":name+".group_slope_cv","status":"INCONCLUSIVE","criterion":">=2 groups with >=2 training samples"})
    return {"beta_blind":beta,"validation_nrmse":val_nrmse,"validation_cosine_median":val_cos,"group_slope_cv":cv,"gates":gates}


def run_reduced_momentum(path: Path,outdir: Path,cfg: dict,blind_cfg: dict):
    ids,groups,u,p,A=_read(path); seed=blind_cfg["split_seed"]; tf=float(blind_cfg["train_fraction"]); g=cfg["gates"]
    pu=_relation("reduced_momentum.p_over_u",u,p,ids,groups,seed+"|pu",tf,g)
    Ap=_relation("reduced_momentum.A_over_p",p,A,ids,groups,seed+"|Ap",tf,g)
    Au=_relation("reduced_momentum.A_over_u",u,A,ids,groups,seed+"|Au",tf,g)
    fact=abs(Au["beta_blind"]-Ap["beta_blind"]*pu["beta_blind"])/max(abs(Au["beta_blind"]),np.finfo(float).tiny)
    fg={"name":"reduced_momentum.factorization","value":fact,"criterion":f"<= {g['factorization_relative_error_max']}","status":"PASS" if fact<=g["factorization_relative_error_max"] else "FAIL"}
    gates=pu["gates"]+Ap["gates"]+Au["gates"]+[fg]
    status="FAIL" if any(x["status"]=="FAIL" for x in gates) else ("INCONCLUSIVE" if any(x["status"]=="INCONCLUSIVE" for x in gates) else "PASS")
    out={"status":status,"p_over_u":pu,"A_over_p":Ap,"A_over_u":Au,"factorization_relative_error":fact,"gates":gates}
    outdir.mkdir(parents=True,exist_ok=True); (outdir/"reduced_momentum_verdict.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
