import numpy as np
from .geometry import aligned_normal_displacement,tangents

def analytic_signal(y):
    y=np.asarray(y,float); n=len(y); Y=np.fft.fft(y); h=np.zeros(n)
    if n%2==0: h[0]=h[n//2]=1;h[1:n//2]=2
    else: h[0]=1;h[1:(n+1)//2]=2
    return np.fft.ifft(Y*h)
def odd_response(zp,zm,eps):
    ref=np.asarray(zp['x_reference'],float); dp=np.asarray([aligned_normal_displacement(y,ref) for y in zp['x']]); dm=np.asarray([aligned_normal_displacement(y,ref) for y in zm['x']]); return .5*(dp-dm)/max(float(eps),1e-15),ref

def learn_modes(response,n_discovery,topk):
    X=response[:n_discovery].reshape(n_discovery,-1); X=X-X.mean(0,keepdims=True); U,S,Vt=np.linalg.svd(X,full_matrices=False); modes=[]; total=float(np.sum(S*S))
    for k in range(min(topk,len(S))):
        v=Vt[k].copy(); j=int(np.argmax(np.abs(v))); v*=1 if v[j]>=0 else -1; modes.append(v)
    return np.asarray(modes), (S[:len(modes)]**2/max(total,1e-30))
def project(response,modes): return response.reshape(len(response),-1)@modes.T

def mode_strain_weights(mode,ref):
    phi=np.asarray(mode).reshape(ref.shape); dx=np.roll(ref,-1,axis=0)-ref; ell=np.maximum(np.linalg.norm(dx,axis=1),1e-15); t=dx/ell[:,None]; dphi=np.roll(phi,-1,axis=0)-phi; w=np.sum(dphi*t,axis=1)/ell; w=w-w.mean(); n=np.linalg.norm(w); return w/n if n>1e-15 else w

def detrend(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float); X=np.c_[np.ones(len(t)),t]; b=np.linalg.lstsq(X,y,rcond=None)[0]; return y-X@b

def recurrence_metrics(t,y):
    t=np.asarray(t,float); y=detrend(t,np.asarray(y,float)); n=len(y)
    if n<16:return {'valid':False,'reason':'TOO_SHORT'}
    dt=float(np.median(np.diff(t))); Y=np.fft.rfft(y); f=np.fft.rfftfreq(n,dt); p=np.abs(Y)**2
    if len(p)<2 or np.sum(p[1:])<=1e-30:return {'valid':False,'reason':'NO_OSCILLATION'}
    k=1+int(np.argmax(p[1:])); f0=float(f[k]); power=float(p[k]/np.sum(p[1:])); T=float(t[-1]-t[0]); df=1/max(T,1e-15)
    # Refine the frequency locally so a holdout window need not contain an integer number of cycles.
    freqs=np.linspace(max(.25*df,f0-df),f0+df,121); ss=float(np.sum((y-y.mean())**2)); best=None
    for ff in freqs:
        w0=2*np.pi*ff; A0=np.c_[np.ones(n),np.cos(w0*t),np.sin(w0*t)]; b0=np.linalg.lstsq(A0,y,rcond=None)[0]; pred0=A0@b0; rss=float(np.sum((y-pred0)**2)); r20=float(1-rss/ss) if ss>1e-30 else 0.
        if best is None or r20>best[0]: best=(r20,float(ff),b0)
    r2,freq,b=best; period=1/freq if freq>0 else np.inf; cycles=float(T/period) if np.isfinite(period) else 0; w=2*np.pi*freq; amp=float(np.hypot(b[1],b[2])); v=np.gradient(y,t,edge_order=2); lag=max(1,int(round(period/dt))); closure=np.nan
    if lag<n//2:
        scale=max(amp,1e-15); d=np.sqrt(((y[lag:]-y[:-lag])/scale)**2+((v[lag:]-v[:-lag])/max(w*scale,1e-15))**2); closure=float(np.median(d))
    half=n//2; rms1=float(np.sqrt(np.mean(y[:half]**2))); rms2=float(np.sqrt(np.mean(y[half:]**2))); ratio=rms2/max(rms1,1e-15)
    return {'valid':True,'frequency':freq,'period':period,'spectral_power_fraction':power,'cycles':cycles,'harmonic_r2':r2,'amplitude':amp,'recurrence_closure_error':closure,'late_to_early_rms_ratio':ratio}

def delayed_stretch_test(t,a,stretch,period,discovery_fraction=.4,n_null=31):
    t=np.asarray(t,float); a=np.asarray(a,float); s=np.asarray(stretch,float); n=len(t); nd=max(8,min(n-8,int(round(discovery_fraction*n)))); acc=np.gradient(np.gradient(a,t,edge_order=2),t,edge_order=2); dt=float(np.median(np.diff(t))); maxlag=max(2,min(nd//3,int(round(.75*period/dt)))) if np.isfinite(period) else max(2,nd//4)
    def corr(x,y):
        x=x-x.mean();y=y-y.mean(); den=np.linalg.norm(x)*np.linalg.norm(y); return float(x@y/den) if den>1e-15 else 0.
    best=(0,0.)
    for lag in range(1,maxlag+1):
        if nd-lag<6:break
        c=corr(s[:nd-lag],acc[lag:nd])
        if abs(c)>abs(best[1]):best=(lag,c)
    lag,cd=best; hs=s[nd:n-lag] if n-lag>nd else np.array([]); ha=acc[nd+lag:n] if n>nd+lag else np.array([]); ch=corr(hs,ha) if len(hs)>=6 else 0.; z=corr(s[nd:n],acc[nd:n]) if n-nd>=6 else 0.; obs=abs(ch); null=[]; m=len(hs)
    if m>=8:
        base=s[nd:n].copy()
        for j in range(1,n_null+1):
            sh=max(1,int(round(j*len(base)/(n_null+1)))); rolled=np.roll(base,sh)[:m]; null.append(abs(corr(rolled,ha)))
    p=(1+sum(v>=obs for v in null))/(1+len(null)) if null else 1.
    return {'lag_samples':int(lag),'delay':float(lag*dt),'discovery_corr':float(cd),'holdout_corr':float(ch),'zero_lag_holdout_corr':float(z),'delay_advantage_abs_corr':float(abs(ch)-abs(z)),'phase_null_p':float(p)}
