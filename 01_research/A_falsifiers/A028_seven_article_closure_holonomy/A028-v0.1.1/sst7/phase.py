from __future__ import annotations
import numpy as np

def wrapped_delta(x):
    return np.angle(np.exp(1j*x))

def winding(phi):
    phi=np.asarray(phi,float).reshape(-1)
    d=wrapped_delta(np.roll(phi,-1)-phi)
    return float(d.sum()/(2*np.pi))

def phase_purity(phi,mmax=None):
    phi=np.asarray(phi,float).reshape(-1)
    f=np.exp(1j*phi)
    c=np.fft.fft(f)/len(f)
    p=np.abs(c)**2
    k=np.fft.fftfreq(len(f))*len(f)
    if mmax is not None:
        mask=np.abs(k)<=mmax; k,p=k[mask],p[mask]
    order=np.argsort(p)[::-1]
    return [(int(round(k[i])),float(p[i])) for i in order[:8]]

def sampling_windings(phi, ns=(32,64,128,256)):
    phi=np.asarray(phi,float).reshape(-1)
    out=[]
    for n in ns:
        if n>len(phi): continue
        idx=np.floor(np.arange(n)*len(phi)/n).astype(int)
        out.append((n,winding(phi[idx])))
    if not out: out=[(len(phi),winding(phi))]
    return out
