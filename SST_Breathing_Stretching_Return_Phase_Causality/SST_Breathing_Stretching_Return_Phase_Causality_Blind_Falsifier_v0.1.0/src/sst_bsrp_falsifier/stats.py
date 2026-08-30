import numpy as np

def design(phi):
    p=np.asarray(phi,float); return np.c_[np.ones(len(p)),np.cos(p),np.sin(p)]

def fit_circular(phi,y):
    X=design(phi); y=np.asarray(y,float); b=np.linalg.lstsq(X,y,rcond=None)[0]; pred=X@b
    ss=float(((y-y.mean())**2).sum()); r2=1-float(((y-pred)**2).sum())/ss if ss>0 else 0.0
    amp=float(np.hypot(b[1],b[2])); opt=float(np.angle(b[1]+1j*b[2]))
    return {'beta0':float(b[0]),'beta_cos':float(b[1]),'beta_sin':float(b[2]),'amplitude':amp,'phase_max_rad':opt,'r2':r2}

def loco_cv(phi,y,groups):
    phi=np.asarray(phi); y=np.asarray(y); groups=np.asarray(groups); pred=np.full(len(y),np.nan)
    for g in np.unique(groups):
        te=groups==g; tr=~te
        if tr.sum()<4: continue
        b=np.linalg.lstsq(design(phi[tr]),y[tr],rcond=None)[0]; pred[te]=design(phi[te])@b
    ok=np.isfinite(pred); ss=float(((y[ok]-y[ok].mean())**2).sum()) if ok.sum()>1 else 0
    return 1-float(((y[ok]-pred[ok])**2).sum())/ss if ss>0 else float('nan')

def grouped_permutation_p(phi,y,groups,nperm=999,seed=12345):
    rng=np.random.default_rng(seed); obs=loco_cv(phi,y,groups); vals=[]; groups=np.asarray(groups); y=np.asarray(y)
    uniq=np.unique(groups)
    for _ in range(nperm):
        yp=y.copy()
        # permute phase labels by whole carrier groups, preserving within-carrier structure
        perm=uniq.copy(); rng.shuffle(perm); mp={a:b for a,b in zip(uniq,perm)}
        pp=np.empty_like(np.asarray(phi,float))
        for a in uniq:
            src=np.where(groups==mp[a])[0]; dst=np.where(groups==a)[0]
            if len(src)==len(dst): pp[dst]=np.asarray(phi)[src]
            else: pp[dst]=rng.choice(np.asarray(phi)[src],size=len(dst),replace=True)
        vals.append(loco_cv(pp,y,groups))
    vals=np.asarray(vals,float); return float((1+np.sum(vals>=obs))/(1+len(vals))),float(obs)
