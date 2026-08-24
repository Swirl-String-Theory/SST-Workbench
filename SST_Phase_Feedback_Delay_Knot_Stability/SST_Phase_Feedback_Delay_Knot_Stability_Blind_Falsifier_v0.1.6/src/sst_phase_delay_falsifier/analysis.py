from __future__ import annotations
from pathlib import Path
import json,math,csv
import numpy as np
from scipy.stats import spearmanr
from .geometry import length,kabsch_rms,modal_basis
from .backend import min_gap,evolve_pair,biot_savart_velocity,BACKEND
from .modal import spectrum,physical_eigen_perturbation

def load_cfg(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def _json_safe(obj):
    """Convert NumPy scalars and non-finite floats to strict-JSON values."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k,v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj

def dump(path,obj):
    safe=_json_safe(obj)
    Path(path).write_text(json.dumps(safe,indent=2,allow_nan=False),encoding='utf-8')

def candidate_scale(x,cfg):
    d=min_gap(x,cfg['geometry']['gap_exclusion'])
    if not np.isfinite(d) or d<=0: raise ValueError('invalid nonadjacent gap')
    return d

def predict_one(x,cfg):
    g=cfg['physics']['gamma_dimensionless']; d=candidate_scale(x,cfg); core=cfg['physics']['core_to_gap']*d
    eps=cfg['modal']['fd_eps_to_gap']*d; modes=list(range(cfg['modal']['m_min'],cfg['modal']['m_max']+1))
    rows,cache=spectrum(x,modes,g,core,eps)
    valid=[r for r in rows if np.isfinite(r['delay_score']) and r['omega']>cfg['modal']['omega_floor']]
    delay=float(np.median([r['delay_score'] for r in valid])) if valid else np.nan
    sigma0=float(np.median([r['sigma'] for r in valid])) if valid else np.nan
    omega=float(np.median([r['omega'] for r in valid])) if valid else np.nan
    z=float(np.median([r['omega']*(np.cos(r['theta'])-1.0) for r in valid])) if valid else np.nan
    return {"backend":BACKEND,"length":length(x),"gap":d,"core":core,"delay_score":delay,"linear_sigma0":sigma0,"median_omega":omega,"delay_feature_z":z,"modes":rows},cache

def predict_all(blind_dir,cfg,out_path):
    out={"config":cfg,"backend":BACKEND,"candidates":[]}
    for p in sorted(Path(blind_dir).glob('B*.npy')):
        x=np.load(p); pred,_=predict_one(x,cfg); pred['blind_id']=p.stem; out['candidates'].append(pred)
    dump(out_path,out); return out

def _growth(times,deps):
    t=np.asarray(times); y=np.asarray(deps); floor=max(y[0]*1e-4,1e-16); ly=np.log(np.maximum(y,floor))
    i0=max(1,int(0.2*len(t))); A=np.vstack([t[i0:],np.ones(len(t)-i0)]).T
    slope,inter=np.linalg.lstsq(A,ly[i0:],rcond=None)[0]
    return float(slope)

def measure_one(x,cfg):
    pred,cache=predict_one(x,cfg); d=pred['gap']; core=pred['core']; g=cfg['physics']['gamma_dimensionless']; L=pred['length']
    tchar=L*L/max(abs(g),1e-300); steps=cfg['nonlinear']['steps']; dt=cfg['nonlinear']['total_time_to_tchar']*tchar/steps
    amp=cfg['nonlinear']['perturb_to_gap']*d; sample_every=max(1,steps//cfg['nonlinear']['samples'])
    mode_rows=[]
    chosen=[r for r in pred['modes'] if np.isfinite(r['delay_score']) and r['omega']>cfg['modal']['omega_floor']]
    chosen=chosen[:cfg['nonlinear']['max_modes']]
    for r in chosen:
        eig,basis=cache[r['m']]; p=physical_eigen_perturbation(eig,basis); xp=x+amp*p
        evo=evolve_pair(x,xp,steps,dt,g,core,sample_every)
        deps=np.array([kabsch_rms(a,b)/d for a,b in zip(evo['a'],evo['b'])])
        slope=_growth(np.asarray(evo['times']),deps)
        mode_rows.append({"m":r['m'],"growth":slope,"theta":r['theta'],"delay_score":r['delay_score'],"final_departure":float(deps[-1]),"final_gap_base":float(evo['final_gap_a']),"final_gap_pert":float(evo['final_gap_b'])})
    growth=float(np.median([q['growth'] for q in mode_rows])) if mode_rows else np.nan
    return {"backend":BACKEND,"observed_growth":growth,"mode_runs":mode_rows,"tchar":tchar,"dt":dt,"steps":steps}

def measure_all(blind_dir,cfg,out_path):
    out={"config":cfg,"backend":BACKEND,"candidates":[]}
    for p in sorted(Path(blind_dir).glob('B*.npy')):
        x=np.load(p); q=measure_one(x,cfg); q['blind_id']=p.stem; out['candidates'].append(q)
    dump(out_path,out); return out

def _fit_global_kappa(x0,z,y):
    den=float(np.dot(z,z)); return max(0.0,float(np.dot(z,y-x0)/den)) if den>0 else 0.0

def evaluate(pred_path,measure_path,out_path):
    pred=json.loads(Path(pred_path).read_text()); meas=json.loads(Path(measure_path).read_text())
    P={q['blind_id']:q for q in pred['candidates']}; M={q['blind_id']:q for q in meas['candidates']}
    ids=[i for i in sorted(set(P)&set(M)) if all(np.isfinite(v) for v in [P[i]['delay_score'],P[i]['linear_sigma0'],P[i]['delay_feature_z'],M[i]['observed_growth']])]
    D=np.array([P[i]['delay_score'] for i in ids]); Y=np.array([M[i]['observed_growth'] for i in ids]); X0=np.array([P[i]['linear_sigma0'] for i in ids]); Z=np.array([P[i]['delay_feature_z'] for i in ids])

    # Confirmatory rank gate is undefined for too-small samples. Keep it explicitly
    # absent (JSON null) rather than generating NaN, which strict JSON must reject.
    if len(ids)>=3:
        rho,pv=spearmanr(D,Y)
        rho=float(rho) if np.isfinite(rho) else None
        pv=float(pv) if np.isfinite(pv) else None
    else:
        rho=pv=None

    # Hash-defined 50/50 split, frozen before labels/reveal. For small n this split
    # is retained only for row diagnostics; the holdout gate itself is not evaluated.
    train=np.array([int(__import__('hashlib').sha256(i.encode()).hexdigest(),16)%2==0 for i in ids],bool)
    if train.sum()<2 or (~train).sum()<2:
        train=np.arange(len(ids))%2==0

    if len(ids)>=4:
        kappa=_fit_global_kappa(X0[train],Z[train],Y[train])
        yhat0=X0[~train]; yhat1=X0[~train]+kappa*Z[~train]
        rmse0=float(np.sqrt(np.mean((Y[~train]-yhat0)**2)))
        rmse1=float(np.sqrt(np.mean((Y[~train]-yhat1)**2)))
        improve=(rmse0-rmse1)/rmse0 if rmse0>0 else 0.0
        kappa=float(kappa) if np.isfinite(kappa) else None
        rmse0=rmse0 if np.isfinite(rmse0) else None
        rmse1=rmse1 if np.isfinite(rmse1) else None
        improve=float(improve) if np.isfinite(improve) else None
    else:
        kappa=rmse0=rmse1=improve=None

    cfg=pred['config']['gates']; min_n=cfg['min_candidates']
    primary=(len(ids)>=min_n and rho is not None and pv is not None and rho<=cfg['spearman_rho_max'] and pv<=cfg['spearman_p_max'])
    holdout=(len(ids)>=min_n and improve is not None and kappa is not None and improve>=cfg['holdout_rmse_improvement_min'] and kappa>0)

    if len(ids)<min_n:
        status='INCONCLUSIVE'
        reason=f'insufficient_candidates: {len(ids)} < {min_n}'
    elif primary and holdout:
        status='PASS'; reason='both_confirmatory_gates_passed'
    else:
        status='FAIL'; reason='one_or_more_confirmatory_gates_failed'

    rows=[{"blind_id":i,"delay_score":P[i]['delay_score'],"linear_sigma0":P[i]['linear_sigma0'],"delay_feature_z":P[i]['delay_feature_z'],"observed_growth":M[i]['observed_growth'],"split":"train" if train[j] else "holdout"} for j,i in enumerate(ids)]
    out={
        "status":status,
        "status_reason":reason,
        "n":len(ids),
        "min_candidates_required":min_n,
        "primary":{"spearman_rho":rho,"p":pv,"threshold_rho_max":cfg['spearman_rho_max'],"threshold_p_max":cfg['spearman_p_max'],"evaluated":bool(len(ids)>=min_n),"pass":bool(primary)},
        "global_gain_holdout":{"kappa":kappa,"rmse_baseline":rmse0,"rmse_delay":rmse1,"fractional_improvement":improve,"required":cfg['holdout_rmse_improvement_min'],"evaluated":bool(len(ids)>=min_n),"pass":bool(holdout)},
        "rows":rows
    }
    dump(out_path,out); return _json_safe(out)

def reveal(eval_path,key_path,out_path):
    e=json.loads(Path(eval_path).read_text()); k=json.loads(Path(key_path).read_text()); mp={q['blind_id']:q for q in k['items']}
    for r in e['rows']: r.update({"source_name":mp[r['blind_id']]['source_name'],"source":mp[r['blind_id']]['source']})
    dump(out_path,e); return e
