"""Euler enstrophy transport identity audit on evolved snapshot triplets.
For Euler: D_t |omega|^2 = 2 omega_i omega_j d_j u_i.
This is a diagnostic, not a proof of a transport barrier.
"""
import json
import numpy as np
from pathlib import Path
from .spectral import SpectralEuler3D
from .cli import KNOTS,ROOT,_paths

def audit_one(knot):
    _,path=_paths(knot)
    with np.load(path,allow_pickle=False) as z:
        a,b,c=(np.asarray(z['v'][j],float) for j in (0,1,2))
        times=z['t'][:3]
    n=a.shape[0];sol=SpectralEuler3D(n)
    omega=[sol.curl(v) for v in (a,b,c)]
    s=[np.sum(w*w,axis=-1) for w in omega]
    dt=(s[2]-s[0])/(times[2]-times[0])
    sh=sol.fft(s[1]);grad_s=np.stack([sol.ifft(1j*sol.k[j]*sh) for j in range(3)],axis=-1)
    adv=np.sum(b*grad_s,axis=-1)
    bh=sol.fft(b)
    gradients=np.stack([np.stack([sol.ifft(1j*sol.k[j]*bh[...,i]) for j in range(3)],axis=-1) for i in range(3)],axis=-2)
    w=omega[1]
    stretch=2*np.einsum('...i,...ij,...j->...',w,gradients,w)
    lhs=dt+adv
    diff=lhs-stretch
    scale=max(float(np.linalg.norm(lhs)),float(np.linalg.norm(stretch)),1e-15)
    return {'knot':knot,'identity':'D_t(|omega|^2)=2 omega_i omega_j partial_j u_i',
      'relative_l2_residual':float(np.linalg.norm(diff)/scale),
      'corr':float(np.corrcoef(lhs.ravel(),stretch.ravel())[0,1]),
      'scope':'three-snapshot centered temporal difference + spectral derivatives',
      'qualification':'SCREEN_ONLY_NEEDS_DT_AND_DX_LADDERS'}
if __name__=='__main__':
    rows=[audit_one(k) for k in KNOTS]
    target=ROOT/'A064-v0.2.0-outputs'/'VORTEX_STRETCHING_AUDIT.json'
    target.write_text(json.dumps(rows,indent=2)+'\n')
    for row in rows:print(row['knot'],'stretch identity relL2=',row['relative_l2_residual'],'corr=',row['corr'])
