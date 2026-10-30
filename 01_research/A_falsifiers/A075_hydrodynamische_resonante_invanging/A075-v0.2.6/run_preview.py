"""Standalone exploration only; never substitutes for Framework v1.1.0 FREEZE/BASIC/FULL."""
from pathlib import Path
import argparse,json
from experiment.science import run_suite,run_matrix,profile_plan
p=argparse.ArgumentParser()
p.add_argument('--profile',choices=['PREVIEW','BASIC','EXTENDED','FULL'],default='PREVIEW')
p.add_argument('--domain-study',action='store_true')
p.add_argument('--domain-study-only',action='store_true')
p.add_argument('--domains',type=str)
p.add_argument('--grid',type=int)
p.add_argument('--grid-up',type=int)
p.add_argument('--dt',type=float)
p.add_argument('--t-end',type=float)
p.add_argument('--threads',type=int,default=12)
p.add_argument('--backend',choices=['cpu-scipy-fft','cpu-numpy-reference','cpp-hybrid','arc-xpu','torch-cpu-reference'],default='cpu-scipy-fft')
p.add_argument('--backends',type=str)
p.add_argument('--require-all-backends',action='store_true')
p.add_argument('--adaptive',action='store_true',default=True)
p.add_argument('--fixed-dt',action='store_true')
p.add_argument('--cfl',type=float,dest='cfl_target',default=.15)
p.add_argument('--max-core-shift',type=float,default=.15)
p.add_argument('--max-vorticity-turn',type=float,default=.12)
p.add_argument('--dt-min',type=float,default=1.e-6)
p.add_argument('--gpu-precision',choices=['fp32','fp64'],default='fp32')
p.add_argument('--diagnostic-stride',type=int,default=2)
p.add_argument('--knots',default=None)
p.add_argument('--max-ram-gb',type=float,default=16)
p.add_argument('--allow-expensive',action='store_true')
p.add_argument('--plan',action='store_true')
p.add_argument('--output-root',type=Path,default=None)
a=p.parse_args()
opts={k:getattr(a,k) for k in ('grid','grid_up','dt','t_end','threads','backend','max_ram_gb','allow_expensive','adaptive','cfl_target','max_core_shift','max_vorticity_turn','dt_min','gpu_precision','diagnostic_stride','require_all_backends','domain_study','domain_study_only','domains')}
if a.fixed_dt:opts['adaptive']=False
if a.domain_study_only:opts['domain_study']=True
if a.domains and not a.domain_study and not a.domain_study_only:p.error('--domains requires --domain-study or --domain-study-only')
if a.domain_study and a.backends:p.error('Run domain study separately from backend matrix')
if a.knots:opts['knots']=a.knots.split(',')
if a.backends:opts['backends']=a.backends.split(',')
if a.plan:
    print(json.dumps(profile_plan(a.profile,opts),indent=2));raise SystemExit(0)
root=Path(__file__).resolve().parent
if a.domain_study_only:
    from experiment.science import _resolve
    from experiment.domain import run_domain_study
    out=a.output_root or (root/'A075_Hydrodynamische_Resonante_Invanging_v0.2.6-outputs'/'science')
    mat=run_domain_study(root,a.profile,out/'domain_study',_resolve(a.profile,opts))
    r={'physical_answer':'UNRESOLVED','cases':{},'backends':{},'domain_study':mat}
else:
    r=(run_matrix(root,a.profile,a.output_root or root/'A075_Hydrodynamische_Resonante_Invanging_v0.2.6-outputs'/'science',opts)
       if a.backends else run_suite(root,a.profile,a.output_root,overrides=opts))
print(json.dumps({'physical_answer':r['physical_answer'],
    'cases':{k:v['status'] for k,v in r.get('cases',{}).items()},
    'backends':{k:v['status'] for k,v in r.get('backends',{}).items()},
    'domain_study':r.get('domain_study',{}).get('executed',False),'execution_layer':'STANDALONE_DEVELOPMENT_ONLY'},indent=2))
