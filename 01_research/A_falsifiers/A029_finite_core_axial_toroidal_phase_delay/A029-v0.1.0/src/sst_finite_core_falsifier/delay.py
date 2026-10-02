from __future__ import annotations
import numpy as np
TWOPI=2*np.pi

def wrap(x): return float(np.angle(np.exp(1j*float(x))))

def loop_wavenumber(length_over_a,m,n,holonomy,closure_offset=0.0):
    """Bishop-frame loop closure: k L + m*holonomy = 2pi(n+offset)."""
    L=float(length_over_a); return float((TWOPI*(float(n)+float(closure_offset))-float(m)*float(holonomy))/max(L,1e-14))

def wavepacket_return(length_over_a,k0,omega0,poly_coeff,group_velocity,n_modes=31,n_times=401):
    """Propagate a narrow wave packet using the measured local dispersion polynomial.
    No delay is supplied; the return time is measured from the periodic propagation.
    """
    L=float(length_over_a); vg=float(group_velocity)
    if not np.isfinite(vg) or abs(vg)<1e-8:return {'available':False,'reason':'near-zero group velocity'}
    tau_pred=L/abs(vg); j=np.arange(-(int(n_modes)//2),int(n_modes)//2+1); q=TWOPI*j/L; sig=max(2*TWOPI/L,0.22*abs(k0)+1e-3); amp=np.exp(-0.5*(q/sig)**2); amp/=np.sum(amp)
    t=np.linspace(0,1.55*tau_pred,int(n_times)); co=np.asarray(poly_coeff,float); domega=np.polyval(co,q)-np.polyval(co,0.0); A=np.array([np.sum(amp*np.exp(-1j*domega*tt)) for tt in t]); mag=np.abs(A); mask=(t>=.55*tau_pred)&(t<=1.45*tau_pred)
    if not np.any(mask):return {'available':False,'reason':'empty return window'}
    inds=np.where(mask)[0]; ip=int(inds[np.argmax(mag[inds])]); tau=float(t[ip]); full_phase=wrap(-float(omega0)*tau+float(np.angle(A[ip]))); return {'available':True,'tau_group':tau_pred,'tau_return':tau,'tau_relative_error':float(abs(tau/tau_pred-1)),'return_coherence':float(mag[ip]/max(mag[0],1e-30)),'loop_phase':full_phase,'t_peak_index':ip}

def circular_features(phi): return np.c_[np.ones(len(phi)),np.cos(phi),np.sin(phi)]

def circular_regression_cv(phi,y,groups):
    phi=np.asarray(phi,float);y=np.asarray(y,float);groups=np.asarray(groups); pred=np.full(len(y),np.nan)
    ug=list(dict.fromkeys(groups.tolist()))
    for g in ug:
        tr=groups!=g;te=groups==g
        if np.sum(tr)<4:continue
        X=circular_features(phi[tr]); q=np.linalg.lstsq(X,y[tr],rcond=None)[0];pred[te]=circular_features(phi[te])@q
    m=np.isfinite(pred)&np.isfinite(y)
    if np.sum(m)<4:return {'cv_r2':float('nan'),'rmse':float('nan'),'n':int(np.sum(m))}
    ss=float(np.sum((y[m]-pred[m])**2));den=float(np.sum((y[m]-np.mean(y[m]))**2));r2=1-ss/max(den,1e-30);return {'cv_r2':float(r2),'rmse':float(np.sqrt(np.mean((y[m]-pred[m])**2))),'n':int(np.sum(m))}
