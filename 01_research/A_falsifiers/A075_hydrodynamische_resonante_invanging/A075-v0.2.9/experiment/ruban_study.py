"""Adversarial single-trefoil periodic Euler screening: not filament Ruban dynamics.

Self evolution from exactly identified initial conditions, fixed absolute T;
no donor, forced motion, or invented reconstruction of author perturbations.
Spectral magnitude change is translation-invariant but NOT topology/lifetime.
"""
from __future__ import annotations
import csv,dataclasses,hashlib,json,time
from pathlib import Path
import numpy as np
from .euler3d import Config,Euler3D,stable_dt
from .ruban import verify_geometry,resolution_gate,PRIMARY
from .heartbeat import phase,advance

def _to_np(solver,x):
    return x.detach().cpu().numpy() if hasattr(x,'detach') else np.asarray(x)

def _spectral_signature(s,uh):
    # Translation does not change |omega_hat|; rotations/deformations generally do.
    om=s.curl_hat(uh)
    a=np.abs(_to_np(s,om))
    return a

def evolve_one(cfg,*,sample_stride=2):
    if cfg.initial_condition not in ('ruban_isolated','legacy_t23_isolated') or cfg.incoming:
        raise ValueError('single source-free Ruban/legacy trefoil only')
    if cfg.backend in ('arc-xpu','torch-cpu-reference'):
        from .euler_torch import TorchEuler3D
        s=TorchEuler3D(cfg)
    else:s=Euler3D(cfg)
    uh,prov=s.initial_velocity(); E0=s.global_energy_hat(uh)
    spec0=_spectral_signature(s,uh)
    denom=max(float(np.linalg.norm(spec0.ravel())),1e-30)
    t=0.;n=0;total_reject=0;history=[]
    def record():
        E=s.global_energy_hat(uh)
        amp=_spectral_signature(s,uh)
        deviation=float(np.linalg.norm((amp-spec0).ravel())/denom)
        if hasattr(uh,'detach'):
            import torch
            enst=float((.5*s.dx**3*torch.sum(torch.abs(s.curl_hat(uh))**2)/s.c.n**3).item())
        else:
            enst=float(.5*s.dx**3/s.c.n**3*np.sum(np.abs(s.curl_hat(uh))**2))
        history.append({'step':n,'t':float(t),'E_global':E,
            'global_relative_energy_drift':(E-E0)/max(abs(E0),1e-30),
            'translation_invariant_vorticity_spectrum_difference':deviation,
            'enstrophy_J_proxy':enst})
    record()
    tiny=max(cfg.final_time*1e-12,1e-13)
    while cfg.final_time-t>tiny:
        if n>=cfg.max_steps:raise RuntimeError('MAX_STEPS_EXCEEDED')
        umax,omax=s.adapt_metrics(uh)
        dt=stable_dt(cfg,s.dx,umax,omax,cfg.final_time-t) if cfg.adaptive else min(cfg.dt,cfg.final_time-t)
        if not np.isfinite(dt) or dt<=0:raise RuntimeError('INVALID_DT')
        retries=0
        while True:
            new=s.rk4(uh,dt)
            up,op=s.adapt_metrics(new)
            if (not cfg.adaptive or
                max(umax,up)*dt/s.dx<=cfg.cfl_target*(1+1e-12) and
                max(umax,up)*dt/cfg.core<=cfg.max_core_shift*(1+1e-12) and
                max(omax,op)*dt<=cfg.max_vorticity_turn*(1+1e-12)):break
            retries+=1;dt/=2
            if retries>12 or dt<cfg.dt_min:raise RuntimeError('ADAPTIVE_STEP_REJECT_LIMIT')
        uh=new;t=min(cfg.final_time,t+dt);n+=1;total_reject+=retries
        advance(n,t,cfg.final_time,dt,retries)
        if n%sample_stride==0 or cfg.final_time-t<=tiny:record()
    if abs(t-cfg.final_time)>max(1e-10,1e-10*cfg.final_time):
        raise AssertionError('physical final time not reached')
    return {'schema':'A075-RUBAN-SOURCE_FREE-EULER-1','initial_condition':cfg.initial_condition,
      'config':dataclasses.asdict(cfg),'provenance':prov,'steps':n,'rejected_attempts':total_reject,
      'initial_energy':E0,'global_energy_relative_drift_max':max(abs(r['global_relative_energy_drift']) for r in history),
      'spectrum_difference_final':history[-1]['translation_invariant_vorticity_spectrum_difference'],
      'history':history,'physical_final_time_reached':True,'topology_conserved_certified':False,
      'ruban_filament_model_reproduced':False,'physical_stability':'UNRESOLVED',
      'remarks':'Periodic image effects and Gaussian finite-core differ from Ruban delta; no geometrical tracking.'}

def _save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')

def _csv(path,rows):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def run_ruban_study(root,output_dir,options,*,light=False):
    root=Path(root);out=Path(output_dir)
    seed=root/'inputs/ruban_t23'/PRIMARY
    verified=verify_geometry(seed)
    if not verified['geometric_fidelity_pass']:raise RuntimeError('Ruban geometry not qualified')
    core=float(options.get('ruban_core') or options.get('core') or .5)
    grid=int(options.get('n') or options.get('grid') or 80)
    up=int(options.get('n_up') or options.get('grid_up') or max(grid+8,grid*3//2//8*8))
    T=float(options.get('T') or options.get('t_end') or .05)
    dt=float(options.get('dt') or .01)
    if not(0<core and 0<T and 0<dt and grid>=16 and grid%2==0):raise ValueError('ruban options invalid')
    # Baseline comparison uses identical R0=1, circulation, Euler sigma,
    # physical box and absolute time; B0 is the only intended geometry change.
    box=float(options.get('ruban_box') or 10.)
    if box<=2.5:raise ValueError('box too small for isolated T23 extent')
    if grid>256 or up>256 or (up<=grid and bool(options.get('ruban_refinement'))):
        raise ValueError('bad grids')
    base=dict(n=grid,box=box,core=core,gamma_receiver=2*np.pi,dt=dt,final_time=T,threads=int(options.get('threads') or 1),
        incoming=False,receiver_on=True,ruban_seed_path=str(seed),xyz_root=str(root/'inputs'),
        backend=str(options.get('backend') or 'cpu-scipy-fft'),adaptive=bool(options.get('adaptive',True)),
        gpu_precision=str(options.get('gpu_precision') or 'fp32'),
        cfl_target=float(options.get('cfl_target') or .15),
        max_core_shift=float(options.get('max_core_shift') or .15),
        max_vorticity_turn=float(options.get('max_vorticity_turn') or .12),
        dt_min=float(options.get('dt_min') or 1e-6),max_steps=100000)
    cases={};levels=[('base',grid,dt)]
    if options.get('ruban_refinement',False) and not light:
        levels.extend([('dt_half',grid,dt/2),('grid_up',up,dt/2)])
    total=2*len(levels);nphase=0
    for label,kind in [('ruban','ruban_isolated'),('analytic_032','legacy_t23_isolated')]:
        for level,n,dtn in levels:
            nphase+=1
            phase('ruban_source_free_euler',backend=base['backend'],knot=label,grid=n,
                physical_end_time=T,phase_index=nphase,phase_total=total,
                message='Unforced single T23; shape diagnostics are non-topological')
            cfg=Config(**{**base,'n':n,'dt':dtn,'initial_condition':kind,
                'geometry':'ruban_t23_B0_0p154' if label=='ruban' else 'analytic_t23_B0_0p32'})
            data=evolve_one(cfg,sample_stride=max(1,int(options.get('diagnostic_stride') or 2)))
            data['resolution']=resolution_gate(box,n,core, .154 if label=='ruban' else .32)
            name=f'{label}_{level}'
            _save(out/f'{name}.json',data);_csv(out/f'{name}_history.csv',data['history'])
            cases[name]={k:data[k] for k in ('steps','initial_energy','global_energy_relative_drift_max',
                    'spectrum_difference_final','physical_final_time_reached','physical_stability')}
    fidelity={'schema':'A075-RUBAN-SEED-FIDELITY-STABILITY-1',
        'framework':'1.1.0','input_sha256':verified['seed_sha256'],
        'geometry':verified,'levels':cases,
        'ruban_resolution':resolution_gate(box,grid,core,.154),
        'analytic_032_resolution':resolution_gate(box,grid,core,.32),
        'refinement_executed':len(levels)>1,
        'stability_certified':False,'topology_certified':False,
        'source_free':True,'periodic_images_present':True,
        'ruban_delta_is_not_euler_sigma':True,
        'paper_perturbation_known':False,'physical_answer':'UNRESOLVED'}
    _save(out/'RUBAN_STABILITY_SUMMARY.json',fidelity)
    return fidelity
