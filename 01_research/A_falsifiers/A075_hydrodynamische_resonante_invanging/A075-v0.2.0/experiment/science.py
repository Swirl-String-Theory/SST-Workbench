"""Adversarial A075 protocol runner; no physical capture PASS without independent gates."""
from __future__ import annotations
import json,hashlib,dataclasses,time
from pathlib import Path
import numpy as np
from .euler3d import Config,Euler3D

QUESTION=('Can freely evolving, fully coupled, finite-core vortex structures retain '
'positive local energy after scattering for many independently measured internal '
'clock cycles, with closed energy flux and convergent Euler dynamics?')

PROFILES={
 'PREVIEW':{'n':24,'n_up':32,'dt':0.06,'T':1.2,'core':0.55,'knots':['0_1','3_1','5_2','6_1']},
 'BASIC':{'n':32,'n_up':48,'dt':0.04,'T':2.0,'core':0.48,'knots':['0_1','3_1','5_2','6_1']},
 'FULL':{'n':64,'n_up':96,'dt':0.03,'T':9.0,'core':0.50,'knots':['0_1','3_1','5_2','6_1']}}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')

def comparison(case,control,donor_E):
    a=case['timeseries'];b=control['timeseries']
    if len(a)!=len(b):raise RuntimeError('Unmatched control timegrid')
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


def case_pair(cfg):
    ref_cfg=dataclasses.replace(cfg,incoming=False)
    ref=Euler3D(ref_cfg).run()
    src=Euler3D(cfg).run(center_track=ref['center_track'])
    donor=Euler3D(dataclasses.replace(cfg,receiver_on=False)).initial_velocity()[0]
    donor_E=Euler3D(dataclasses.replace(cfg,receiver_on=False)).stats(donor,[0,0,0],[0,0,0])['E_global']
    return src,ref,comparison(src,ref,donor_E)


def run_suite(root:Path,profile='PREVIEW',output_root=None):
    profile=profile.upper();p=PROFILES[profile];root=Path(root)
    out=Path(output_root) if output_root else root/'A075_Hydrodynamische_Resonante_Invanging_v0.2.0-outputs'/'science'
    out.mkdir(parents=True,exist_ok=True)
    result={'schema':'A075-SCIENCE-GATES-0.2.0','profile':profile,'question':QUESTION,
            'framework_required':'SST_Falsifier_Framework_v1.0.10',
            'execution_layer':'STANDALONE_SCIENCE_PREVIEW_NOT_FRAMEWORK_FREEZE',
            'physical_answer':'UNRESOLVED','cases':{},'gates':{},'elapsed_seconds':None}
    t0=time.monotonic()
    def config(n,dt,geom):return Config(n=n,core=p['core'],dt=dt,final_time=p['T'],geometry=geom,xyz_root=str(root/'inputs'))
    for knot in p['knots']:
        try:
            c0=config(p['n'],p['dt'],knot)
            src,control,cmp=case_pair(c0)
            save(out/f'{knot}_base_case.json',src);save(out/f'{knot}_control.json',control)
            c1=config(p['n'],p['dt']/2,knot)
            half_src,half_control,half_cmp=case_pair(c1)
            c2=config(p['n_up'],p['dt']/2,knot)
            up_src,up_control,up_cmp=case_pair(c2)
            save(out/f'{knot}_dt_half.json',half_src);save(out/f'{knot}_space_up.json',up_src)
            time_diff=abs(cmp['window_excess_final_J']-half_cmp['window_excess_final_J'])
            space_diff=abs(half_cmp['window_excess_final_J']-up_cmp['window_excess_final_J'])
            scale=max(abs(up_cmp['isolated_donor_energy_J']),1e-14)
            nums={'total_global_energy_drift':max(src['global_relative_energy_drift'],control['global_relative_energy_drift']),
                  'max_CFL':max(src['max_CFL'],control['max_CFL']),
                  'max_flux_budget_residual_over_global_E':cmp['max_normalized_flux_budget_residual'],
                  'time_refinement_observable_over_donor_E':time_diff/scale,
                  'space_refinement_observable_over_donor_E':space_diff/scale,
                  'core_points_per_radius_coarse':p['core']/(c0.box/c0.n),
                  'core_points_per_radius_fine':p['core']/(c2.box/c2.n),
                  'fixed_physical_final_time':p['T'],
                  'probe_period':src['receiver_period_s'],'probe_peak_count':src['receiver_peak_count'],
                  'clock_qualified':False,'source_exit_qualified':False,
                  'knot_embedding_source':src['geometry_provenance'][1]['source']}
            # Not a full continuum certification; only short-scale software diagnostics.
            screen=(nums['core_points_per_radius_coarse']>=3.0 and nums['total_global_energy_drift']<1e-5 and nums['max_CFL']<0.35 and
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
