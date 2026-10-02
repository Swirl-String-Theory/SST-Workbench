#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from finite_core_spectral.core import run_scan, write_json, write_csv

def main():
 p=argparse.ArgumentParser(description='Blind convergence ladder over discretization/core regularization.')
 p.add_argument('--out-dir',default='audit_refinement'); p.add_argument('--threads',type=int,default=1); p.add_argument('--q-min',type=float,default=2.5); p.add_argument('--q-max',type=float,default=16.0); p.add_argument('--q-step',type=float,default=0.5); p.add_argument('--force-build',action='store_true')
 a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); allrows=[]; summaries=[]
 cases=[(16,0,1e-3),(24,0,3e-4),(32,0,1e-4),(24,1,3e-4),(24,2,3e-4)]
 for idx,(n,model,eps) in enumerate(cases):
  cfg={'n_nodes':n,'ring_radius_over_core':4.0,'q_min':a.q_min,'q_max':a.q_max,'q_step':a.q_step,'image_shell':1,'fd_eps_over_core':eps,'core_model':model,'threads':a.threads,'neutral_modes':6,'eig_zero_tol':1e-8,'residual_max':5e-2}
  res=run_scan(cfg,force_build=(a.force_build and idx==0),progress=True)
  tag=f'N{n}_M{model}_E{eps:g}'; write_json(out/f'{tag}.json',res)
  for r in res['rows']: allrows.append({'case':tag,**r})
  summaries.append({'case':tag,'n_candidates':len(res['candidates']),'candidates':res['candidates']})
 write_csv(out/'refinement_rows.csv',allrows); write_json(out/'refinement_summary.json',summaries); print(json.dumps(summaries,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
