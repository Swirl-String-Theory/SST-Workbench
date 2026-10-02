from __future__ import annotations
import numpy as np
from .geometry import split_components,pack,total_length

def normal_field(points,offsets,harmonics=(1,2,3,4)):
    comps=split_components(points,offsets); fields=[]
    for C in comps:
        n=len(C);t=np.roll(C,-1,axis=0)-np.roll(C,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
        g=np.array([0.,0.,1.]);N=g-(t@g)[:,None]*t;bad=np.linalg.norm(N,axis=1)<1e-6
        if np.any(bad):
            g2=np.array([0.,1.,0.]);N[bad]=g2-(t[bad]@g2)[:,None]*t[bad]
        N/=np.linalg.norm(N,axis=1)[:,None];s=np.arange(n)/n; amp=np.zeros(n)
        for h in harmonics: amp += np.sin(2*np.pi*h*s+0.37*h)/len(harmonics)
        fields.append(N*amp[:,None])
    return pack(fields)[0]

def perturbed(points,offsets,eps,sign=1):
    F=normal_field(points,offsets);X=points+sign*eps*F
    # recenter and rescale total arclength to 1; action test is fixed-L shape excitation.
    X=X-X.mean(0); comps=split_components(X,offsets); L=total_length(comps);X=X/L
    return X
