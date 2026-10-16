import argparse,json
from hopf_extension import ROOT,CASES,run_case,geometry,audit

def main():
 p=argparse.ArgumentParser(description='A064 v0.2.2 L6n1 / T(3,3) / Triple Gear Hopf-link comparison')
 p.add_argument('command',nargs='?',default='RUN',choices=['RUN','BUILD','VALIDATE','SELFTEST','REPORT','FREEZE','CERTIFY'])
 p.add_argument('--case',default='all',choices=['all',*CASES]);p.add_argument('--grid',type=int,default=24)
 p.add_argument('--duration',type=float,default=.32);p.add_argument('--frames',type=int,default=13)
 p.add_argument('--core',type=float,default=.42);p.add_argument('--force',action='store_true')
 a=p.parse_args()
 if a.command in ('FREEZE','CERTIFY'):
  print('Framework v1.0.7 not integrated: cannot certify or freeze');return 3
 if a.command=='SELFTEST':
  import pytest
  return pytest.main([str(ROOT/'tests'),'-q'])
 if a.command=='REPORT':
  from hopf_report import generate
  generate(ROOT);return 0
 if a.grid%2 or a.grid<20:p.error('grid must be even >=20')
 cases=CASES if a.case=='all' else (a.case,)
 if a.command=='VALIDATE':
  for c in cases:
   curves,pr=geometry(c);print(json.dumps(audit(curves,pr,c),indent=2))
  return 0
 results=[]
 for c in cases:
  aresult=run_case(c,a.grid,a.duration,a.frames,a.core,a.force)
  print(f'{c}: N={a.grid} E_drift={aresult["euler_diagnostics"]["max_energy_rel_drift"]:.3g} '
    f'outer crossing={aresult["outer_enstrophy"].get("tracer_cross_fraction")} '
    f'core ownership change={aresult["kinematic_nearest_core_exchange"]["changed_ownership"]} '
    f'candidate genus1={aresult["genus_one_feature"] is not None}')
  results.append(aresult)
 if a.command=='RUN':
  summary={'schema':'A064-HOPF-LANES-v1','cases':[r['case'] for r in results],
     'version':'v0.2.2','scientific_evidence':'UNQUALIFIED_3D_EULER_SIMULATION',
     'results':[{'case':r['case'],'grid':r['grid'],'outer_crossings':r['outer_enstrophy'].get('tracer_cross_fraction'),
       'nearest_core_exchange':r['kinematic_nearest_core_exchange']['changed_ownership'],
       'core_seeds_valid':r['kinematic_nearest_core_exchange']['seeds_valid'],
       'genus1_candidate':r['genus_one_feature'] is not None,
       'max_energy_drift':r['euler_diagnostics']['max_energy_rel_drift']} for r in results]}
  (ROOT/'outputs'/'RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
  from hopf_report import generate
  generate(ROOT)
 return 0
if __name__=='__main__':raise SystemExit(main())
