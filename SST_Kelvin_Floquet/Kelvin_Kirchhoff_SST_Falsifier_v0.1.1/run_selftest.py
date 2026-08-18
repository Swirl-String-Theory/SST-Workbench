from __future__ import annotations
import argparse, math, tempfile
from pathlib import Path
import numpy as np
from kk_native.core import load_backend,induced_velocity
from kk_native.fallback import induced_velocity as py_velocity
from kelvin_falsifier.geometry import rigid_fit,resample_closed,parallel_frame
from kelvin_falsifier.io import read_components

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--require-native',action='store_true'); ap.add_argument('--threads',type=int,default=4); a=ap.parse_args()
    backend,name=load_backend(require_native=a.require_native,build_verbose=True)
    print('[SELFTEST] backend:',name)
    n=64; th=np.linspace(0,2*np.pi,n,endpoint=False); c=np.c_[np.cos(th),np.sin(th),np.zeros(n)]; off=[0,n]
    vnat,_=induced_velocity(c,off,0.15,1.0,threads=a.threads,require_native=a.require_native)
    vpy=py_velocity(c,off,0.15,1.0)
    rel=np.linalg.norm(vnat-vpy)/max(np.linalg.norm(vpy),1e-30); print('[SELFTEST] native/python relerr=',rel)
    if rel>2e-12: raise SystemExit('native/python mismatch')
    # exact rigid fit
    U=np.array([0.2,-0.1,0.3]); w=np.array([0.0,0.0,0.7]); vv=U+np.cross(np.tile(w,(n,1)),c-c.mean(axis=0)); fit=rigid_fit(c,vv)
    if fit['relative_residual']>1e-12: raise SystemExit('rigid fit failed')
    r=resample_closed(c,101)
    if len(r)!=101: raise SystemExit('resample failed')
    t,nn,b=parallel_frame(r)
    if not np.all(np.isfinite(nn)): raise SystemExit('frame failed')
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'x.txt'; p.write_text('0 0 0\n1 0 0\n0 1 0\n\n0 0 1\n1 0 1\n0 1 1\n')
        if len(read_components(p))!=2: raise SystemExit('multi-component parser failed')
    print('[SELFTEST] PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
