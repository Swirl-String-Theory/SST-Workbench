from __future__ import annotations
import numpy as np
from .geometry import kabsch_align, radius_of_gyration


def signed_projection(pert: np.ndarray, base: np.ndarray, seed_disp: np.ndarray) -> tuple[float,float]:
    pa=kabsch_align(pert,base);d=pa-base;denom=float(np.sum(seed_disp*seed_disp))
    a=float(np.sum(d*seed_disp)/denom) if denom>0 else 0.0
    rms=float(np.sqrt(np.mean(np.sum(d*d,axis=1)))/max(radius_of_gyration(base),1e-300))
    return a,rms


def zero_cross_frequency(t: np.ndarray,a: np.ndarray)->float:
    t=np.asarray(t,float);a=np.asarray(a,float)
    if len(t)<5:return float('nan')
    x=a-np.mean(a);cross=[]
    for i in range(len(x)-1):
        if x[i]==0:cross.append(t[i])
        elif x[i]*x[i+1]<0:
            f=abs(x[i])/(abs(x[i])+abs(x[i+1]));cross.append(t[i]+f*(t[i+1]-t[i]))
    if len(cross)<4:return float('nan')
    period=2.0*float(np.median(np.diff(cross)));return 2*np.pi/period if period>0 else float('nan')


def dominant_frequency(t: np.ndarray,a: np.ndarray)->tuple[float,str,float]:
    """Zero-crossing estimate first; conservative FFT fallback with peak-fraction confidence."""
    w=zero_cross_frequency(t,a)
    if np.isfinite(w):return float(w),'zero_crossing',1.0
    t=np.asarray(t,float);x=np.asarray(a,float)
    if len(t)<12:return float('nan'),'unresolved',0.0
    dt=float(np.median(np.diff(t)))
    if not np.allclose(np.diff(t),dt,rtol=1e-5,atol=max(abs(dt)*1e-8,1e-300)):return float('nan'),'unresolved',0.0
    x=x-np.mean(x);win=np.hanning(len(x));spec=np.abs(np.fft.rfft(x*win))**2;freq=np.fft.rfftfreq(len(x),dt)
    if len(spec)<=2:return float('nan'),'unresolved',0.0
    spec[0]=0.0;i=int(np.argmax(spec));total=float(np.sum(spec));score=float(spec[i]/total) if total>0 else 0.0
    cycles=float(freq[i]*(t[-1]-t[0]))
    if i<2 or cycles<1.5 or score<0.35:return float('nan'),'unresolved',score
    return float(2*np.pi*freq[i]),'fft',score


def envelope_gamma(t: np.ndarray,a: np.ndarray)->float:
    t=np.asarray(t,float);y=np.abs(np.asarray(a,float));idx=[i for i in range(1,len(y)-1) if y[i]>=y[i-1] and y[i]>y[i+1] and y[i]>1e-12]
    if len(idx)<3:return float('nan')
    tt=t[idx];yy=y[idx];mask=yy>max(np.max(yy)*1e-6,1e-15)
    if np.count_nonzero(mask)<3:return float('nan')
    slope,_=np.polyfit(tt[mask],np.log(yy[mask]),1);return float(max(0.0,-slope))


def kelvin_duration(t: np.ndarray,a: np.ndarray)->float:
    """Kelvin-like support time applied to S(t)=a(t)^2."""
    t=np.asarray(t,float);S=np.asarray(a,float)**2
    if len(t)<2:return float('nan')
    # np.trapz is available on NumPy 1.26 and 2.x.
    trap=getattr(np,'trapezoid',np.trapz);i1=float(trap(S,t));i2=float(trap(S*S,t));return i1*i1/i2 if i2>0 else float('nan')


def kelvin_window_metrics(t: np.ndarray,a: np.ndarray)->dict:
    out={}
    for frac in (0.5,0.75,1.0):
        n=max(3,int(round(frac*len(t))));out[f'T_K_{int(frac*100)}_s']=kelvin_duration(t[:n],a[:n])
    full=out['T_K_100_s'];out['T_K_over_window']=full/max(float(t[-1]-t[0]),1e-300) if np.isfinite(full) else float('nan');return out


def energy_metrics(h: np.ndarray)->dict:
    h=np.asarray(h,float);h0=float(h[0]);den=max(abs(h0),1e-300);rel=(h-h0)/den
    return {'H0_J':h0,'energy_rel_maxabs':float(np.max(np.abs(rel))),'energy_rel_min':float(np.min(rel)),'energy_rel_final':float(rel[-1])}
