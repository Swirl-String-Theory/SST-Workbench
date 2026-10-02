#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, time
import numpy as np
from finite_core_spectral.core import _backend

def main():
    ap=argparse.ArgumentParser(description='Dimensionless native C4 performance benchmark; no external target used.')
    ap.add_argument('--n',type=int,default=48); ap.add_argument('--shell',type=int,default=2); ap.add_argument('--threads',type=int,default=16); ap.add_argument('--q',type=float,default=2.5)
    a=ap.parse_args(); b,name=_backend(False,False,True)
    if name!='cpp' or not hasattr(b,'ring_normal_jacobian_c4'):
        print(json.dumps({'ok':False,'backend':name,'note':'native v0.1.2.3 backend required'},indent=2)); return 1
    cell=math.exp(a.q); args=(a.n,4.0,cell,a.shell,1e-4,0,a.threads,True)
    t=time.perf_counter(); full=np.asarray(b.ring_normal_jacobian(*args)); tf=time.perf_counter()-t
    t=time.perf_counter(); fast=np.asarray(b.ring_normal_jacobian_c4(*args)); tc=time.perf_counter()-t
    audit=dict(b.ring_c4_symmetry_audit(a.n,4.0,cell,a.shell,1e-4,0,True))
    rel=float(np.linalg.norm(full-fast)/max(np.linalg.norm(full),1e-300))
    out={'ok':bool(rel<1e-8 and float(audit['relative_error'])<1e-8),'backend':name,'n_nodes':a.n,'image_shell':a.shell,'threads':a.threads,'full_seconds':tf,'c4_seconds':tc,'speedup':tf/max(tc,1e-300),'relative_matrix_error':rel,'c4_audit':audit}
    print(json.dumps(out,indent=2)); return 0 if out['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
