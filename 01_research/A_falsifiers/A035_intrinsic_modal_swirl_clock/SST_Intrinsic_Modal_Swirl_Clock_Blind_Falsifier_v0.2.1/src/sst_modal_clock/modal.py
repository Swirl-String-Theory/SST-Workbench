import numpy as np
from .geometry import aligned_normal_displacement

def analytic_signal(y):
    y=np.asarray(y,float); n=len(y); Y=np.fft.fft(y); h=np.zeros(n)
    if n%2==0: h[0]=h[n//2]=1;h[1:n//2]=2
    else: h[0]=1;h[1:(n+1)//2]=2
    return np.fft.ifft(Y*h)

def trajectory_displacement(z,ref=None):
    ref=np.asarray(z['x_reference'] if ref is None else ref,float)
    # v0.2.1: analysis is invariant to Stage-A tangential mesh gauge. Every
    # snapshot is re-expressed on uniform normalized arclength and cyclically
    # phase-aligned before rigid/normal projection.
    return np.asarray([aligned_normal_displacement(y,ref,parameterization_invariant=True) for y in z['x']]),ref

def odd_response(zp,zm,eps):
    ref=np.asarray(zp['x_reference'],float); dp,_=trajectory_displacement(zp,ref); dm,_=trajectory_displacement(zm,ref)
    return .5*(dp-dm)/max(float(eps),1e-15),ref

def natural_response(z0):
    return trajectory_displacement(z0)

def even_probe_contamination(zp,zm,z0):
    ref=np.asarray(z0['x_reference'],float); dp,_=trajectory_displacement(zp,ref); dm,_=trajectory_displacement(zm,ref); d0,_=trajectory_displacement(z0,ref)
    return .5*(dp+dm)-d0

def learn_modes(response,n_discovery,topk):
    X=response[:n_discovery].reshape(n_discovery,-1); center=X.mean(0,keepdims=True); Xc=X-center
    U,S,Vt=np.linalg.svd(Xc,full_matrices=False); total=float(np.sum(S*S)); modes=[]
    for k in range(min(topk,len(S))):
        v=Vt[k].copy(); j=int(np.argmax(np.abs(v))); v*=1 if v[j]>=0 else -1; modes.append(v)
    return np.asarray(modes),(S[:len(modes)]**2/max(total,1e-30)),center.ravel()

def project(response,modes,center=None):
    X=response.reshape(len(response),-1)
    if center is not None: X=X-np.asarray(center,float)[None,:]
    return X@modes.T

def mode_strain_weights(mode,ref):
    phi=np.asarray(mode).reshape(ref.shape); dx=np.roll(ref,-1,axis=0)-ref; ell=np.maximum(np.linalg.norm(dx,axis=1),1e-15); t=dx/ell[:,None]
    dphi=np.roll(phi,-1,axis=0)-phi; w=np.sum(dphi*t,axis=1)/ell; w=w-w.mean(); n=np.linalg.norm(w)
    return w/n if n>1e-15 else w

def _harmonic_fit(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float); n=len(y); dt=float(np.median(np.diff(t))); T=float(t[-1]-t[0]); yy=y-y.mean(); Y=np.fft.rfft(yy); f=np.fft.rfftfreq(n,dt); p=np.abs(Y)**2
    if len(p)<2 or np.sum(p[1:])<=1e-30:return None
    k=1+int(np.argmax(p[1:])); f0=float(f[k]); power=float(p[k]/np.sum(p[1:])); df=1/max(T,1e-15); freqs=np.linspace(max(.20*df,f0-df),f0+df,161); ss=float(np.sum(yy*yy)); best=None
    for ff in freqs:
        w=2*np.pi*ff; A=np.c_[np.ones(n),np.cos(w*t),np.sin(w*t)]; b=np.linalg.lstsq(A,y,rcond=None)[0]; pred=A@b; rss=float(np.sum((y-pred)**2)); r2=float(1-rss/ss) if ss>1e-30 else 0.
        if best is None or r2>best[0]: best=(r2,float(ff),b)
    r2,freq,b=best; return {'frequency':freq,'period':1/freq if freq>0 else np.inf,'spectral_power_fraction':power,'harmonic_r2':r2,'amplitude':float(np.hypot(b[1],b[2]))}

def _cycle_periods_from_phase(t,y,period_hint):
    y=np.asarray(y,float)-float(np.mean(y)); z=analytic_signal(y); ph=np.unwrap(np.angle(z)); sgn=1 if np.polyfit(np.asarray(t,float),ph,1)[0]>=0 else -1; ph=sgn*ph
    # enforce weak monotonicity only for crossing extraction, not for the data itself
    base=float(ph[0]); twopi=2*np.pi; lo=int(np.ceil((ph.min()-base)/twopi)); hi=int(np.floor((ph.max()-base)/twopi)); crossings=[]
    for m in range(lo,hi+1):
        target=base+m*twopi; d=ph-target
        idx=np.where((d[:-1]<=0)&(d[1:]>0))[0]
        if len(idx):
            i=int(idx[0]); a=d[i]; b=d[i+1]; f=0. if b==a else -a/(b-a); crossings.append(float(t[i]+f*(t[i+1]-t[i])))
    periods=np.diff(crossings)
    if np.isfinite(period_hint) and len(periods): periods=periods[(periods>.35*period_hint)&(periods<2.5*period_hint)]
    return periods

def recurrence_metrics(t,y,max_returns=4):
    t=np.asarray(t,float); y=np.asarray(y,float); n=len(y)
    if n<24:return {'valid':False,'reason':'TOO_SHORT'}
    fit=_harmonic_fit(t,y)
    if not fit:return {'valid':False,'reason':'NO_OSCILLATION'}
    period=float(fit['period']); amp=float(fit['amplitude']); T=float(t[-1]-t[0]); cycles=float(T/period) if np.isfinite(period) else 0.; dt=float(np.median(np.diff(t))); yy=y-y.mean(); v=np.gradient(y,t,edge_order=2); w=2*np.pi/max(period,1e-15)
    closure_by_return=[]
    for r in range(1,int(max_returns)+1):
        lag=max(1,int(round(r*period/dt)))
        min_overlap=max(12,int(round(.5*period/dt)))
        if n-lag<min_overlap: closure_by_return.append(np.nan); continue
        d=np.sqrt(((y[lag:]-y[:-lag])/max(amp,1e-15))**2+((v[lag:]-v[:-lag])/max(w*amp,1e-15))**2)
        closure_by_return.append(float(np.median(d)))
    finite=[x for x in closure_by_return if np.isfinite(x)]
    periods=_cycle_periods_from_phase(t,y,period); period_cv=float(np.std(periods)/max(np.mean(periods),1e-15)) if len(periods)>=2 else np.inf
    # Cycle amplitude stationarity on fixed harmonic-period bins.
    nc=int(np.floor(cycles)); amps=[]; means=[]
    for i in range(nc):
        a=t[0]+i*period; b=a+period; mask=(t>=a)&(t<b)
        if np.count_nonzero(mask)>=6:
            yyseg=y[mask]; amps.append(.5*float(np.max(yyseg)-np.min(yyseg))); means.append(float(np.mean(yyseg)))
    amp_cv=float(np.std(amps)/max(np.mean(amps),1e-15)) if len(amps)>=2 else np.inf
    drift=float(abs(means[-1]-means[0])/max(amp,1e-15)) if len(means)>=2 else np.inf
    return {'valid':True,**fit,'cycles':cycles,'multi_return_closure':closure_by_return,'multi_return_closure_median':float(np.median(finite)) if finite else np.inf,'multi_return_closure_max':float(np.max(finite)) if finite else np.inf,'n_return_closures':len(finite),'cycle_periods':periods.tolist(),'period_cv':period_cv,'cycle_amplitudes':amps,'amplitude_cv':amp_cv,'cycle_mean_drift_fraction':drift}

def delayed_stretch_test(t,a,stretch,period,discovery_time=1.0,n_null=31):
    t=np.asarray(t,float); a=np.asarray(a,float); s=np.asarray(stretch,float); n=len(t); nd=int(np.searchsorted(t,float(discovery_time),side='right')); nd=max(8,min(n-8,nd)); acc=np.gradient(np.gradient(a,t,edge_order=2),t,edge_order=2); dt=float(np.median(np.diff(t)))
    maxlag=max(2,min(nd//3,int(round(.75*period/dt)))) if np.isfinite(period) else max(2,nd//4)
    def corr(x,y):
        x=np.asarray(x,float);y=np.asarray(y,float);x=x-x.mean();y=y-y.mean(); den=np.linalg.norm(x)*np.linalg.norm(y); return float(x@y/den) if den>1e-15 else 0.
    best=(0,0.)
    for lag in range(1,maxlag+1):
        if nd-lag<6:break
        c=corr(s[:nd-lag],acc[lag:nd])
        if abs(c)>abs(best[1]):best=(lag,c)
    lag,cd=best; hs=s[nd:n-lag] if n-lag>nd else np.array([]); ha=acc[nd+lag:n] if n>nd+lag else np.array([]); ch=corr(hs,ha) if len(hs)>=6 else 0.; z=corr(s[nd:n],acc[nd:n]) if n-nd>=6 else 0.; obs=abs(ch); null=[]; m=len(hs)
    if m>=8:
        base=s[nd:n].copy()
        for j in range(1,n_null+1):
            sh=max(1,int(round(j*len(base)/(n_null+1)))); null.append(abs(corr(np.roll(base,sh)[:m],ha)))
    p=(1+sum(v>=obs for v in null))/(1+len(null)) if null else 1.
    return {'lag_samples':int(lag),'delay':float(lag*dt),'discovery_corr':float(cd),'holdout_corr':float(ch),'zero_lag_holdout_corr':float(z),'delay_advantage_abs_corr':float(abs(ch)-abs(z)),'phase_null_p':float(p),'discovery_time_used':float(t[nd-1])}
