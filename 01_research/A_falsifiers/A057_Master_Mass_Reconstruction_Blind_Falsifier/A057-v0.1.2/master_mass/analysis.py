from __future__ import annotations
import hashlib,math
import numpy as np
from .utils import safe_mean,safe_std,safe_cv

def summarize_by_topology(rows,key='energy_kernel'):
    groups={}
    for r in rows:
        if r.get(key) is None:continue
        groups.setdefault(r['topology_id'],[]).append(r)
    out={}
    for top,rs in groups.items():
        vals=[r[key] for r in rs if np.isfinite(r[key])]
        out[top]={"n":len(vals),"mean":safe_mean(vals),"std":safe_std(vals),"cv":safe_cv(vals),"independence_groups":sorted({str(r.get('independence_group')) for r in rs if r.get('independence_group')})}
        # aggregate descriptor means
        for d in ['ropelength_proxy','bending','torsion2','writhe_sum','bishop_holonomy_abs_sum','linking_abs_sum','mutual_helicity_unit_circulation']:
            vv=[r.get('geometry',{}).get(d) for r in rs];vv=[x for x in vv if x is not None and np.isfinite(x)]
            out[top][d]=safe_mean(vv)
        # Topology-reference scalars are copied only when E010 provides them explicitly.
        for d in ['hyperbolic_volume','genus','bridge_index','braid_index','crossing_number']:
            vv=[r.get('topology_features',{}).get('values',{}).get(d) for r in rs];vv=[x for x in vv if x is not None and np.isfinite(x)]
            out[top][d]=safe_mean(vv)
    return out

def variance_discriminator(summary):
    means=np.array([v['mean'] for v in summary.values() if v.get('mean') is not None],float)
    within=np.array([v['std'] for v in summary.values() if v.get('std') is not None and v.get('n',0)>1],float)
    between=float(np.std(means,ddof=1)) if len(means)>1 else np.nan; w=float(np.nanmedian(within)) if len(within) else np.nan
    ratio=float(between/max(w,1e-30)) if np.isfinite(between) and np.isfinite(w) else None
    return {"between_std":between if np.isfinite(between) else None,"median_within_std":w if np.isfinite(w) else None,"between_to_within":ratio}

def split_label(topology,seed=570106):
    h=int(hashlib.sha256(f'{seed}:{topology}'.encode()).hexdigest()[:8],16)%10
    return 'discovery' if h<6 else ('confirmation' if h<8 else 'holdout')

def _features(summary,feature_names):
    rows=[]
    for top,v in summary.items():
        if v.get('mean') is None or v['mean']<=0:continue
        x=[];ok=True
        for f in feature_names:
            z=v.get(f)
            if z is None or not np.isfinite(z):ok=False;break
            x.append(float(z))
        if ok:rows.append((top,np.array(x),math.log(v['mean'])))
    return rows

def ridge_fit_predict(train,test,lam=1e-6):
    if not train:return []
    X=np.vstack([x for _,x,_ in train]);y=np.array([y for *_,y in train]);mu=X.mean(0);sd=X.std(0);sd[sd<1e-12]=1
    Z=(X-mu)/sd;A=np.column_stack([np.ones(len(Z)),Z]);coef=np.linalg.solve(A.T@A+lam*np.eye(A.shape[1]),A.T@y)
    out=[]
    for top,x,y0 in test:
        z=(x-mu)/sd;yp=float(np.r_[1,z]@coef);out.append((top,y0,yp))
    return out

def rmse(pred):return float(np.sqrt(np.mean([(a-b)**2 for _,a,b in pred]))) if pred else None

def model_competition(summary):
    families={
      'length_only':['ropelength_proxy'],
      'geometry3':['ropelength_proxy','bending','torsion2'],
      'topology_geometry':['ropelength_proxy','bending','torsion2','writhe_sum','linking_abs_sum'],
      'hyperbolic_volume_only':['hyperbolic_volume'],
      'geometry_plus_hyperbolic':['ropelength_proxy','bending','torsion2','hyperbolic_volume'],
    }
    results={}
    for name,features in families.items():
        rows=_features(summary,features);train=[r for r in rows if split_label(r[0])=='discovery'];conf=[r for r in rows if split_label(r[0])=='confirmation'];hold=[r for r in rows if split_label(r[0])=='holdout']
        pc=ridge_fit_predict(train,conf);ph=ridge_fit_predict(train,hold)
        results[name]={"features":features,"n_train":len(train),"n_confirmation":len(conf),"n_holdout":len(hold),"confirmation_log_rmse":rmse(pc),"holdout_log_rmse":rmse(ph),"confirmation_predictions":[{"topology":t,"actual_log":a,"pred_log":p} for t,a,p in pc],"holdout_predictions":[{"topology":t,"actual_log":a,"pred_log":p} for t,a,p in ph]}
    return results
