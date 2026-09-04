#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from finite_core_spectral.core import independence_manifest, write_json, write_csv
from finite_core_spectral.convergence import adaptive_case, evaluate_primary_convergence

BASE={
 'n_nodes':64,'ring_radius_over_core':4.0,'q_min':2.31,'q_max':4.10,'q_step':0.025,
 'image_shell':2,'fd_eps_over_core':1e-4,'core_model':0,'threads':16,
 'neutral_modes':6,'eig_zero_tol':1e-8,'residual_max':5e-2,
}

def _cases(quick=False):
    # Independent one-axis-at-a-time ladders around a shared baseline.
    if quick:
        return [
          ('resolution','N32',32),('resolution','N48',48),
          ('image_shell','S1',1),('image_shell','S2',2),
          ('fd_eps','H3e-4',3e-4),('fd_eps','H1e-4',1e-4),('fd_eps','H3e-5',3e-5),
        ]
    return [
      ('resolution','N32',32),('resolution','N48',48),('resolution','N64',64),('resolution','N96',96),
      ('image_shell','S1',1),('image_shell','S2',2),('image_shell','S3',3),
      ('fd_eps','H3e-4',3e-4),('fd_eps','H1e-4',1e-4),('fd_eps','H3e-5',3e-5),('fd_eps','H1e-5',1e-5),
    ]

def main():
    p=argparse.ArgumentParser(description='Blind v0.1.1 convergence campaign. No external physical target is accepted.')
    p.add_argument('--out-dir',default='audit_convergence')
    p.add_argument('--threads',type=int,default=16)
    p.add_argument('--q-min',type=float,default=2.31); p.add_argument('--q-max',type=float,default=4.10)
    p.add_argument('--q-step',type=float,default=0.025); p.add_argument('--fine-q-step',type=float,default=0.0025)
    p.add_argument('--q-cluster-tol',type=float,default=0.02)
    p.add_argument('--quick',action='store_true'); p.add_argument('--force-python',action='store_true'); p.add_argument('--force-build',action='store_true'); p.add_argument('--build-verbose',action='store_true')
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    base={**BASE,'threads':a.threads,'q_min':a.q_min,'q_max':a.q_max,'q_step':a.q_step}
    write_json(out/'independence_manifest.json',independence_manifest(base))
    case_results=[]; flat=[]; cache={}
    for idx,(axis,tag,value) in enumerate(_cases(a.quick),1):
        cfg=dict(base)
        if axis=='resolution': cfg['n_nodes']=int(value)
        elif axis=='image_shell': cfg['image_shell']=int(value)
        elif axis=='fd_eps': cfg['fd_eps_over_core']=float(value)
        print(f'\n=== [{idx}/{len(_cases(a.quick))}] {axis}:{tag} ===')
        cache_key=json.dumps(cfg,sort_keys=True,separators=(',',':'))
        if cache_key in cache:
            print('reusing identical baseline configuration from earlier ladder axis')
            result=cache[cache_key]
        else:
            result=adaptive_case(cfg,a.fine_q_step,force_python=a.force_python,force_build=(a.force_build and not cache),build_verbose=a.build_verbose,progress=True)
            cache[cache_key]=result
        case={'axis':axis,'case':tag,'value':value,'result':result}; case_results.append(case)
        write_json(out/f'case_{axis}_{tag}.json',case)
        for r in result['coarse']['rows']: flat.append({'axis':axis,'case':tag,'value':value,'stage':'coarse',**r})
        for j,fr in enumerate(result['fine_runs']):
            for r in fr['rows']: flat.append({'axis':axis,'case':tag,'value':value,'stage':f'fine{j}',**r})
    clusters=evaluate_primary_convergence(case_results,a.q_cluster_tol)
    write_csv(out/'convergence_rows.csv',flat)
    write_json(out/'candidate_clusters.json',clusters)
    summary={
      'ok':True,'dimensionless_only':True,'n_cases':len(case_results),'q_cluster_tolerance':a.q_cluster_tol,
      'n_primary_clusters':len(clusters),'n_promoted_converged_candidates':sum(bool(c['promote_converged_candidate']) for c in clusters),
      'promoted_candidates':[c for c in clusters if c['promote_converged_candidate']],
      'note':'Promotion is numerical convergence only; it is not an external physical interpretation.'
    }
    write_json(out/'audit_summary.json',summary); print('\n'+json.dumps(summary,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
