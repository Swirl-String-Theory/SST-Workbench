from __future__ import annotations
from pathlib import Path
import numpy as np
from .spectral_euler import velocity_from_vorticity,dealias_mask,wave_numbers
ROOT=Path(__file__).resolve().parents[1]

def _python_seed(P,N,L,sigma):
    P=np.asarray(P,float); T=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0); T/=np.linalg.norm(T,axis=1)[:,None]
    dx=L/N; q=-.5*L+(np.arange(N)+.5)*dx; X=np.stack(np.meshgrid(q,q,q,indexing='ij'),axis=-1); om=np.zeros((3,N,N,N),float); inv=1/(2*sigma*sigma)
    for p,t in zip(P,T):
        d=(X-p+.5*L)%L-.5*L; d2=np.sum(d*d,axis=-1); w=np.exp(-d2*inv)*(d2<=18*sigma*sigma)
        for c in range(3): om[c]+=w*t[c]
    return om

def centerline_vorticity(P,N,L,sigma,prefer_native=True):
    if prefer_native:
        try:
            from sst_falsifier.backends.cpp_pybind import load
            mod,build=load(ROOT,force_build=False,require=False,verbose=False)
            if mod is not None and hasattr(mod,'centerline_vorticity_seed'):
                return np.asarray(mod.centerline_vorticity_seed(np.ascontiguousarray(P,float),int(N),float(L),float(sigma),1.0)),{"backend":"cpp","build":build.to_dict() if build else None}
        except Exception: pass
    return _python_seed(P,int(N),float(L),float(sigma)),{"backend":"python"}

def velocity_seed(P,N,L,sigma,prefer_native=True):
    om,info=centerline_vorticity(P,N,L,sigma,prefer_native); uh=velocity_from_vorticity(om,L); mask=dealias_mask(N); uh*=mask[None,...]
    u=np.fft.ifftn(uh,axes=(1,2,3)).real; rms=float(np.sqrt(np.mean(np.sum(u*u,axis=0))))
    if not np.isfinite(rms) or rms<=0: raise RuntimeError('invalid finite-core seed RMS velocity')
    return uh/rms,{**info,"velocity_rms_before_normalization":rms}
