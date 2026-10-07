from __future__ import annotations
import math, numpy as np
from scipy.optimize import least_squares
from .numeric import mittag_leffler_relax

def _bic(rss,n,k): return float(n*math.log(max(rss/max(n,1),1e-300))+k*math.log(max(n,2)))

def _phase_design(name,p,s):
    if name=='W': return np.column_stack([s])
    if name=='KG': return np.column_stack([s,-p])
    if name=='DUFFING': return np.column_stack([s,-p,-p**3])
    if name=='SG': return np.column_stack([s,-np.sin(p)])
    raise ValueError(name)

def phase_model_competition(y,ss,ph,discovery_fraction=0.65):
    y=np.asarray(y,float); ss=np.asarray(ss,float); ph=np.asarray(ph,float); nt=y.shape[0]
    cut=max(4,min(nt-4,int(round(discovery_fraction*nt))))
    out={}
    for name in ('W','KG','DUFFING','SG'):
        Xtr=_phase_design(name,ph[:cut].ravel(),ss[:cut].ravel()); Ytr=y[:cut].ravel()
        coef=np.linalg.lstsq(Xtr,Ytr,rcond=None)[0]; rtr=Ytr-Xtr@coef; rss=float(rtr@rtr)
        Xte=_phase_design(name,ph[cut:].ravel(),ss[cut:].ravel()); Yte=y[cut:].ravel(); rte=Yte-Xte@coef
        nrmse=float(np.sqrt(np.mean(rte*rte))/max(np.std(Yte),1e-30))
        out[name]={"coef":[float(c) for c in coef],"design_condition":float(np.linalg.cond(Xtr)),
                   "discovery_rss":rss,"discovery_bic":_bic(rss,len(Ytr),Xtr.shape[1]),
                   "confirmation_nrmse":nrmse,"discovery_rows":len(Ytr),"confirmation_rows":len(Yte)}
    sg=out['SG']; comps=[out[k] for k in ('W','KG','DUFFING')]
    sg['delta_bic_vs_best']=float(min(c['discovery_bic'] for c in comps)-sg['discovery_bic'])
    sg['nrmse_ratio_vs_best']=float(sg['confirmation_nrmse']/max(min(c['confirmation_nrmse'] for c in comps),1e-30))
    sg['physical_coefficients']=bool(len(sg['coef'])>=2 and sg['coef'][0]>0 and sg['coef'][1]>0)
    return out

def normalize_ringdown(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float)
    if len(t)!=len(y) or len(t)<12: raise ValueError('ringdown requires >=12 matched samples')
    order=np.argsort(t); t=t[order]; y=y[order]; baseline=0.0; z=y.copy(); scale=float(z[0])
    if not np.isfinite(scale) or scale<=0: raise ValueError('non-positive ringdown scale')
    return t-t[0],z/scale,{"baseline":baseline,"scale":scale}

def _fit_model(name,t,y):
    tmax=max(float(t[-1]),1e-12); dt=max(float(np.median(np.diff(t))),1e-12)
    if name=='EXP':
        def pred(p,x): return np.exp(-x/np.exp(p[0]))
        p0=[math.log(max(tmax/3,dt))]; lo=[math.log(dt/5)]; hi=[math.log(tmax*20)]
    elif name=='STRETCHED':
        def pred(p,x): return np.exp(-np.power(x/np.exp(p[0]),np.exp(p[1])))
        p0=[math.log(max(tmax/3,dt)),math.log(.8)]; lo=[math.log(dt/5),math.log(.2)]; hi=[math.log(tmax*20),math.log(3.)]
    elif name=='BIEXP':
        def pred(p,x):
            t1=np.exp(p[0]); t2=np.exp(p[1]); w=1/(1+np.exp(-p[2])); return w*np.exp(-x/t1)+(1-w)*np.exp(-x/t2)
        p0=[math.log(max(tmax/5,dt)),math.log(max(tmax/1.5,2*dt)),0.0]; lo=[math.log(dt/5),math.log(dt/5),-8]; hi=[math.log(tmax*20),math.log(tmax*20),8]
    elif name=='ML':
        def pred(p,x): return mittag_leffler_relax(x,np.exp(p[0]),p[1])
        p0=[math.log(max(tmax/3,dt)),.75]; lo=[math.log(dt/5),.45]; hi=[math.log(tmax*20),.995]
    else: raise ValueError(name)
    sol=least_squares(lambda p:pred(p,t)-y,p0,bounds=(lo,hi),max_nfev=500,xtol=1e-10,ftol=1e-10,gtol=1e-10)
    yh=pred(sol.x,t); r=y-yh; params=[float(x) for x in sol.x]
    if name in ('EXP','STRETCHED','BIEXP','ML'): params[0]=float(np.exp(sol.x[0]))
    if name=='STRETCHED': params[1]=float(np.exp(sol.x[1]))
    if name=='BIEXP': params[1]=float(np.exp(sol.x[1])); params[2]=float(1/(1+np.exp(-sol.x[2])))
    return {"params":params,"rss":float(r@r),"bic":_bic(float(r@r),len(y),len(sol.x))}

def _predict(name,p,t):
    if name=='EXP': return np.exp(-t/p[0])
    if name=='STRETCHED': return np.exp(-np.power(t/p[0],p[1]))
    if name=='BIEXP': return p[2]*np.exp(-t/p[0])+(1-p[2])*np.exp(-t/p[1])
    return mittag_leffler_relax(t,p[0],p[1])

def ringdown_competition(t,y,train_fraction=.70):
    t,z,norm=normalize_ringdown(t,y); cut=max(8,min(len(t)-4,int(round(train_fraction*len(t))))); out={}
    for name in ('EXP','STRETCHED','BIEXP','ML'):
        fit=_fit_model(name,t[:cut],z[:cut]); yh=_predict(name,fit['params'],t); r=z[cut:]-yh[cut:]
        fit['holdout_nrmse']=float(np.sqrt(np.mean(r*r))/max(np.std(z[cut:]),1e-30)); out[name]=fit
    ml=out['ML']; comps=[out[k] for k in ('EXP','STRETCHED','BIEXP')]
    ml['delta_bic_vs_best']=float(min(c['bic'] for c in comps)-ml['bic'])
    ml['nrmse_ratio_vs_best']=float(ml['holdout_nrmse']/max(min(c['holdout_nrmse'] for c in comps),1e-30))
    ml['alpha']=float(ml['params'][1]); ml['tau']=float(ml['params'][0]); ml['normalization']=norm
    return out,t,z
