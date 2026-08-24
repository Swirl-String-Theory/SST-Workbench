from __future__ import annotations
import numpy as np

def _one_peak(t,y):
    t=np.asarray(t,float); y=np.asarray(y,float)
    y=y-np.mean(y)
    dt=float(np.median(np.diff(t)))
    f=np.fft.rfftfreq(len(t),dt)
    p=np.abs(np.fft.rfft(y))**2
    if len(p)<=1: return np.nan
    i=1+int(np.argmax(p[1:]))
    return float(f[i])

def peak_set(t,signals):
    a=np.asarray(signals,float)
    if a.ndim==1: a=a[None,:,None]
    elif a.ndim==2: a=a[:,:,None]
    elif a.ndim!=3: raise ValueError('signals must be T, runsxT or runsxTxchannels')
    peaks=[]
    for run in a:
        pp=[_one_peak(t,run[:,c]) for c in range(run.shape[1])]
        peaks.append(pp)
    return np.asarray(peaks,float)

def peak_cv(peaks):
    p=np.asarray(peaks,float)
    vals=p[np.isfinite(p)&(p>0)]
    if len(vals)<2: return np.nan
    return float(np.std(vals)/np.mean(vals))

def finite_size_collapse(peaks,L):
    p=np.asarray(peaks,float)
    L=np.asarray(L,float).reshape(-1)
    if p.shape[0]!=len(L): return np.nan
    first=np.nanmedian(p,axis=1)
    scaled=first*L
    return float(np.nanstd(scaled)/(np.nanmean(np.abs(scaled))+1e-300))


def dominant_mode_under_sampling(phi,ns=(32,64,128,256,512),mmax=32):
    """Return the dominant Fourier winding of exp(i phi) under subsampling."""
    phi=np.asarray(phi,float).reshape(-1)
    out=[]
    for n in ns:
        if n>len(phi): continue
        idx=np.floor(np.arange(n)*len(phi)/n).astype(int)
        f=np.exp(1j*phi[idx]); c=np.fft.fft(f)/n; k=np.rint(np.fft.fftfreq(n)*n).astype(int)
        mask=np.abs(k)<=min(mmax,n//2)
        kk=k[mask]; pp=np.abs(c[mask])**2
        j=int(np.argmax(pp)); out.append((int(n),int(kk[j]),float(pp[j])))
    return out
