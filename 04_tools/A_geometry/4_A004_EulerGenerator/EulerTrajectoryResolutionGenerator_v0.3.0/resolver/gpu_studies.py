"""V2 orthogonal convergence/sensitivity campaign controller.

Scientific boundary: these are numerical screens of *specified* periodic Galerkin
Euler fields and passive tracers. They are NOT material-core stability tests.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, math, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
from .adapters import check_source, hash_file
from .gpu_core import estimate_vram_gib as estimate_gib

VERSION='v0.3.0'
SCHEMA='SST-EULER-XPU-INDEPENDENT-LADDERS-3'
SMALL_RADIUS={'a075':77/500,'a077':.19}
BASE_BOX={'a075':10.,'a077':8.}

def even_up(value:int|float)->int:
    n=int(math.ceil(value));return max(16,n+(n%2))

def target_resolution(provider:str, nominal_cells:float=4, effective:bool=False)->int:
    if provider not in SMALL_RADIUS or nominal_cells<=0:raise ValueError('invalid provider/required cells')
    factor=1.5 if effective else 1.0 # 2/3 de-aliasing effective wavenumber cap
    return even_up(BASE_BOX[provider]*nominal_cells*factor/SMALL_RADIUS[provider])

def case_for(provider:str, case_a077:str='toroidal_plus'):
    return 'ruban' if provider=='a075' else case_a077

def plan_runs(provider:str, profile:str, studies:list[str], target_cells:float, effective:bool,
              tf:float, dt:float, markers:int, seed:int, case_a077:str='toroidal_plus')->list[dict]:
    base=32 if profile=='smoke' else (96 if profile=='pilot' else target_resolution(provider,target_cells,effective))
    n_levels=(16,24,32) if profile=='smoke' else ((48,64,96) if profile=='pilot' else tuple(sorted({even_up(base*f) for f in (1.,1.2,1.4)})))
    case=case_for(provider,case_a077)
    run=[]
    def add(study,tag,n=base,step_dt=dt,core_factor=1.,box_factor=1.,pert=0.,trial_seed=seed):
        b=BASE_BOX[provider]*box_factor
        entry={'provider':provider,'case':case,'study':study,'tag':tag,'n':n,
               't_final':tf,'dt_request':step_dt,'box_length':b,'core_factor':core_factor,
               'perturb':pert,'seed':trial_seed,'markers':markers,'memory_estimate_gib':round(estimate_gib(n),2),
               'host_initialization_estimate_gib':round(1.5+384*n**3/2**30,2),
               'geometric_radius_over_dx':round(SMALL_RADIUS[provider]*n/b,5),
               'spectral_effective_radius_cells':round(SMALL_RADIUS[provider]*n/b*2/3,5)}
        run.append(entry)
    if 'spatial' in studies:
        for n in n_levels:add('spatial',f'n{n}',n=n)
    if 'temporal' in studies:
        for f in (1.,.5,.25):add('temporal',f'dt_x{f}',step_dt=dt*f)
    if 'core' in studies:
        for f in (.8,1.,1.2):add('core',f'core_x{f}',core_factor=f)
    if 'box' in studies:
        for f in (.75,1.,1.25):
            n=even_up(base*f) # keep actual grid dx approximately invariant
            add('box',f'box_x{f}',n=n,box_factor=f)
    if 'perturb' in studies:
        add('perturb','baseline',pert=0.)
        for amp in (.005,.02):
            for j in range(3):add('perturb',f'eps{amp}_seed{j}',pert=amp,trial_seed=seed+j+1)
    return run

def _read_result(directory:Path)->tuple[dict,dict]:
    m=json.loads((directory/'RUN_MANIFEST.json').read_text(encoding='utf-8'))
    h=json.loads((directory/'OUTPUT_MANIFEST.json').read_text(encoding='utf-8'))
    if not h['files']:raise ValueError('EMPTY_OUTPUT_MANIFEST')
    for f,digest in h['files'].items():
        path=directory/f
        if not path.is_file() or hash_file(path)!=digest:raise ValueError('OUTPUT_HASH_MISMATCH '+str(path))
    path=directory/'trial_0000'/'trajectory.npz'
    with np.load(path,allow_pickle=False) as dat:
        times=dat['times_solver'].copy();x=dat['positions_unwrapped_solver'].copy()
        v=dat['velocity_solver'].copy()
    if times.ndim!=1 or np.any(np.diff(times)<=0) or x.ndim!=3 or x.shape[0]!=len(times) or x.shape[-1]!=3 or v.shape!=x.shape or not np.isfinite(x).all() or not np.isfinite(v).all():
        raise ValueError('INVALID_TRAJECTORY_DATA')
    return m,{'time':times,'x':x,'v':v}

def _aligned_error(reference:dict,another:dict,scale:float)->dict:
    ref_t=reference['time'];other_t=another['time']
    if abs(ref_t[-1]-other_t[-1])>1e-12:raise ValueError('DIFFERENT_FINAL_TIME')
    if reference['x'].shape[1]!=another['x'].shape[1]:raise ValueError('DIFFERENT_MARKER_COUNT')
    # compare at common physical sampling times, independent of dt, not frame index
    x=np.empty_like(reference['x']);y=another['x']
    for j in range(y.shape[1]):
        for k in range(3):x[:,j,k]=np.interp(ref_t,other_t,y[:,j,k])
    dx=x-reference['x']
    return {'relative_end_position_to_smallest_radius':float(np.linalg.norm(dx[-1])/max(scale*math.sqrt(len(dx[-1])),1e-14)),
            'rms_trajectory_position_to_smallest_radius':float(np.sqrt(np.mean(np.sum(dx*dx,axis=-1)))/scale),
            'max_trajectory_position_to_smallest_radius':float(np.max(np.linalg.norm(dx,axis=-1))/scale)}

def evaluate(records:list[dict],run_dirs:dict[str,Path],target_cells:float,effective:bool)->dict:
    out={'schema':SCHEMA,'summary':{},'comparisons':{},'status':'DEVELOPMENT_NUMERICAL_ONLY',
         'physics_status':'UNRESOLVED_MATERIAL_VORTEX_STABILITY_AND_SPIN',
         'caveats':['A smooth regularized Euler field does not identify a material vortex-tube boundary.',
                    'Core-width variation changes initial fields; it is not a convergence limit by itself.',
                    'Passive tracers do not prove core materiality, knot isotopy, or spinor holonomy.',
                    'Per-run energy/helicity drift is necessary but insufficient.']}
    groups={}
    for r in records:
        if r['tag'] not in run_dirs:continue
        m,data=_read_result(run_dirs[r['tag']])
        h=m['trials_summary'][0]
        sig={'max_energy_drift':h['energy_drift_max_rel'],'max_divergence':h['max_divergence_Linf'],
             'max_cfl':h['max_cfl'],'run_n':r['n'],'run_dt':m['dt'],
             'core_radius_per_dx':r['geometric_radius_over_dx'],
             'effective_radius_cells':r['spectral_effective_radius_cells']}
        out['summary'][r['tag']]=sig
        groups.setdefault(r['study'],[]).append((r,data))
    for group,arr in groups.items():
        if len(arr)<2:
            out['comparisons'][group]={'status':'INCOMPLETE'};continue
        # spatial/temporal: pair refinement relative to best resolved output;
        # core/box/perturb: relative to baseline of matching physical setup
        if group=='spatial':arr.sort(key=lambda x:x[0]['n']);ref=arr[-1]
        elif group=='temporal':arr.sort(key=lambda x:x[0]['dt_request'],reverse=True);ref=arr[-1]
        else:
            refs=[x for x in arr if x[0]['tag'] in ('core_x1.0','box_x1.0','baseline')]
            if not refs:out['comparisons'][group]={'status':'MISSING_REFERENCE'};continue
            ref=refs[0]
        scale=SMALL_RADIUS[ref[0]['provider']]
        comparison={p[0]['tag']:_aligned_error(ref[1],p[1],scale) for p in arr if p[0]['tag']!=ref[0]['tag']}
        res={'status':'MEASURED_NUMERICAL_DIAGNOSTIC_ONLY','reference':ref[0]['tag'],'metrics':comparison}
        if group in ('spatial','temporal') and len(arr)>=3:
            # Consecutive differences rather than false "reference error" claims.
            e01=_aligned_error(arr[1][1],arr[0][1],scale)['relative_end_position_to_smallest_radius']
            e12=_aligned_error(arr[2][1],arr[1][1],scale)['relative_end_position_to_smallest_radius']
            ratio=e12/max(e01,1e-30)
            res['asymptotic_screen']={'coarse_middle_difference_over_radius':e01,
               'middle_fine_difference_over_radius':e12,'refinement_ratio':ratio,
               'screen_tolerance_over_radius':.02,'contraction_limit':.75,
               'meets_exploratory_error_screen':(None if max(e01,e12)<1e-12 else bool(e12<.02 and ratio<.75)),
               'precision_floor_detected':bool(max(e01,e12)<1e-12),
               'status':'PRECISION_FLOOR_ORDER_UNMEASURABLE' if max(e01,e12)<1e-12 else 'NUMERICAL_REFINEMENT_SCREEN_ONLY'}
        if group in ('box','core','perturb'):
            res['parameter_sensitivity']={
              'max_endpoint_deviation_over_radius':max(z['relative_end_position_to_smallest_radius'] for z in comparison.values()),
              'meaning':{'box':'periodic image/domain sensitivity',
                         'core':'regularization/initial-profile sensitivity (not a convergence study)',
                         'perturb':'full-field initial perturbation response (not restoring-force proof)'}[group],
              'status':'MEASURED_ONLY_NO_PHYSICAL_PASS'}
        if group=='spatial':
            nominal=min(r['geometric_radius_over_dx'] for r,_ in arr)
            finest=ref[0]['spectral_effective_radius_cells'] if effective else ref[0]['geometric_radius_over_dx']
            res['resolution_screen']={'target_cells':target_cells,'target_is_spectral_effective':effective,
                 'finest_level_meets_nominal_cell_screen':finest>=target_cells,'all_levels_meet_nominal_cell_screen':nominal>=target_cells,
                 'status':'SCREEN_ONLY_NOT_CONTINUUM_CERTIFICATION'}
            # Not meaningful to report Richardson order for non-geometric ratios without fitting.
        out['comparisons'][group]=res
    return out

def make_archive(out:Path)->tuple[str,str]:
    archive=out.parent/(out.name+'_outputs.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for f in sorted(out.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(out))
    sha=hash_file(archive)
    (Path(str(archive)+'.sha256')).write_text(sha+'  '+archive.name+'\n',encoding='utf-8')
    return str(archive),sha

def main(argv=None):
    p=argparse.ArgumentParser(description='Orthogonal Euler trajectory studies; PLAN is default, --execute required for runs')
    p.add_argument('--a075-root');p.add_argument('--a077-root')
    p.add_argument('--providers',nargs='+',choices=['a075','a077'],default=['a075','a077'])
    p.add_argument('--studies',nargs='+',choices=['spatial','temporal','core','box','perturb','all'],default=['all'])
    p.add_argument('--profile',choices=['smoke','pilot','qualification'],default='pilot')
    p.add_argument('--effective-resolution',action='store_true',help='require 4 retained spectral resolution cells, rather than nominal grid cells')
    p.add_argument('--target-cells',type=float,default=4.)
    p.add_argument('--time',type=float,default=.02);p.add_argument('--dt',type=float,default=.001)
    p.add_argument('--markers',type=int,default=16);p.add_argument('--seed',type=int,default=77075)
    p.add_argument('--a077-case',choices=['no_toroidal','toroidal_plus','toroidal_minus'],default='toroidal_plus')
    p.add_argument('--output-parent',default='..')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--memory-limit-gib',type=float,default=12.)
    p.add_argument('--device',choices=['xpu','cpu-test'],default='xpu')
    p.add_argument('--ram-limit-gib',type=float,default=16.0)
    p.add_argument('--cpu-test',action='store_true')
    p.add_argument('--precision',choices=['fp32','dd32-tracer'],default='dd32-tracer')
    p.add_argument('--skip-unaffordable',action='store_true',help='skip rather than fake running over-memory jobs')
    p.add_argument('--allow-memory',action='store_true')
    a=p.parse_args(argv)
    if a.allow_memory:p.error('--allow-memory forbidden for GPU; VRAM gate cannot be bypassed')
    if a.device=='cpu-test' and not a.cpu_test:p.error('CPU test mode requires --cpu-test')
    if a.time<=0 or a.dt<=0 or a.markers<1 or a.target_cells<=0 or a.memory_limit_gib<=0:
        p.error('positive time/dt/markers/cells/memory required')
    studies=['spatial','temporal','core','box','perturb'] if 'all' in a.studies else list(dict.fromkeys(a.studies))
    paths={'a075':a.a075_root,'a077':a.a077_root}
    sources={}
    plans={}
    for provider in a.providers:
        if not paths[provider]:p.error(f'--{provider}-root required')
        root=Path(paths[provider]).resolve()
        sources[provider]={'root':str(root),'sha256':check_source(provider,root)}
        plans[provider]=plan_runs(provider,a.profile,studies,a.target_cells,a.effective_resolution,a.time,a.dt,a.markers,a.seed,a.a077_case)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    base=Path(a.output_parent).resolve();out=base/f'EulerTrajectoryResolutionGenerator_{VERSION}-outputs'/(f'STUDIES_{stamp}')
    out.mkdir(parents=True,exist_ok=False)
    plan={'schema':SCHEMA,'version':VERSION,'sources':sources,'profile':a.profile,'time_end':a.time,
          'temporal_step_base':a.dt,'target_cells':a.target_cells,'spectral_effective_target':a.effective_resolution,
          'studies':studies,'runs':plans,'executed':False,'scientific_claim':'NONE; GPU FP32 field and optional compensated DD32 tracer positions only',
          'device_requested':a.device,'precision_requested':a.precision,
          'limitations':['Memory estimates are indicative; stop on RAM/CFL limit',
                         'Spatial refinement compares discretizations of the same modeled initial conditions',
                         'Core width and box length change model parameters, so are sensitivity axes, not proof of a continuum limit',
                         'Velocity interpolation is trilinear and separately needs refinement',
                         'No material vortex boundary/transport tangency or independent solver validation']}
    (out/'RUN_PLAN.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    all_runs=[r for group in plans.values() for r in group]
    print('Planned',len(all_runs),'runs, peak estimated',round(max(x['memory_estimate_gib'] for x in all_runs),2),'GiB')
    for provider in a.providers:
        print(provider,'N_target=',target_resolution(provider,a.target_cells,a.effective_resolution),'L=',BASE_BOX[provider],
              'r_minor=',SMALL_RADIUS[provider])
    if not a.execute:
        print('PLAN_ONLY',out);return 0
    if not a.skip_unaffordable and any((x['memory_estimate_gib']>a.memory_limit_gib or x['host_initialization_estimate_gib']>a.ram_limit_gib) for x in all_runs):
        (out/'PRECHECK_FAILURE.json').write_text(json.dumps({'reason':'MEMORY_LIMIT_EXCEEDED','limit_gib':a.memory_limit_gib},indent=2)+'\n')
        print('REFUSED: estimated memory exceeds threshold; use --skip-unaffordable or higher limit after checking physical RAM')
        return 2
    ledger=[];evaluations={}
    for provider in a.providers:
        run_dirs={};records=plans[provider]
        for r in records:
            if (r['memory_estimate_gib']>a.memory_limit_gib or r['host_initialization_estimate_gib']>a.ram_limit_gib):
                ledger.append({**r,'execution':'SKIPPED_MEMORY_PREFLIGHT'});continue
            subroot=out/provider/r['study']/r['tag'];subroot.mkdir(parents=True,exist_ok=False)
            cmd=[sys.executable,'-m','resolver.gpu_run','--provider',provider,'--source',sources[provider]['root'],
                 '--grid',str(r['n']),'--time',str(a.time),'--dt',str(r['dt_request']),
                 '--markers',str(a.markers),'--seed',str(r['seed']),'--perturb',str(r['perturb']),
                 '--box-length',str(r['box_length']),'--core-factor',str(r['core_factor']),
                 '--output-parent',str(subroot),'--vram-limit-gib',str(a.memory_limit_gib),'--precision',a.precision,'--device',a.device,'--ram-limit-gib',str(a.ram_limit_gib),'--execute']
            cmd+=['--geometry','ruban'] if provider=='a075' else ['--case',r['case']]
            if a.device=='cpu-test':
                if not a.cpu_test:raise RuntimeError('CPU_TEST_EXPLICIT_PERMISSION_REQUIRED')
                cmd.append('--cpu-test')
            # No bypass for GPU VRAM guard; a memory estimate above the limit is always refused.
            print(f"[RUN] {provider} {r['study']} {r['tag']} N={r['n']}",flush=True)
            with (subroot/'RUN_STDOUT.log').open('w',encoding='utf-8') as logfile:
                proc=subprocess.run(cmd,stdout=logfile,stderr=subprocess.STDOUT,check=False)
            candidates=list(subroot.glob(f'EulerTrajectoryResolutionGenerator_{VERSION}-outputs/*/RUN_MANIFEST.json'))
            if proc.returncode==0 and len(candidates)==1:run_dirs[r['tag']]=candidates[0].parent
            entry={**r,'execution':'COMPLETED' if proc.returncode==0 and len(candidates)==1 else 'FAILED',
                   'return_code':proc.returncode,'result_manifest':str(candidates[0].relative_to(out)) if len(candidates)==1 else None}
            ledger.append(entry)
            (out/'RUN_LEDGER.json').write_text(json.dumps(ledger,indent=2,allow_nan=False)+'\n')
            if entry['execution']=='FAILED':
                (out/'CAMPAIGN_STATUS.json').write_text(json.dumps({'status':'PARTIAL_FAIL_CLOSED','failure':entry},indent=2)+'\n')
                return proc.returncode or 3
        try:evaluations[provider]=evaluate(records,run_dirs,a.target_cells,a.effective_resolution)
        except Exception as exc:
            (out/'EVALUATION_ERROR.txt').write_text(repr(exc)+'\n')
            raise
    (out/'EVALUATION.json').write_text(json.dumps(evaluations,indent=2,allow_nan=False)+'\n')
    status='PARTIAL_INCOMPLETE' if any(l['execution']!='COMPLETED' for l in ledger) else 'COMPLETE_NUMERICAL_SCREEN_ONLY'
    (out/'CAMPAIGN_STATUS.json').write_text(json.dumps({'status':status,'n_completed':sum(l['execution']=='COMPLETED' for l in ledger),
           'n_planned':len(ledger),'physical_core_stability':'UNRESOLVED','spin':'UNRESOLVED','GPU_execution_qualified':a.device=='xpu'},indent=2)+'\n')
    z,h=make_archive(out)
    print('CAMPAIGN_STATUS:',status,'OUTPUT:',out,'ARCHIVE:',z,'SHA256:',h)
    return 0 if status=='COMPLETE_NUMERICAL_SCREEN_ONLY' else 3

if __name__=='__main__':raise SystemExit(main())
