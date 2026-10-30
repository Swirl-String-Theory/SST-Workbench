"""Dual-provider resolution campaign; sequential to control memory and preserve provenance."""
from __future__ import annotations
import argparse,datetime,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from .adapters import check_source,hash_file

def main():
    p=argparse.ArgumentParser(description='Shared source-locked A075+A077 Euler trajectories, sequential grid ladder')
    p.add_argument('--a075-root',required=True);p.add_argument('--a077-root',required=True)
    p.add_argument('--grids',type=int,nargs='+',default=[48,64,80,96])
    p.add_argument('--time',type=float,default=.02);p.add_argument('--dt',type=float,default=.001)
    p.add_argument('--markers',type=int,default=12);p.add_argument('--trials',type=int,default=1)
    p.add_argument('--perturb',type=float,default=0.)
    p.add_argument('--a077-cases',nargs='+',choices=['no_toroidal','toroidal_plus','toroidal_minus'],default=['toroidal_plus'])
    p.add_argument('--a075-geometry',choices=['ruban','coupled_ring_trefoil'],default='ruban')
    p.add_argument('--a075-core',type=float,default=.42)
    p.add_argument('--seed',type=int,default=77075);p.add_argument('--output-parent',default='..')
    p.add_argument('--allow-memory',action='store_true');p.add_argument('--memory-limit-gib',type=float,default=8.)
    a=p.parse_args()
    if len(set(a.grids))!=len(a.grids):raise ValueError('duplicate grid level')
    if len(a.grids)<3:raise ValueError('spatial study requires >= 3 grid levels')
    for n in a.grids:
        if n<16 or n%2:raise ValueError('even grid dimensions >=16 required')
    sources={'a075':Path(a.a075_root).resolve(),'a077':Path(a.a077_root).resolve()}
    source_sha={k:check_source(k,v) for k,v in sources.items()}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    parent=Path(a.output_parent).resolve()
    campaign=parent/('EulerTrajectoryResolutionGenerator_v0.2.0-outputs')/('DUAL_'+stamp)
    campaign.mkdir(parents=True,exist_ok=False)
    executions=[]
    for provider in ('a075','a077'):
      cases=[a.a075_geometry] if provider=='a075' else a.a077_cases
      for case in cases:
       for n in a.grids:
        cmd=[sys.executable,'-m','resolver.run','--provider',provider,'--source',str(sources[provider]),
             '--grid',str(n),'--time',str(a.time),'--dt',str(a.dt),
             '--markers',str(a.markers),'--trials',str(a.trials),'--perturb',str(a.perturb),
             '--seed',str(a.seed),'--output-parent',str(campaign),'--memory-limit-gib',str(a.memory_limit_gib)]
        cmd+=['--geometry',case,'--core',str(a.a075_core)] if provider=='a075' else ['--case',case]
        if a.allow_memory:cmd.append('--allow-memory')
        if n>96:cmd.append('--allow-large')
        print(f'[CAMPAIGN] provider={provider} case={case} n={n}',flush=True)
        r=subprocess.run(cmd,check=False)
        executions.append({'provider':provider,'case':case,'n':n,'exit_code':r.returncode})
        if r.returncode!=0:
            (campaign/'CAMPAIGN_PARTIAL.json').write_text(json.dumps({'runs':executions,'source_hashes':source_sha,'status':'INCOMPLETE'},indent=2)+'\n')
            raise SystemExit(r.returncode)
    summary={'schema':'SST-EULER-DUAL-CAMPAIGN-1','status':'NUMERICAL_DIAGNOSTICS_ONLY',
        'source_hashes':source_sha,'grid_levels':a.grids,'fixed_final_time':a.time,'fixed_dt':a.dt,
        'spatial_axis_only':'n; equal time step and same final time, identical initial physical parameters',
        'run_ledger':executions,'independence_warning':'multiple grids are refinements, not independent replications',
        'unresolved':'3D finite-core material vorticity and any electron/spin claims'}
    (campaign/'CAMPAIGN_MANIFEST.json').write_text(json.dumps(summary,indent=2)+'\n')
    archive=parent/('EulerTrajectoryResolutionGenerator_v0.2.0_DUAL_'+stamp+'_outputs.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(campaign.rglob('*')):
            if f.is_file() and (f.name.endswith('.zip') or f.name.endswith('.sha256') or f.name=='CAMPAIGN_MANIFEST.json'):
                z.write(f,f.relative_to(campaign))
    h=hash_file(archive)
    (Path(str(archive)+'.sha256')).write_text(h+'  '+archive.name+'\n')
    print(f'[PASS] DUAL campaign={campaign}\nARCHIVE={archive}\nSHA256={h}',flush=True)
if __name__=='__main__':main()
