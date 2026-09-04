import numpy as np
from .geometry import radius_gyration

def length(x): return float(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1).sum())

def segment_quality(x):
    ds=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1); m=float(ds.mean())
    return {'ds_min':float(ds.min()),'ds_max':float(ds.max()),'ds_ratio':float(ds.max()/max(ds.min(),1e-30)),'ds_cv':float(ds.std()/max(m,1e-30))}

def analytic_signal(y):
    y=np.asarray(y,float); n=len(y); Y=np.fft.fft(y); h=np.zeros(n)
    if n%2==0: h[0]=h[n//2]=1; h[1:n//2]=2
    else: h[0]=1; h[1:(n+1)//2]=2
    return np.fft.ifft(Y*h)

def dominant_period(t,y):
    t=np.asarray(t); y=np.asarray(y)-np.mean(y)
    if len(y)<8: return np.nan,np.nan
    dt=float(np.median(np.diff(t))); f=np.fft.rfftfreq(len(y),dt); p=np.abs(np.fft.rfft(y))**2
    if len(p)<=1 or np.all(p[1:]==0): return np.nan,np.nan
    k=1+int(np.argmax(p[1:])); frac=float(p[k]/max(p[1:].sum(),1e-30))
    return (1.0/f[k] if f[k]>0 else np.nan),frac

def second_derivative(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float)
    return np.gradient(np.gradient(y,t,edge_order=2),t,edge_order=2)

def first_derivative(t,y): return np.gradient(np.asarray(y,float),np.asarray(t,float),edge_order=2)

def interp(t,y,x): return float(np.interp(float(x),np.asarray(t,float),np.asarray(y,float)))

def packet_track(delta_sigma,t,min_corr=.15):
    S=np.asarray(delta_sigma,float); t=np.asarray(t,float); M,N=S.shape
    # remove spatial DC and slow material background
    S=S-S.mean(axis=1,keepdims=True)
    norms=np.linalg.norm(S,axis=1); packet_rms_peak=float(np.max(norms)/np.sqrt(max(N,1)))
    nz=np.where(norms>max(norms.max()*1e-4,1e-15))[0]
    if len(nz)==0: return {'available':False,'reason':'NO_DIFFERENTIAL_PACKET'}
    iref=int(nz[min(1,len(nz)-1)]); ref=S[iref]; refn=np.linalg.norm(ref)
    if refn<1e-15: return {'available':False,'reason':'ZERO_TEMPLATE'}
    lags=[]; corrs=[]
    for row in S:
        rn=np.linalg.norm(row)
        if rn<1e-15: lags.append(np.nan); corrs.append(0.0); continue
        cc=np.fft.ifft(np.fft.fft(row)*np.conj(np.fft.fft(ref))).real/(rn*refn)
        k=int(np.argmax(cc)); ks=k if k<=N//2 else k-N
        # parabolic sub-index refinement
        km=(k-1)%N; kp=(k+1)%N; y0,y1,y2=cc[km],cc[k],cc[kp]; den=(y0-2*y1+y2)
        off=0.0 if abs(den)<1e-15 else 0.5*(y0-y2)/den; off=float(np.clip(off,-.5,.5))
        lags.append(ks+off); corrs.append(float(cc[k]))
    lag=np.asarray(lags,float); valid=np.isfinite(lag)
    if valid.sum()<6: return {'available':False,'reason':'TOO_FEW_PACKET_SAMPLES'}
    phase=np.full(M,np.nan); phase[valid]=np.unwrap(2*np.pi*lag[valid]/N)
    phase=phase-phase[iref]
    # direction determined by robust median slope after reference
    ids=np.where(valid & (np.arange(M)>=iref))[0]
    if len(ids)<4: return {'available':False,'reason':'TOO_SHORT'}
    coef=np.polyfit(t[ids],phase[ids],1); slope=float(coef[0])
    direction=1.0 if slope>=0 else -1.0
    prog=direction*phase
    target=2*np.pi
    cross=np.where((np.arange(M)>iref) & np.isfinite(prog) & (prog>=target))[0]
    if len(cross)==0:
        total=float(np.nanmax(prog[iref:])) if np.any(np.isfinite(prog[iref:])) else 0.0
        return {'available':False,'reason':'NO_FULL_RETURN','packet_rms_peak':packet_rms_peak,'total_cycles':total/(2*np.pi),'median_corr':float(np.median(np.asarray(corrs)[ids])),'slope':slope}
    j=int(cross[0]); j0=max(iref,j-1)
    p0,p1=prog[j0],prog[j]; t0,t1=t[j0],t[j]
    tau=float(t1 if p1==p0 else t0+(target-p0)*(t1-t0)/(p1-p0))
    cmed=float(np.median(np.asarray(corrs)[ids]))
    monot=float(np.mean(np.diff(prog[ids])>=-0.05))
    dtmed=float(np.median(np.diff(t))) if len(t)>1 else 0.0
    phase_res=2*np.pi/N
    tau_unc=float(abs(phase_res/max(abs(slope),1e-15)) + .5*dtmed)
    return {'available':bool(cmed>=min_corr),'reason':'OK' if cmed>=min_corr else 'LOW_CORRELATION','tau_return':tau,'tau_uncertainty':tau_unc,'packet_phase_resolution_rad':phase_res,'packet_rms_peak':packet_rms_peak,'median_corr':cmed,'monotonic_fraction':monot,'slope':slope,'total_cycles':float(np.nanmax(prog[iref:])/(2*np.pi)),'phase_series':phase,'corr_series':np.asarray(corrs)}


def breathing_harmonic_phase(t,y,tau,scan_points=161):
    """Fit a single coherent breathing harmonic and evaluate its phase at tau.

    Frequency is refined by a dense local scan around the dominant FFT bin.
    Returns an explicit lower-bound phase uncertainty from coefficient covariance,
    frequency-grid resolution, and (optionally added by caller) return-time uncertainty.
    """
    t=np.asarray(t,float); y=np.asarray(y,float)
    if len(t)<12 or not np.isfinite(y).all():
        return {'available':False,'reason':'TOO_FEW_BREATHING_SAMPLES'}
    y0=y-np.mean(y); dt=float(np.median(np.diff(t))); T=float(t[-1]-t[0])
    if T<=0 or np.sqrt(np.mean(y0*y0))<1e-15:
        return {'available':False,'reason':'NO_BREATHING_SIGNAL'}
    f=np.fft.rfftfreq(len(y),dt); P=np.abs(np.fft.rfft(y0))**2
    if len(P)<2 or np.all(P[1:]<=0):
        return {'available':False,'reason':'NO_BREATHING_PEAK'}
    k=1+int(np.argmax(P[1:])); f0=float(f[k]); df=1.0/max(T,1e-15)
    flo=max(df*0.25,f0-df); fhi=f0+df
    freqs=np.linspace(flo,fhi,max(21,int(scan_points)))
    best=None
    for ff in freqs:
        w=2*np.pi*ff
        X=np.c_[np.ones(len(t)),np.cos(w*t),np.sin(w*t)]
        b=np.linalg.lstsq(X,y,rcond=None)[0]; pred=X@b
        ss=float(((y-y.mean())**2).sum()); rss=float(((y-pred)**2).sum()); r2=1-rss/ss if ss>0 else 0.0
        if best is None or r2>best[0]: best=(r2,ff,w,X,b,rss)
    r2,ff,w,X,b,rss=best; a=float(b[1]); bb=float(b[2]); amp=float(np.hypot(a,bb))
    if amp<1e-15: return {'available':False,'reason':'ZERO_HARMONIC_AMPLITUDE'}
    delta=float(np.arctan2(bb,a)); phi=float(np.angle(np.exp(1j*(w*float(tau)-delta))))
    dof=max(len(t)-3,1); s2=rss/dof
    try:
        cov=s2*np.linalg.inv(X.T@X); va=float(cov[1,1]); vb=float(cov[2,2]); cab=float(cov[1,2])
        vard=(bb*bb*va+a*a*vb-2*a*bb*cab)/max((a*a+bb*bb)**2,1e-30)
        coeff_unc=float(np.sqrt(max(vard,0.0)))
    except np.linalg.LinAlgError:
        coeff_unc=float('inf')
    domega_grid=2*np.pi*float(freqs[1]-freqs[0]) if len(freqs)>1 else float('inf')
    grid_unc=.5*abs(domega_grid*float(tau))
    return {'available':True,'reason':'OK','phase_rad':phi,'frequency':ff,'omega':w,'period':1.0/ff,
            'harmonic_r2':float(r2),'amplitude':amp,'coefficient_phase_uncertainty_rad':coeff_unc,
            'frequency_grid_phase_uncertainty_rad':grid_unc,
            'phase_uncertainty_without_return_time_rad':float(np.hypot(coeff_unc,grid_unc)),
            'frequency_scan_step':float(freqs[1]-freqs[0]) if len(freqs)>1 else np.nan}

def phase_at(t,q,tau):
    q=np.asarray(q,float); qd=q-np.mean(q); z=analytic_signal(qd)
    ph=np.unwrap(np.angle(z)); return float(np.angle(np.exp(1j*np.interp(tau,t,ph))))
