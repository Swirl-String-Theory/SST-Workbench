"""A075 v0.2.6 real scientific execution adapter for Framework v1.1.0.

Every accepted record corresponds to an actual (donor, no-donor) time evolution
of the SAME finite-core periodic Euler initial condition. Devices that cannot
run are recorded as unavailable, never replaced by a CPU calculation.

Science contract: execution agreement != spatial/temporal convergence, topology
preservation, independence from periodic images, source departure, or capture.
"""
from __future__ import annotations
from dataclasses import replace, asdict
from pathlib import Path
import hashlib, json, os
import numpy as np
from experiment.euler3d import Config, Euler3D
from experiment.science import _resolve, case_pair

BACKENDS={
 'py':('cpu-scipy-fft','python','experiment/euler3d.py','float64'),
 'cpp':('cpp-hybrid','pybind11','native/cpp/native.cpp','float64'),
 'gpu':('arc-xpu','torch_xpu','experiment/euler_torch.py','float32'),
}

def _sha(path:Path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def _json_bytes(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

def _options(mode):
    choices=json.loads(os.getenv('A075_RUNTIME_OPTIONS_JSON','{}'))
    if choices.get('domain_study_only'):
        raise RuntimeError('Domain-only study has no standard comparison trajectory; run its diagnostic separately')
    if choices.get('boundary','periodic')!='periodic':
        raise RuntimeError('True free-space Euler backend not implemented')
    profile=mode if mode in ('BASIC','EXTENDED','FULL') else 'PREVIEW'
    p=_resolve(profile,choices)
    # The scientific backend crosscheck runs one source/control pair, not an
    # artificially cheaper unrelated kernel. Missing 5_2/6_1 files are not
    # substituted; the canonical analytic 0_1 is the common execution seed.
    return profile,p

def _canonical(root,p):
    ruban=bool(p.get('ruban_study'))
    c=Config(n=p['n'],dt=p['dt'],final_time=p['T'],core=(p.get('ruban_core') or p['core']),
        box=float(p.get('ruban_box') or 10.),
        gamma_receiver=float(2*np.pi) if ruban else 1.,
        initial_condition='ruban_isolated' if ruban else 'legacy_coupled',
        incoming=not ruban,
        ruban_seed_path=str(root/'inputs/ruban_t23/RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz') if ruban else '',
        geometry='3_1' if ruban else '0_1',
        xyz_root=str(root/'inputs'),threads=p['threads'],backend='cpu-scipy-fft',
        adaptive=p['adaptive'],cfl_target=p['cfl_target'],
        max_core_shift=p['max_core_shift'],max_vorticity_turn=p['max_vorticity_turn'],
        dt_min=p['dt_min'],steps_per_diagnostic=p['diagnostic_stride'])
    # Hash *actual* initial Fourier velocity field, not just descriptive tags.
    initial,_=Euler3D(c).initial_velocity()
    h=hashlib.sha256()
    h.update(np.ascontiguousarray(initial,dtype=np.complex128).tobytes())
    h.update(_json_bytes({k:getattr(c,k) for k in (
        'n','box','core','rho','gamma_receiver','gamma_donor','dt','final_time',
        'geometry','initial_condition','ruban_seed_path','incoming','adaptive','cfl_target','max_core_shift','max_vorticity_turn',
        'dt_min','steps_per_diagnostic','window_halfwidth','window_edge','seed')}))
    return c,h.hexdigest()

def _real_euler_pair(root,output_dir,c_base,kind,devices,input_digest):
    backend,actual,source_rel,precision=BACKENDS[kind]
    dev=devices.get(kind,{})
    if not dev.get('available'):
        return {'executed':False,'reason':dev.get('reason','backend unavailable')}
    if kind=='gpu':
        if not (dev.get('provider')=='intel' and str(dev.get('device_type','')).startswith('xpu')):
            return {'executed':False,'reason':'A075 requires real Intel XPU; no CUDA/CPU substitution'}
        # Arc A770 has no native IEEE binary64. Explicit screening only.
        import torch
        if not torch.xpu.is_available():
            return {'executed':False,'reason':'Runtime XPU vanished after preflight'}
    if kind=='cpp':
        from experiment.native import load_cpp
        native=load_cpp()
        compiled=Path(native.__file__).resolve()
        if _sha(compiled) not in {e.get('sha256') for e in dev.get('modules',[])}:
            return {'executed':False,'reason':'Native module fingerprint differs from framework preflight'}
    else:
        compiled=None
    cfg=replace(c_base,backend=backend,gpu_precision='fp32' if kind=='gpu' else 'fp64')
    if cfg.initial_condition=='ruban_isolated':
        from experiment.ruban_study import evolve_one
        record=evolve_one(cfg,sample_stride=2)
        source={'global_relative_energy_drift':record['global_energy_relative_drift_max'],
                'max_CFL':None}
        control={'global_relative_energy_drift':0.}
        comparison={'source_free':True,'spectral_difference':record['spectrum_difference_final'],
                    'global_energy_relative_drift_max':record['global_energy_relative_drift_max']}
        steps=[None]*record['steps']
        metrics=[float(record['initial_energy']),
                 float(record['spectrum_difference_final']),
                 float(record['global_energy_relative_drift_max']),
                 float(record['history'][-1]['enstrophy_J_proxy'])]
        execution_note='Single source-free Ruban T23 3D periodic Euler evolution; not donor capture'
    else:
        source,control,comparison,steps=case_pair(cfg)
        metrics=[float(comparison['window_excess_final_J']),
                 float(comparison['tail_min_excess_over_donor_E']),
                 float(source['global_relative_energy_drift']),
                 float(control['global_relative_energy_drift'])]
        execution_note='real 3D Fourier--Galerkin Euler source/control pair'
    if not all(np.isfinite(metrics)):
        raise ValueError('Euler observable contains nonfinite elements')
    evidence={
      'schema':'A075-SCIENCE-BACKEND-EXECUTION-1',
      'executed':True,'actual_backend':actual,'input_sha256':input_digest,
      'precision':precision,'physical_final_time':float(cfg.final_time),
      'observables_units':['J','dimensionless','dimensionless','vorticity_squared_integrated'] if cfg.initial_condition=='ruban_isolated' else ['J','dimensionless','dimensionless','dimensionless'],
      'observable':metrics,
      'source_execution':execution_note,
      'gaussian_core_sigma':float(cfg.core),'grid_n':int(cfg.n),
      'time_step_max':float(cfg.dt),'adaptive':bool(cfg.adaptive),
      'knot':'RUBAN_T23_B0_0p154' if cfg.initial_condition=='ruban_isolated' else '0_1','periodic_domain':True,
      'source_departure_qualified':False,'retention_qualified':False,
      'measurement':comparison,
      'source_result':{'global_relative_energy_drift':source['global_relative_energy_drift'],
                       'max_CFL':source.get('max_CFL')},
      'control_result':{'global_relative_energy_drift':control['global_relative_energy_drift']},
      'step_count':len(steps),
      'device_type':'xpu' if kind=='gpu' else 'cpu',
      'compiled_binary_sha256':_sha(compiled) if compiled else None,
      'source_code_sha256':_sha(root/source_rel),
      'qualification':'DIAGNOSTIC_EXECUTION_ONLY',
    }
    output_dir.mkdir(parents=True,exist_ok=True)
    path=output_dir/(kind+'.json')
    path.write_text(json.dumps(evidence,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')
    return {
      'executed':True,'actual_backend':actual,'input_sha256':input_digest,
      'source_path':source_rel,'source_sha256':_sha(root/source_rel),
      'evidence_path':'backend_science/'+path.name,
      'evidence_sha256':_sha(path),'observable':metrics,
    }

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    """Mandatory Framework v1.1.0 hook; no fabricated success/fallback."""
    root=Path(root).resolve();out=Path(output_dir).resolve()
    try:
        profile,p=_options(mode)
        config,identity=_canonical(root,p)
    except Exception as exc:
        return {k:{'executed':False,'reason':f'Preflight: {type(exc).__name__}: {exc}'} for k in BACKENDS}
    from experiment.heartbeat import phase
    records={}
    for index,kind in enumerate(BACKENDS):
        phase('science_backend_pair',backend=kind,knot='Ruban_T23' if config.initial_condition=='ruban_isolated' else '0_1',grid=config.n,physical_end_time=config.final_time,phase_index=index+1,phase_total=len(BACKENDS),
             message='Mandatory framework backend science: donor + control RK4 integration')
        try:
            records[kind]=_real_euler_pair(root,out,config,kind,devices,identity)
        except Exception as exc:
            records[kind]={'executed':False,'reason':f'{type(exc).__name__}: {exc}'}
    # Write an explicit diagnostic summary; canonical framework checks hashes
    # and 2-of-3 eligibility, not this self-reported development status.
    diag={'schema':'A075-BACKEND-DIAGNOSTIC-1','profile':profile,'input_sha256':identity,
          'resolved_grid':config.n,'final_time':config.final_time,
          'records':{k:{'executed':bool(v.get('executed')), 'reason':v.get('reason')}
                     for k,v in records.items()},'physics':'UNRESOLVED'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'A075_BACKEND_DIAGNOSTICS.json').write_text(json.dumps(diag,indent=2)+'\n',encoding='utf8')
    return records
