#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from finite_core_spectral.core import independence_manifest, run_scan, write_csv, write_json

def main():
 p=argparse.ArgumentParser(description='Single blind dimensionless finite-core spectral scan. No external physical constants or targets are accepted.')
 p.add_argument('--out-dir',default='audit_out'); p.add_argument('--n-nodes',type=int,default=32); p.add_argument('--ring-radius-over-core',type=float,default=4.0)
 p.add_argument('--q-min',type=float,default=2.31); p.add_argument('--q-max',type=float,default=4.10); p.add_argument('--q-step',type=float,default=0.025)
 p.add_argument('--image-shell',type=int,default=2); p.add_argument('--fd-eps-over-core',type=float,default=1e-4); p.add_argument('--core-model',type=int,default=0); p.add_argument('--threads',type=int,default=1)
 p.add_argument('--neutral-modes',type=int,default=6); p.add_argument('--eig-zero-tol',type=float,default=1e-8); p.add_argument('--residual-max',type=float,default=5e-2)
 p.add_argument('--force-python',action='store_true'); p.add_argument('--force-build',action='store_true'); p.add_argument('--build-verbose',action='store_true'); p.add_argument('--quiet',action='store_true')
 a=p.parse_args(); cfg={k:v for k,v in vars(a).items() if k not in {'out_dir','force_python','force_build','build_verbose','quiet'}}
 out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); write_json(out/'independence_manifest.json',independence_manifest(cfg))
 res=run_scan(cfg,force_python=a.force_python,force_build=a.force_build,build_verbose=a.build_verbose,progress=not a.quiet)
 write_json(out/'scan.json',res); write_csv(out/'scan.csv',res['rows']); write_json(out/'candidate_scales.json',res['candidates']); write_json(out/'mode_tracking.json',res['mode_tracking'])
 summary={'ok':True,'dimensionless_only':True,'config_sha256':res['config_sha256'],'n_points':len(res['rows']),'n_candidates':len(res['candidates']),
          'neutral_candidates_below_fd_gate_suppressed':True,'equilibrium_gate_pass_fraction':sum(r['equilibrium_gate_ok'] for r in res['rows'])/len(res['rows']),
          'candidate_kinds':sorted({c['kind'] for c in res['candidates']})}
 write_json(out/'audit_summary.json',summary); print(json.dumps(summary,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
