"""Adversarial A075 protocol runner; no physical capture PASS without independent gates."""
from __future__ import annotations
import json,hashlib,dataclasses,time,os,csv
from pathlib import Path
import numpy as np
from .euler3d import Config,Euler3D,run_paired

QUESTION=('Can freely evolving, fully coupled, finite-core vortex structures retain '
'positive local energy after scattering for many independently measured internal '
'clock cycles, with closed energy flux and convergent Euler dynamics?')

# All numerical profiles hold the *physical* box and Gaussian core width fixed.
# The PREVIEW is intentionally a fast, underresolved software smoke test.
# BASIC and FULL resolve the initial Gaussian sigma better; neither certifies
# dynamical core convergence, flux closure, donor exit or a clock.
PROFILES={
 'PREVIEW':{'n':48,'n_up':64,'dt':0.02,'T':0.6,'core':0.50,'knots':['0_1','3_1','5_2','6_1']},
 'BASIC':  {'n':80,'n_up':112,'dt':0.015,'T':1.2,'core':0.50,'knots':['0_1','3_1','5_2','6_1']},
 'EXTENDED':{'n':96,'n_up':128,'dt':0.012,'T':3.0,'core':0.50,'knots':['0_1','3_1','5_2','6_1']},
 'FULL':   {'n':96,'n_up':128,'dt':0.010,'T':9.0,'core':0.50,'knots':['0_1','3_1','5_2','6_1']}}

# Conservative control on the one-dimensional Courant factor u_max dt/dx.
MAX_CFL_SCREEN=0.20
MIN_SIGMA_CELLS_FOR_SCREEN=4.0

# Only the CPU FFT backend is qualified for this release.  The shared Framework
# SYCL worker supports a Biot-Savart kernel, not the A075 full 3D Euler solver.
SUPPORTED_BACKENDS = {'cpu-scipy-fft', 'cpu-numpy-reference', 'cpp-hybrid', 'arc-xpu', 'torch-cpu-reference'}
ALLOWED_GRIDS = tuple(range(16, 257, 8))

def _resolve(name, overrides=None):
    """Frozen policy ranges plus per-run declared choices; never fit output data."""
    if name.upper() not in PROFILES:raise ValueError('unknown profile')
    p=dict(PROFILES[name.upper()]); opts=dict(overrides or {})
    p['n']=int(opts.get('grid') or p['n'])
    p['n_up']=int(opts.get('grid_up') or (max(p['n']+16, int(np.ceil(1.4*p['n']/8))*8) if opts.get('grid') else p['n_up']))
    p['dt']=float(opts.get('dt') or p['dt'])
    p['T']=float(opts.get('t_end') or p['T'])
    p['threads']=int(opts.get('threads') or 1)
    p['backend']=str(opts.get('backend') or 'cpu-scipy-fft')
    p['adaptive']=bool(opts.get('adaptive',True))
    p['cfl_target']=float(opts.get('cfl_target') or 0.15)
    p['max_core_shift']=float(opts.get('max_core_shift') or 0.15)
    p['max_vorticity_turn']=float(opts.get('max_vorticity_turn') or 0.12)
    p['dt_min']=float(opts.get('dt_min') or 1.e-6)
    p['gpu_precision']=str(opts.get('gpu_precision') or 'fp32')
    p['backends']=list(opts.get('backends') or [])
    p['domain_study']=bool(opts.get('domain_study',False))
    p['domain_study_only']=bool(opts.get('domain_study_only',False))
    p['domains']=opts.get('domains')
    p['boundary']=str(opts.get('boundary','periodic'))
    if p['boundary'] != 'periodic':raise RuntimeError('FREE_SPACE_NOT_IMPLEMENTED; no physical open boundary is simulated')
    p['diagnostic_stride']=int(opts.get('diagnostic_stride') or 2)
    if p['gpu_precision'] not in ('fp32','fp64'):raise ValueError('gpu_precision must be fp32 or fp64')
    if any(z<=0 for z in (p['cfl_target'],p['max_core_shift'],p['max_vorticity_turn'],p['dt_min'])):raise ValueError('positive time safety factors required')
    if p['dt_min'] >= p['dt']:raise ValueError('dt-min must be smaller than dt-max')
    if p['diagnostic_stride']<1:raise ValueError('diagnostic_stride >= 1')
    if opts.get('knots'):
        p['knots']=list(opts['knots'])
    if p['n'] not in ALLOWED_GRIDS or p['n_up'] not in ALLOWED_GRIDS or p['n_up'] <= p['n']:
        raise ValueError('grid and grid-up must be even multiples of 8, 16..256, and grid-up > grid')
    if p['domain_study'] and p['backends']:raise ValueError('Run domain study separately from backend matrix')
    if p['T']<=0 or p['dt']<=0 or p['threads']<1 or p['threads']>64:
        raise ValueError('time and threads must be positive, threads <= 64')
    if len(set(p['knots'])) != len(p['knots']) or not set(p['knots'])<= {'0_1','3_1','5_2','6_1'} or not p['knots']:
        raise ValueError('knots must be nonempty unique 0_1,3_1,5_2,6_1')
    if p['backend'] not in SUPPORTED_BACKENDS:
        raise RuntimeError('BLOCKED_UNVALIDATED_BACKEND: must be Python, C++ hybrid, or real PyTorch XPU')
    # Adaptive steps end at exact T by clipping final step; no integer T/dt restriction.
    p['effective_fft_workers']=p['threads'] if p['backend'] in ('cpu-scipy-fft','cpp-hybrid') else (1 if p['backend']=='cpu-numpy-reference' else 0)
    p['allow_expensive']=bool(opts.get('allow_expensive',False))
    p['max_ram_gb']=float(opts.get('max_ram_gb') or 16)
    return p

def run_budget(p):
    # Conservative peak RSS screening estimate; not an allocation guarantee.
    mem_gib=(p['n_up']**3 * 3 * 16 * 30)/2**30
    work_units=(round(2*p['T']/p['dt']))*len(p['knots'])*p['n_up']**3
    work_units*=max(1,len(p.get('backends',[])))
    reasons=[]
    if mem_gib>p['max_ram_gb']:reasons.append('estimated peak memory exceeds --max-ram-gb')
    if work_units>1_500_000_000 and not p['allow_expensive']:
        reasons.append('large CPU run; pass --allow-expensive to acknowledge compute budget')
    return {'estimated_peak_GiB_upper_proxy':round(mem_gib,3),
            'relative_work_units':int(work_units), 'budget_approved':not reasons,'block_reasons':reasons}



def profile_plan(name: str, overrides=None) -> dict:
    p=_resolve(name,overrides)
    box=Config().box
    n,nup=p['n'],p['n_up']
    # A lower-bound proxy: one complex128 vector field (many such arrays are
    # needed by FFT and RK4, so actual peak memory is substantially larger).
    if p['domain_study']:
        from .domain import parse_domains,domain_budget
        boxes=parse_domains(p['domains'],p['n'],box)
        dom_budget=domain_budget(boxes,p)
    else:boxes=[];dom_budget=None
    return {'profile':name.upper(),'box':box,'domain_boxes':boxes,'domain_budget':dom_budget,'gaussian_sigma':p['core'],
            'backend':p['backend'],'threads':p['threads'],'threads_requested':p['threads'], 'effective_fft_workers':p['effective_fft_workers'],'knots':p['knots'],
            'budget':run_budget(p),
            'coarse_grid':n,'refined_grid':nup,
            'dx_coarse':box/n,'dx_refined':box/nup,
            'cells_per_sigma_coarse':p['core']*n/box,
            'cells_per_sigma_refined':p['core']*nup/box,
            'dt_max':p['dt'],'dt_half_max':p['dt']/2,'adaptive':p['adaptive'],'CFL_target':p['cfl_target'],
            'max_core_sigma_shift':p['max_core_shift'],'max_vorticity_turn':p['max_vorticity_turn'],
            'dt_min':p['dt_min'],'final_time':p['T'],
            'steps_base':round(p['T']/p['dt']),
            'steps_half':round(2*p['T']/p['dt']),
            'max_CFL_screen':MAX_CFL_SCREEN,
            'one_complex_vector_field_MiB_refined':(nup**3*3*16)/2**20,
            'disclaimer':'REAL peak memory is many times this field; 3 simulations per knot, each with donor/control; FULL is expensive.'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')

def comparison(case,control,donor_E):
    a=case['timeseries'];b=control['timeseries']
    if len(a)!=len(b) or any(abs(x['t']-y['t'])>1e-10 for x,y in zip(a,b)):
        raise RuntimeError('Unmatched control timegrid')
    excess=np.array([x['E_window']-y['E_window'] for x,y in zip(a,b)])
    t=np.array([x['t'] for x in a])
    # No physical hold measurement unless independently qualified *source exit*.
    tail=t>=t[-1]*.75
    flux_err=max(case['max_window_budget_residual_over_E0'],control['max_window_budget_residual_over_E0'])
    total0=case['timeseries'][0]['E_global']-control['timeseries'][0]['E_global']
    return {'source_total_initial_excess_J':float(total0),
            'isolated_donor_energy_J':float(donor_E),
            'window_excess_initial_J':float(excess[0]),
            'window_excess_final_J':float(excess[-1]),
            'tail_min_excess_J':float(np.min(excess[tail])),
            'tail_min_excess_over_donor_E':float(np.min(excess[tail])/donor_E),
            'max_normalized_flux_budget_residual':float(flux_err),
            'control_center_reused_exactly':True,
            'source_departure_confirmed':False,
            'late_clock_cycles':None,
            'retention_qualified':False,
            'status':'UNRESOLVED_SOURCE_EXIT_CLOCK_AND_CONVERGENCE'}


def write_steps(path,steps):
    if not steps:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(steps[0]),extrasaction='ignore')
        w.writeheader();w.writerows(steps)

def case_pair(cfg):
    if cfg.adaptive:
        src,ref,steps=run_paired(cfg)
    else:
        ref_cfg=dataclasses.replace(cfg,incoming=False)
        ref=Euler3D(ref_cfg).run()
        src=Euler3D(cfg).run(center_track=ref['center_track'])
        steps=[]
    donor=Euler3D(dataclasses.replace(cfg,receiver_on=False,backend='cpu-scipy-fft')).initial_velocity()[0]
    donor_E=Euler3D(dataclasses.replace(cfg,receiver_on=False,backend='cpu-scipy-fft')).stats(donor,[0,0,0],[0,0,0])['E_global']
    return src,ref,comparison(src,ref,donor_E),steps


def run_suite(root:Path,profile='PREVIEW',output_root=None,overrides=None):
    profile=profile.upper();p=_resolve(profile,overrides);root=Path(root)
    budget=run_budget(p)
    if p['backend'] in ('cpp-hybrid','arc-xpu'):
        short='cpp' if p['backend']=='cpp-hybrid' else 'gpu'
        pr=probe_backend(short,root)
        if not pr['available']:
            raise RuntimeError('BACKEND_UNAVAILABLE_'+short+': '+pr.get('reason','unknown'))
    if not budget['budget_approved']:
        raise RuntimeError('A075 pre-run budget refused: '+', '.join(budget['block_reasons']))
    out=Path(output_root) if output_root else root/'A075_Hydrodynamische_Resonante_Invanging_v0.2.6-outputs'/'science'
    out.mkdir(parents=True,exist_ok=True)
    source_hashes={name:sha(root/name) for name in (
        'experiment/euler3d.py','experiment/euler_torch.py','experiment/science.py',
        'experiment/pipeline.py','native/cpp/native.cpp','tools/build_native.py')}
    save(out/'SOLVER_SOURCE_HASHES.json',{'sha256':source_hashes,
        'source_root':str(root),'framework':'1.1.0'})
    result={'schema':'A075-SCIENCE-GATES-0.2.3','profile':profile,'resolved_options':p,'budget':budget,'question':QUESTION,
            'framework_required':'SST_Falsifier_Framework_v1.1.0',
            'execution_layer':'STANDALONE_OR_FRAMEWORK_ADAPTER_DEPENDING_ON_ENTRYPOINT',
            'physical_answer':'UNRESOLVED','cases':{},'gates':{},'elapsed_seconds':None}
    t0=time.monotonic()
    def config(n,dt,geom):return Config(n=n,core=p['core'],dt=dt,final_time=p['T'],geometry=geom,xyz_root=str(root/'inputs'),threads=p['threads'],backend=p['backend'],adaptive=p['adaptive'],cfl_target=p['cfl_target'],max_core_shift=p['max_core_shift'],max_vorticity_turn=p['max_vorticity_turn'],dt_min=p['dt_min'],steps_per_diagnostic=p['diagnostic_stride'],gpu_precision=p['gpu_precision'])
    for knot_idx,knot in enumerate(p['knots']):
        try:
            from .heartbeat import phase
            phase('suite_base',backend=p['backend'],knot=knot,grid=p['n'],physical_end_time=p['T'],phase_index=knot_idx*3+1,phase_total=len(p['knots'])*3)
            c0=config(p['n'],p['dt'],knot)
            src,control,cmp,steps0=case_pair(c0)
            write_steps(out/f'{knot}_base_energy_matrix.csv',steps0)
            save(out/f'{knot}_base_case.json',src);save(out/f'{knot}_control.json',control)
            phase('suite_time_refinement',backend=p['backend'],knot=knot,grid=p['n'],physical_end_time=p['T'],phase_index=knot_idx*3+2,phase_total=len(p['knots'])*3)
            c1=config(p['n'],p['dt']/2,knot)
            half_src,half_control,half_cmp,steps1=case_pair(c1)
            write_steps(out/f'{knot}_dt_half_energy_matrix.csv',steps1)
            phase('suite_space_refinement',backend=p['backend'],knot=knot,grid=p['n_up'],physical_end_time=p['T'],phase_index=knot_idx*3+3,phase_total=len(p['knots'])*3)
            c2=config(p['n_up'],p['dt']/2,knot)
            up_src,up_control,up_cmp,steps2=case_pair(c2)
            write_steps(out/f'{knot}_space_up_energy_matrix.csv',steps2)
            save(out/f'{knot}_dt_half.json',half_src);save(out/f'{knot}_space_up.json',up_src)
            median_base=float(np.median([z['dt'] for z in steps0])) if steps0 else None
            median_half=float(np.median([z['dt'] for z in steps1])) if steps1 else None
            effective_time_gate=bool(median_base and median_half and median_half<=.75*median_base and len(steps1)>len(steps0))
            time_diff=abs(cmp['window_excess_final_J']-half_cmp['window_excess_final_J'])
            space_diff=abs(half_cmp['window_excess_final_J']-up_cmp['window_excess_final_J'])
            scale=max(abs(up_cmp['isolated_donor_energy_J']),1e-14)
            nums={'total_global_energy_drift':max(src['global_relative_energy_drift'],control['global_relative_energy_drift']),
                  'max_CFL':max(z['max_CFL'] for z in (src,control,half_src,half_control,up_src,up_control)),
                  'max_flux_budget_residual_over_global_E':max(z['max_window_budget_residual_over_E0'] for z in (src,control,half_src,half_control,up_src,up_control)),
                  'time_refinement_observable_over_donor_E':time_diff/scale,
                  'space_refinement_observable_over_donor_E':space_diff/scale,
                  'core_points_per_radius_coarse':p['core']/(c0.box/c0.n),
                  'core_points_per_sigma_coarse':p['core']/(c0.box/c0.n),
                  'core_points_per_radius_fine':p['core']/(c2.box/c2.n),
                  'core_points_per_sigma_fine':p['core']/(c2.box/c2.n),
                  'fixed_physical_final_time':p['T'],
                  'temporal_refinement_effective':effective_time_gate,'dt_median_base':median_base,'dt_median_half':median_half,
                  'dt_steps_base':len(steps0),'dt_steps_half':len(steps1),'dt_steps_space':len(steps2),
                  'dt_base_min_used':min((z['dt'] for z in steps0),default=None),
                  'dt_base_max_used':max((z['dt'] for z in steps0),default=None),
                  'energy_numerical_loss_sum_J':sum(z['numerical_loss_donor_J'] for z in steps0),
                  'energy_numerical_gain_sum_J':sum(z['numerical_gain_donor_J'] for z in steps0),
                  'probe_period':src['receiver_period_s'],'probe_peak_count':src['receiver_peak_count'],
                  'clock_qualified':False,'source_exit_qualified':False,
                  'knot_embedding_source':src['geometry_provenance'][1]['source']}
            # Not a full continuum certification; only short-scale software diagnostics.
            screen=(nums['temporal_refinement_effective'] and nums['core_points_per_sigma_coarse']>=MIN_SIGMA_CELLS_FOR_SCREEN and nums['total_global_energy_drift']<1e-5 and nums['max_CFL']<MAX_CFL_SCREEN and
                    nums['max_flux_budget_residual_over_global_E']<5e-3 and
                    nums['time_refinement_observable_over_donor_E']<2e-2 and
                    nums['space_refinement_observable_over_donor_E']<0.12)
            result['cases'][knot]={'status':'NUMERICAL_SCREEN_PASS_ONLY' if screen else 'DIAGNOSTIC_UNDERRESOLVED_OR_FAILED',
                                   'diagnostics':nums,'capture':cmp,
                                   'full_euler_certified':False,'late_retention_certified':False}
        except FileNotFoundError as exc:
            result['cases'][knot]={'status':'BLOCKED_REQUIRED_KNOT_GEOMETRY_MISSING','reason':str(exc)}
        except Exception as exc:
            result['cases'][knot]={'status':'FAIL','reason':type(exc).__name__+': '+str(exc)}
    if p['domain_study']:
        from .domain import run_domain_study
        result['domain_study']=run_domain_study(root,profile,out/'domain_study',p)
        result['gates']={} if not result.get('gates') else result['gates']
        # An isolated-domain/sensitivity gate has not yet earned a full free-space qualification.
        result['domain_qualification']='PERIODIC_BOX_SENSITIVITY_ONLY_NO_FREE_SPACE_CLAIM'
    result['elapsed_seconds']=time.monotonic()-t0
    result['gates']={
        'G0':{'status':'NOT_RUN','reason':'Authentic framework FREEZE not executed by standalone science runner'},
        'G1':{'status':'PASS' if all(sha(root/'source_evidence'/f'{k}_README.md')==v for k,v in {'A021':'b615595589551dafbcabddc223e554abeb6ab5a02a064fa96522af73d533e3e9','A032':'e78411ee0a3a0cd770bd8293e117f44b1908bd419877b5163d5df21b71b9da0e'}.items()) else 'FAIL','reason':'Byte-exact A021 and A032 methodological provenance'},
        'G2':{'status':'PASS' if all(x['status']=='NUMERICAL_SCREEN_PASS_ONLY' for x in result['cases'].values()) else 'UNRESOLVED',
              'reason':'Short-time Galerkin conservation and fixed-time refinement ONLY; geometry cases may remain blocked'},
        'G3':{'status':'UNRESOLVED','reason':'No qualified donor exit, clock cycles and post-exit energy-flux hold'},
        'G4':{'status':'NOT_RUN','reason':'No preregistered independent late holdout'},
        'G5':{'status':'NOT_RUN','reason':'No native C++/pybind11 parity'},
        'G6':{'status':'NOT_RUN','reason':'No GPU/SYCL parity'},
        'G7':{'status':'UNRESOLVED','reason':'5_2/6_1 must be from user-supplied provenance-clean XYZ'},
        'G8':{'status':'UNRESOLVED','reason':'3D Fourier-Galerkin Euler is executed but continuum convergence, box independence, core fidelity and local material-volume flux are not certified'},
        'G9':{'status':'WITHHELD','reason':'No physical promotion or private reveal'}}
    save(out/'A075_GATES.json',result)
    return result


BACKEND_NAMES={'py':'cpu-scipy-fft','cpp':'cpp-hybrid','gpu':'arc-xpu','numpy':'cpu-numpy-reference','torchcpu':'torch-cpu-reference'}

def probe_backend(name,root):
    if name=='py':return {'available':True,'actual':'cpu-scipy-fft','precision':'float64'}
    if name=='numpy':return {'available':True,'actual':'cpu-numpy-reference','precision':'float64'}
    if name=='cpp':
        try:
            from .native import load_cpp
            module=load_cpp()
            return {'available':True,'actual':'cpp-hybrid','precision':'float64','kernel_path':module.__file__,
                    'openmp_compiled':bool(module.openmp_enabled()),'openmp_max_threads':int(module.openmp_threads())}
        except Exception as e:return {'available':False,'reason':str(e)}
    if name in ('gpu','torchcpu'):
        try:
            import torch
            if name=='gpu' and (not hasattr(torch,'xpu') or not torch.xpu.is_available()):
                return {'available':False,'reason':'No PyTorch XPU device; never count Framework Biot-Savart SYCL probe as full Euler GPU'}
            if name=='gpu':
                try:
                    a=torch.ones((4,4,4),device='xpu',dtype=torch.float32)
                    test=torch.fft.fftn(a,dim=(0,1,2))
                    if str(test.device.type)!='xpu':
                        raise RuntimeError('torch FFT did not run on the XPU device')
                    _=float(test[0,0,0].abs().item())
                except Exception as e:
                    return {'available':False,'reason':'XPU_FFT_RUNTIME_FAIL: '+str(e)}
            return {'available':True,'actual':BACKEND_NAMES[name],'precision':'fp32-default' if name=='gpu' else 'float64',
                    'torch_version':torch.__version__,'device':str(torch.xpu.get_device_name()) if name=='gpu' else 'cpu'}
        except Exception as e:return {'available':False,'reason':str(e)}
    return {'available':False,'reason':'unknown backend'}

def run_matrix(root,profile,output_root,overrides):
    """Backend-by-backend common protocol; no PASS for a backend that did not run."""
    requested=list(overrides.get('backends') or ['py'])
    bad=set(requested)-set(BACKEND_NAMES)
    if bad:raise ValueError('Unknown backends '+str(sorted(bad)))
    out=Path(output_root);out.mkdir(parents=True,exist_ok=True)
    combined_budget=run_budget(_resolve(profile,overrides))
    if not combined_budget['budget_approved']:
        raise RuntimeError('A075 backend matrix budget refused: '+', '.join(combined_budget['block_reasons']))
    probes={b:probe_backend(b,root) for b in requested}
    matrix={'schema':'A075-BACKEND-MATRIX-1','requested':requested,'probes':probes,
            'status':'DEVELOPMENT_ONLY','physical_answer':'UNRESOLVED','backends':{},
            'parity':{},'gate_policy':'backend software parity does not override missing physical gates'}
    save(out/'BACKEND_PREFLIGHT.json',matrix)
    if overrides.get('require_all_backends') and any(not x['available'] for x in probes.values()):
        matrix['status']='BLOCKED_REQUIRED_BACKEND_UNAVAILABLE'
        save(out/'BACKEND_MATRIX.json',matrix)
        raise RuntimeError('Required backend unavailable: '+str({k:v for k,v in probes.items() if not v['available']}))
    for b in requested:
        if not probes[b]['available']:
            matrix['backends'][b]={'execution':'NOT_EXECUTED','status':'BLOCKED','reason':probes[b]['reason']}
            continue
        local={k:v for k,v in overrides.items() if k not in ('backends','require_all_backends')}
        local['backend']=BACKEND_NAMES[b]
        try:
            res=run_suite(root,profile,out/'backends'/b,overrides=local)
            completed=sum(x['status'] in ('NUMERICAL_SCREEN_PASS_ONLY','DIAGNOSTIC_UNDERRESOLVED_OR_FAILED') for x in res['cases'].values())
            failures={k:v for k,v in res['cases'].items() if v['status']=='FAIL'}
            execution='FAILED' if failures else ('EXECUTED' if completed else 'NOT_EXECUTED')
            matrix['backends'][b]={'execution':execution,'status':'DEVELOPMENT_ONLY' if completed and not failures else 'FAILED_OR_BLOCKED',
              'cases':res['cases'],'actual_backend':BACKEND_NAMES[b],
              'precision':'fp32' if b=='gpu' and local.get('gpu_precision','fp32')=='fp32' else 'fp64'}
        except Exception as exc:
            matrix['backends'][b]={'execution':'FAILED','status':'FAIL','reason':type(exc).__name__+': '+str(exc)}
    ref=matrix['backends'].get('py')
    for name,entry in matrix['backends'].items():
        if name=='py' or entry.get('execution')!='EXECUTED' or not ref or ref.get('execution')!='EXECUTED':continue
        comparable={}
        for knot,d in entry['cases'].items():
            base=ref['cases'].get(knot,{})
            if 'diagnostics' not in d or 'diagnostics' not in base:continue
            # Compare same observable, same initial geometry and physical final time.
            v=d['capture']['window_excess_final_J'];z=base['capture']['window_excess_final_J']
            relative=abs(v-z)/max(abs(base['capture']['isolated_donor_energy_J']),1e-12)
            comparable[knot]={'absolute_difference_J':abs(v-z),'normalized_difference':relative,
                              'numerical_parity_screen_only':relative < (5e-4 if name=='gpu' else 1e-8)}
        matrix['parity'][name]=comparable
    matrix['status']='COMPLETED_PARTIAL' if any(x['execution']!='EXECUTED' for x in matrix['backends'].values()) else 'COMPLETED_SOFTWARE_MATRIX_ONLY'
    save(out/'BACKEND_MATRIX.json',matrix)
    if overrides.get('require_all_backends') and any(x['execution']!='EXECUTED' for x in matrix['backends'].values()):
        raise RuntimeError('REQUIRED_BACKEND_EXECUTION_FAILED: see BACKEND_MATRIX.json')
    return matrix
