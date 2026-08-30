import numpy as np
from .geometry import fourier_normal_basis,align_cyclic,normalize_length
from .dynamics import simulate

def _series_for_mode(tr,x0,mode,pattern):
    a=[]; sig=[]
    pattern=np.asarray(pattern,float); pattern=pattern-np.mean(pattern); pattern/=max(np.linalg.norm(pattern),1e-15)
    for x,s in zip(tr['x'],tr['sigma']):
        xa,_,_,_,_=align_cyclic(x,x0,4)
        a.append(float(np.sum((xa-x0)*mode)))
        sig.append(float(np.dot(s,pattern)))
    return np.asarray(a),np.asarray(sig),tr['t']

def _accel(a,t):
    if len(a)<5:return np.zeros_like(a)
    v=np.gradient(a,t); return np.gradient(v,t)

def _rmse(y,x=None):
    if x is None:
        yh=np.full_like(y,np.mean(y)); return float(np.sqrt(np.mean((y-yh)**2)))
    A=np.c_[np.ones(len(x)),x]; b=np.linalg.lstsq(A,y,rcond=None)[0]; yh=A@b; return float(np.sqrt(np.mean((y-yh)**2)))

def _discover_lag(sig,acc,maxlag):
    best=(0,-1.0)
    for lag in range(1,maxlag+1):
        if len(sig)-lag<6: break
        c=np.corrcoef(sig[:-lag],acc[lag:])[0,1]
        if np.isfinite(c) and abs(c)>best[1]: best=(lag,abs(float(c)))
    return best

def causal_gate(x0,T,cfg):
    basis,labels=fourier_normal_basis(x0,max(2,int(cfg.get('causal_basis_kmax',2)))); mode=basis[0]; eps=float(cfg.get('causal_eps',3e-4)); out={}; pattern=np.cos(2*np.pi*np.arange(len(x0))/len(x0))
    for coremode in ('material','fixed'):
        trs=[]
        for sign in (+1,-1): trs.append(simulate(normalize_length(x0+sign*eps*mode,2*np.pi),cfg,T,mode=coremode,long_mesh=False,store_samples=int(cfg.get('causal_samples',160))))
        ap,sp,t=_series_for_mode(trs[0],x0,mode,pattern); am,sm,_=_series_for_mode(trs[1],x0,mode,pattern); a=(ap-am)/(2*eps); sig=(sp-sm)/(2*eps); acc=_accel(a,t); n=len(t); cut=max(5,n//2); maxlag=max(1,min(int(cfg.get('causal_max_lag_samples',24)),cut//3)); lag,c=_discover_lag(sig[:cut],acc[:cut],maxlag)
        y=acc[cut+lag:]; x=sig[cut:len(sig)-lag] if lag else sig[cut:]
        if len(y)!=len(x): m=min(len(y),len(x)); y=y[:m];x=x[:m]
        r0=_rmse(y); r1=_rmse(y,x) if len(y)>=5 else r0; imp=float((r0-r1)/max(r0,1e-15)); dt=float(np.median(np.diff(t))) if len(t)>1 else float('nan'); tau=lag*dt
        # measured oscillation frequency from odd amplitude, no target phase
        ac=a-a.mean(); z=np.fft.rfft(ac); f=np.fft.rfftfreq(len(ac),dt) if np.isfinite(dt) else np.array([0.]); k=int(np.argmax(np.abs(z[1:]))+1) if len(z)>1 else 0; omega=float(2*np.pi*f[k]) if k<len(f) else 0.0; phase=float((omega*tau)%(2*np.pi))
        out[coremode]={'discovery_lag_samples':lag,'discovery_abs_corr':c,'measured_delay':tau,'measured_omega':omega,'measured_phase':phase,'holdout_rmse_null':r0,'holdout_rmse_delay':r1,'holdout_improvement':imp,'completed':all(tr['stop_reason']=='COMPLETED' for tr in trs)}
    m=out['material']; f=out['fixed']
    advantage=float(m['holdout_improvement']-f['holdout_improvement'])
    # v0.2.0: the fixed-core arm is allowed to discover its own best lag, making it a
    # conservative null.  A material-core mechanism requires both absolute predictive
    # improvement and a preregistered material-over-fixed advantage. Measured phase is
    # diagnostic only; no target phase appears in this gate.
    gate=bool(m['completed'] and f['completed']
              and m['holdout_improvement']>=float(cfg.get('causal_min_material_improvement',.10))
              and f['holdout_improvement']<=float(cfg.get('causal_max_fixed_improvement',.05))
              and advantage>=float(cfg.get('causal_min_material_advantage_over_fixed',.08)))
    out['material_minus_fixed_holdout_improvement']=advantage
    out['measured_phase_is_diagnostic_only']=True
    out['mechanism_gate_pass']=gate; return out
