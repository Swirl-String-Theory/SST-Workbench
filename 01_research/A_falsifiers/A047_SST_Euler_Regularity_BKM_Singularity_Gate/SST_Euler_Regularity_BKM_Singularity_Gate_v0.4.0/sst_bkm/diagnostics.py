from __future__ import annotations

import math
import numpy as np
from .spectral import wave_numbers, curl_hat


def diagnostics(uh,L):
    N=uh.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L)
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    wh=curl_hat(uh,kx,ky,kz)
    w=np.fft.ifftn(wh,axes=(1,2,3)).real
    umag=np.sqrt(np.sum(u*u,axis=0)); wmag=np.sqrt(np.sum(w*w,axis=0))
    energy=0.5*np.mean(np.sum(u*u,axis=0))
    helicity=np.mean(np.sum(u*w,axis=0))
    enstrophy=0.5*np.mean(np.sum(w*w,axis=0))
    divh=1j*(kx*uh[0]+ky*uh[1]+kz*uh[2])
    div=np.fft.ifftn(divh).real
    idx=np.unravel_index(np.argmax(wmag),wmag.shape)
    G=np.empty((3,3),float); ks=(kx,ky,kz)
    for a in range(3):
        for b in range(3):
            G[a,b]=np.fft.ifftn(1j*ks[b]*uh[a]).real[idx]
    S=0.5*(G+G.T); W=0.5*(G-G.T)
    evals,evecs=np.linalg.eigh(S)
    wv=w[:,idx[0],idx[1],idx[2]]; wn=np.linalg.norm(wv)
    xi=wv/wn if wn>0 else np.zeros(3)
    align=float(xi@S@xi) if wn>0 else 0.0
    wx,wy,wz=wv
    Wexp=np.array([[0.0,-0.5*wz,0.5*wy],[0.5*wz,0.0,-0.5*wx],[-0.5*wy,0.5*wx,0.0]])
    decomp=float(np.linalg.norm(G-(S+Wexp))/max(np.linalg.norm(G),1e-30))
    return {
        "energy":float(energy),"helicity":float(helicity),"enstrophy":float(enstrophy),"max_u":float(umag.max()),
        "max_omega":float(wmag.max()),"div_rms":float(np.sqrt(np.mean(div*div))),
        "strain_lambda_max":float(evals[-1]),"omega_strain_alignment":align,
        "relative_vorticity_decomposition_error":decomp,
        "hot_index":[int(x) for x in idx],"principal_strain_vector":[float(x) for x in evecs[:,-1]],
    }


def inverse_omega_fit(times,maxomega,late_fraction=0.45,candidate_horizon_factor=1.5,r2_min=0.98):
    t=np.asarray(times,float); m=np.asarray(maxomega,float)
    n=len(t); i=max(0,int((1.0-late_fraction)*n))
    x=t[i:]; y=1.0/np.maximum(m[i:],1e-300)
    if len(x)<5: return {"candidate":False,"reason":"too_few_points","late_fraction":late_fraction}
    p=np.polyfit(x,y,1); pred=np.polyval(p,x)
    ssr=float(np.sum((y-pred)**2)); sst=float(np.sum((y-y.mean())**2))
    r2=1.0-ssr/sst if sst>0 else 0.0
    slope,intercept=float(p[0]),float(p[1])
    tstar=-intercept/slope if slope<0 else None
    tend=float(t[-1])
    candidate=bool(tstar is not None and tstar>tend and tstar<=candidate_horizon_factor*tend and r2>=r2_min)
    return {"candidate":candidate,"slope":slope,"intercept":intercept,"r2":r2,"t_star":tstar,"late_fraction":late_fraction}


def blowup_fit(times,maxomega,late_fraction=0.45):
    # Backward-compatible v0.3.0 name/contract.
    return inverse_omega_fit(times,maxomega,late_fraction=late_fraction)


def _aicc_from_rss(rss,n,k):
    rss=max(float(rss),1e-300); n=int(n); k=int(k)
    aic=n*math.log(rss/n)+2*k
    if n-k-1<=0: return float('inf')
    return float(aic+(2*k*(k+1))/(n-k-1))


def _fit_exponential(t,m):
    y=np.log(np.maximum(m,1e-300)); p=np.polyfit(t,y,1); pred=np.polyval(p,t)
    rss=float(np.sum((y-pred)**2))
    return {'model':'exponential','rate':float(p[0]),'logA':float(p[1]),'rss_log':rss,'aicc':_aicc_from_rss(rss,len(t),2)}


def _fit_algebraic_nonsingular(t,m):
    # log omega = a + gamma log(1+t/tau), tau>0; grid tau, linear gamma.
    y=np.log(np.maximum(m,1e-300)); span=max(float(t[-1]-t[0]),1e-9)
    taus=np.geomspace(max(span*0.05,1e-6),max(span*20.0,1e-5),240)
    best=None
    for tau in taus:
        x=np.log1p(np.maximum(t-t[0],0.0)/tau)
        A=np.column_stack([np.ones_like(x),x]); beta=np.linalg.lstsq(A,y,rcond=None)[0]; pred=A@beta
        rss=float(np.sum((y-pred)**2)); aicc=_aicc_from_rss(rss,len(t),3)
        if best is None or aicc<best['aicc']:
            best={'model':'algebraic_nonsingular','tau':float(tau),'gamma':float(beta[1]),'logA':float(beta[0]),'rss_log':rss,'aicc':aicc}
    return best


def _fit_finite_time_power(t,m,tstar_max_factor=5.0):
    # log omega = logA - gamma log(t*-t), search only future t*>T.
    y=np.log(np.maximum(m,1e-300)); T=float(t[-1]); span=max(float(T-t[0]),1e-9)
    lo=T+max(span*0.01,1e-6); hi=max(T*tstar_max_factor,T+span*8)
    grid=np.geomspace(max(lo-T,1e-8),max(hi-T,1e-7),500)+T
    best=None
    for ts in grid:
        d=ts-t
        if np.any(d<=0): continue
        x=-np.log(d)
        A=np.column_stack([np.ones_like(x),x]); beta=np.linalg.lstsq(A,y,rcond=None)[0]; pred=A@beta
        gamma=float(beta[1]); rss=float(np.sum((y-pred)**2)); aicc=_aicc_from_rss(rss,len(t),3)
        if best is None or aicc<best['aicc']:
            best={'model':'finite_time_power','t_star':float(ts),'gamma':gamma,'logA':float(beta[0]),'rss_log':rss,'aicc':aicc}
    return best


def model_competition(times,maxomega,config=None):
    cfg=dict(config or {})
    t=np.asarray(times,float); m=np.asarray(maxomega,float)
    windows=list(cfg.get('late_fractions',[0.35,0.45,0.55]))
    daic_min=float(cfg.get('delta_aicc_min',10.0)); gamma_min=float(cfg.get('gamma_min',0.9))
    tstar_spread_max=float(cfg.get('tstar_relative_spread_max',0.15))
    rows=[]
    for frac in windows:
        i=max(0,int((1.0-float(frac))*len(t))); tw=t[i:]; mw=m[i:]
        if len(tw)<8:
            rows.append({'late_fraction':float(frac),'status':'TOO_FEW_POINTS'}); continue
        finite=_fit_finite_time_power(tw,mw,float(cfg.get('tstar_max_factor',5.0)))
        exp=_fit_exponential(tw,mw); alg=_fit_algebraic_nonsingular(tw,mw)
        nonsing=min((exp,alg),key=lambda x:x['aicc'])
        delta=float(nonsing['aicc']-finite['aicc'])
        rows.append({'late_fraction':float(frac),'finite_time':finite,'best_nonsingular':nonsing,'delta_aicc_finite_vs_nonsingular':delta})
    valid=[r for r in rows if 'finite_time' in r]
    tstars=[r['finite_time']['t_star'] for r in valid]
    gammas=[r['finite_time']['gamma'] for r in valid]
    deltas=[r['delta_aicc_finite_vs_nonsingular'] for r in valid]
    spread=(max(tstars)-min(tstars))/max(float(np.mean(tstars)),1e-30) if len(tstars)>=2 else None
    pass_gate=bool(valid and len(valid)==len(windows) and min(deltas)>=daic_min and min(gammas)>=gamma_min and spread is not None and spread<=tstar_spread_max)
    return {
        'windows':rows,'finite_time_model_gate_pass':pass_gate,
        'min_delta_aicc':min(deltas) if deltas else None,'min_gamma':min(gammas) if gammas else None,
        'tstar_relative_spread':spread,'thresholds':{'delta_aicc_min':daic_min,'gamma_min':gamma_min,'tstar_relative_spread_max':tstar_spread_max},
    }
