#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from finite_core_spectral.core import spectrum_at_q, write_json

def main():
 p=argparse.ArgumentParser(description='One dimensionless finite-core ring spectrum.')
 p.add_argument('--q',type=float,required=True); p.add_argument('--n-nodes',type=int,default=24); p.add_argument('--ring-radius-over-core',type=float,default=4.0)
 p.add_argument('--image-shell',type=int,default=1); p.add_argument('--fd-eps-over-core',type=float,default=1e-4); p.add_argument('--core-model',type=int,default=0); p.add_argument('--threads',type=int,default=1)
 p.add_argument('--neutral-modes',type=int,default=6); p.add_argument('--residual-max',type=float,default=5e-2); p.add_argument('--force-python',action='store_true'); p.add_argument('--force-build',action='store_true'); p.add_argument('--build-verbose',action='store_true'); p.add_argument('--save-eigs',action='store_true'); p.add_argument('--out',default='')
 a=p.parse_args(); cfg=vars(a).copy();
 for k in ['q','force_python','force_build','build_verbose','save_eigs','out']: cfg.pop(k,None)
 cfg.update({'q_min':a.q-1e-6,'q_max':a.q+1e-6,'q_step':1e-6,'eig_zero_tol':1e-8})
 r=spectrum_at_q(cfg,a.q,force_python=a.force_python,force_build=a.force_build,build_verbose=a.build_verbose,save_eigs=a.save_eigs)
 if a.out: write_json(a.out,r)
 print(json.dumps(r,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
