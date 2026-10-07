from __future__ import annotations
import math
import numpy as np
from scipy.optimize import least_squares
from .numeric import mittag_leffler_relax

def _bic(rss,n,k): return float(n*math.log(max(rss/n,1e-300))+k*math.log(max(n,2)))

def phase_model_competition(y,ss,ph,folds=4):
    y=np.asarray(y,float); ss=np.asarray(ss,float); ph=np.asarray(ph,float)
    nt,ns=y.shape
    specs={
      'W': lambda p,s: np.column_stack([s]),
      'KG': lambda p,s: np.column_stack([s,-p]),
      'DUFFING': lambda p,s: np.column_stack([s,-p,-p**3]),
      'SG': lambda p,s: np.column_stack([s,-np.sin(p)]),
    }
    blocks=np.array_split(np.arange(nt),min(folds,nt))
    out={}
    for name,fn in specs.items():
        rss_cv=0.0; n_cv=0; y_all=[]; r_all=[]
        for block in blocks:
            train=np.setdiff1d(np.arange(nt),block)
            Xtr=fn(ph[train].ravel(),ss[train].ravel()); Ytr=y[train].ravel()
            coef=np.linalg.lstsq(Xtr,Ytr,rcond=None)[0]
            Xte=fn(ph[block].ravel(),ss[block].ravel()); Yte=y[block].ravel()
            res=Yte-Xte@coef; rss_cv+=float(res@res); n_cv+=len(res); y_all.append(Yte); r_all.append(res)
        Y=np.concatenate(y_all); R=np.concatenate(r_all)
        nrmse=float(np.sqrt(np.mean(R*R))/max(np.std(Y),1e-30))
        X=fn(ph.ravel(),ss.ravel()); Yf=y.ravel(); coef=np.linalg.lstsq(X,Yf,rcond=None)[0]
        out[name]={"coef":[float(c) for c in coef],"design_condition":float(np.linalg.cond(X)),"cv_rss":rss_cv,"cv_n":n_cv,"cv_nrmse":nrmse,"cv_bic":_bic(rss_cv,n_cv,X.shape[1])}
    sg=out['SG']; comps=[out[k] for k in ('W','KG','DUFFING')]
    best_bic=min(c['cv_bic'] for c in comps); best_nrmse=min(c['cv_nrmse'] for c in comps)
    sg['delta_bic_vs_best']=float(best_bic-sg['cv_bic'])
    sg['nrmse_ratio_vs_best']=float(sg['cv_nrmse']/max(best_nrmse,1e-30))
    sg['physical_coefficients']=bool(len(sg['coef'])>=2 and sg['coef'][0]>0 and sg['coef'][1]>0)
    return out

def normalize_ringdown(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float)
    if len(t)!=len(y) or len(t)<12: raise ValueError('ringdown requires >=12 matched samples')
    order=np.argsort(t); t=t[order]; y=y[order]
    # v0.1.0 assumes the provider supplies a zero-baseline non-negative amplitude.
    # Automatic late-time subtraction is forbidden because it can erase a genuine
    # long Mittag-Leffler tail and create a false preference for finite exponentials.
    baseline=0.0; z=y.copy()
    scale=float(z[0])
    if not np.isfinite(scale) or scale<=0: raise ValueError('non-positive ringdown scale')
    z=z/scale; t=t-t[0]
    return t,z,{"baseline":baseline,"scale":scale}

def _fit_model(name,t,y):
    tmax=max(float(t[-1]),1e-12); dt=max(float(np.median(np.diff(t))),1e-12)
    if name=='EXP':
        def pred(p,x): return np.exp(-x/np.exp(p[0]))
        p0=[math.log(max(tmax/3,dt))]; lo=[math.log(dt/5)]; hi=[math.log(tmax*20)]
    elif name=='STRETCHED':
        def pred(p,x): return np.exp(-np.power(x/np.exp(p[0]),np.exp(p[1])))
        p0=[math.log(max(tmax/3,dt)),math.log(0.8)]; lo=[math.log(dt/5),math.log(0.2)]; hi=[math.log(tmax*20),math.log(3.0)]
    elif name=='BIEXP':
        def pred(p,x):
            t1=np.exp(p[0]); t2=np.exp(p[1]); w=1/(1+np.exp(-p[2])); return w*np.exp(-x/t1)+(1-w)*np.exp(-x/t2)
        p0=[math.log(max(tmax/5,dt)),math.log(max(tmax/1.5,2*dt)),0.0]; lo=[math.log(dt/5),math.log(dt/5),-8]; hi=[math.log(tmax*20),math.log(tmax*20),8]
    elif name=='ML':
        def pred(p,x): return mittag_leffler_relax(x,np.exp(p[0]),p[1])
        p0=[math.log(max(tmax/3,dt)),0.75]; lo=[math.log(dt/5),0.45]; hi=[math.log(tmax*20),0.995]
    else: raise ValueError(name)
    sol=least_squares(lambda p: pred(p,t)-y,p0,bounds=(lo,hi),max_nfev=500,xtol=1e-10,ftol=1e-10,gtol=1e-10)
    yh=pred(sol.x,t); r=y-yh; rss=float(r@r)
    params=[float(x) for x in sol.x]
    if name in ('EXP','STRETCHED','BIEXP','ML'): params[0]=float(np.exp(sol.x[0]))
    if name=='STRETCHED': params[1]=float(np.exp(sol.x[1]))
    if name=='BIEXP': params[1]=float(np.exp(sol.x[1])); params[2]=float(1/(1+np.exp(-sol.x[2])))
    return {"params":params,"rss":rss,"bic":_bic(rss,len(y),len(sol.x)),"pred":yh}

def ringdown_competition(t,y,train_fraction=0.70):
    t,z,norm=normalize_ringdown(t,y); cut=max(8,min(len(t)-4,int(round(train_fraction*len(t)))))
    tr=np.arange(cut); te=np.arange(cut,len(t)); out={}
    for name in ('EXP','STRETCHED','BIEXP','ML'):
        fit=_fit_model(name,t[tr],z[tr])
        # refit helper to reconstruct prediction on all x from physical params
        p=fit['params']
        if name=='EXP': yh=np.exp(-t/p[0])
        elif name=='STRETCHED': yh=np.exp(-np.power(t/p[0],p[1]))
        elif name=='BIEXP': yh=p[2]*np.exp(-t/p[0])+(1-p[2])*np.exp(-t/p[1])
        else: yh=mittag_leffler_relax(t,p[0],p[1])
        r=z[te]-yh[te]; nrmse=float(np.sqrt(np.mean(r*r))/max(np.std(z[te]),1e-30))
        fit.pop('pred',None); fit['holdout_nrmse']=nrmse; out[name]=fit
    ml=out['ML']; comps=[out[k] for k in ('EXP','STRETCHED','BIEXP')]
    ml['delta_bic_vs_best']=float(min(c['bic'] for c in comps)-ml['bic'])
    ml['nrmse_ratio_vs_best']=float(ml['holdout_nrmse']/max(min(c['holdout_nrmse'] for c in comps),1e-30))
    ml['alpha']=float(ml['params'][1]); ml['tau']=float(ml['params'][0]); ml['normalization']=norm
    return out, t, z
