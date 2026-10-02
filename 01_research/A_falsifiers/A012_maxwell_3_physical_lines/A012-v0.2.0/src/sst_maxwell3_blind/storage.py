from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .numerics import scalar_fit_through_origin, nrmse, r2_score


def run_storage(path: Path,outdir: Path,cfg: dict):
    z=np.load(path,allow_pickle=False)
    D=np.asarray(z["D_struct"],float); Y=np.asarray(z["ampere_minus_J"],float); dt=float(np.asarray(z["dt"]).ravel()[0])
    if D.shape!=Y.shape or D.ndim<2 or D.shape[-1]!=3 or D.shape[0]<5: raise ValueError("storage NPZ shapes must match (nt,...,3), nt>=5")
    d=np.empty_like(D); d[1:-1]=(D[2:]-D[:-2])/(2*dt); d[0]=(D[1]-D[0])/dt; d[-1]=(D[-1]-D[-2])/dt
    nt=D.shape[0]; train=(np.arange(nt)%2)==0; valid=~train
    beta=scalar_fit_through_origin(d[train],Y[train]); pred=beta*d[valid]
    v_nrmse=nrmse(Y[valid].reshape(-1,3),pred.reshape(-1,3)); v_r2=r2_score(Y[valid],pred)
    baseline=float(np.sqrt(np.mean(Y[valid]**2))); residual=float(np.sqrt(np.mean((Y[valid]-pred)**2))); reduction=1.0-residual/baseline if baseline>0 else 0.0
    g=cfg["gates"]; gates=[
      {"name":"storage.validation_nrmse","value":v_nrmse,"criterion":f"<= {g['validation_nrmse_max']}","status":"PASS" if v_nrmse<=g["validation_nrmse_max"] else "FAIL"},
      {"name":"storage.validation_r2","value":v_r2,"criterion":f">= {g['validation_r2_min']}","status":"PASS" if v_r2>=g["validation_r2_min"] else "FAIL"},
      {"name":"storage.residual_reduction","value":reduction,"criterion":f">= {g['residual_reduction_min']}","status":"PASS" if reduction>=g["residual_reduction_min"] else "FAIL"},
    ]
    status="FAIL" if any(x["status"]=="FAIL" for x in gates) else "PASS"
    out={"status":status,"lambda_blind":beta,"validation_nrmse":v_nrmse,"validation_r2":v_r2,"residual_reduction":reduction,"gates":gates}
    outdir.mkdir(parents=True,exist_ok=True); (outdir/"storage_current_verdict.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
