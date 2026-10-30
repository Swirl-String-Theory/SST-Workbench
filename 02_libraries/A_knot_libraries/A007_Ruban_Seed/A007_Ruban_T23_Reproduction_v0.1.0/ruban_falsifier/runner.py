"""Run an auditable Ruban pilot and record statuses without stability promotion."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, platform, sys, time, zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .model import RubanModel,torus_knot,ring
from .metrics import length,shape_drift,segment_stats,nonlocal_clearance,is_regular

VERSION='v0.1.0'
PREFIX='Ruban_T23_Reproduction'
ROOT=Path(__file__).resolve().parents[1]

def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def configure(mode):
    return {
      'SMOKE':dict(n=64,dt=0.001,final_time=0.025,snapshot_interval=0.005,b0=[0.154],perturb=1e-5,include_convergence=False),
      'BASIC':dict(n=128,dt=0.002,final_time=0.5,snapshot_interval=0.05,b0=[0.14,0.154,0.17],perturb=1e-4,include_convergence=False),
      'FULL':dict(n=256,dt=0.002,final_time=320.,snapshot_interval=1.,b0=[0.14,0.148,0.152,0.154,0.156,0.16,0.168],perturb=1e-4,include_convergence=False),
      'CERTIFY':dict(n=256,dt=0.002,final_time=320.,snapshot_interval=1.,b0=[0.152,0.154,0.156],perturb=1e-4,include_convergence=True),
    }[mode].copy()

def ring_test(model,n=128):
    x=ring(n)
    u=model.velocity(x)
    transverse=np.linalg.norm(u[:,:2],axis=1).max()
    z=float(np.mean(u[:,2])); spread=float(np.std(u[:,2]))
    return {'n':n,'mean_uz':z,'max_transverse_velocity':float(transverse),
      'std_uz':spread,'symmetry_pass':transverse<2e-9 and spread<2e-9,
      'note':'ring field symmetry only, not an external calibrated velocity benchmark'}

def simulate(n,b0,dt,final_time,snapshot_interval,perturb,Lambda,delta,seed,
             max_drift=0.25,max_energy_rel=1e-3,max_ds_ratio=10.,save_path=None):
    if dt<=0 or final_time<=0 or snapshot_interval<dt: raise ValueError('dt/time invalid')
    steps=math.ceil(final_time/dt)
    sample_every=max(1,round(snapshot_interval/dt))
    model=RubanModel(Lambda,delta)
    x0=torus_knot(n,b0,perturbation=perturb,seed=seed)
    ref=torus_knot(n,b0)
    e0=model.energy(x0)
    l0=length(x0)
    x=x0.copy();rows=[];t=0.;stop_reason='TIME_LIMIT'
    tstart=time.perf_counter()
    def sample(step):
        e=model.energy(x);l=length(x)
        drift=shape_drift(x,ref,quick=True)
        seg=segment_stats(x)
        return dict(step=step,time=t,energy=e,energy_rel=abs(e-e0)/max(abs(e0),1e-12),
                length=l,length_rel=l/l0-1.,shape_rms=drift,
                z_mean=float(x[:,2].mean()),
                min_nonlocal_vertex_distance=nonlocal_clearance(x,skip=max(4,n//40)),
                **seg)
    rows.append(sample(0))
    for step in range(1,steps+1):
        h=min(dt,final_time-t)
        if h<=0:break
        try:x=model.rk4(x,h)
        except FloatingPointError:
            stop_reason='NONFINITE_FIELD';break
        t+=h
        if step%sample_every==0 or step==steps:
            if not is_regular(x):stop_reason='DEGENERATE_GEOMETRY';break
            d=sample(step)
            rows.append(d)
            # Energy gate prevents falsely interpreting numerical explosion as physics.
            if d['energy_rel']>max_energy_rel:stop_reason='ENERGY_DRIFT_STOP';break
            if d['ds_ratio']>max_ds_ratio:stop_reason='SAMPLING_QUALITY_STOP';break
            if d['shape_rms']>max_drift:stop_reason='OPERATIONAL_DEFORMATION_STOP';break
    if save_path:
        save_path=Path(save_path); save_path.parent.mkdir(parents=True,exist_ok=True)
        with save_path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return {'n':n,'b0':b0,'lambda':Lambda,'delta':delta,
      'lambda_tilde':model.lambda_tilde,'dt':dt,'target_final_time':final_time,
      'attained_time':t,'steps_taken':step,'elapsed_s':time.perf_counter()-tstart,
      'initial_energy':e0,'initial_length':l0,'last':rows[-1],'stop_reason':stop_reason,
      'net_z_travel':float(rows[-1]['z_mean']-rows[0]['z_mean']),
      'operational_survival_only': stop_reason=='TIME_LIMIT',
      'paper_reproduced':'UNRESOLVED','euler_stability':'NOT_TESTED'}

def write_report(out,run,results):
    message='''# Ruban T(2,3) - reproducible falsifier report

## Claim and scope
Attempt to reproduce Ruban (2018), arXiv:1801.04822, equation (9), Fig. 3:
T(2,3), B0=0.154, delta/R0=0.05, Lambda=1.4+0.5 ln(200),
R0=1, Gamma=2*pi, lifetime >300 and distance >1200 R0 for a selected run.

This release is a numerical filament-model reproduction attempt, NOT a solution
of full three-dimensional incompressible Euler nor a test of internal core twist.

## Numerical method
Fourier pseudospectral X_beta/X_betabeta; full O(N^2) Rosenhead-Moore
quadrature including self-contribution at finite delta; Ruban local induction
lambda_tilde/2 * (X_beta cross X_betabeta)/|X_beta|^3;
fixed-step classical RK4; deterministic long-wave perturbations; no artificial
viscosity, smoothing, knot forcing or remeshing. The paper's exact random seed,
finite deformation criterion and integrator implementation are unavailable.

## Limitations and falsifier gates
- G0 provenance/geometry: requires correct seeded T(2,3), parameter data, source SHA.
- G1 solver smoke: ring symmetry, sign, initial convergence, finite field.
- G2 energy + sampling: error must remain below specified bounds.
- G3 duration: T >= 300 dimensionless, with no stop and documented travel.
- G4 parametric window: local B0 scan should show lifetime sensitivity.
- G5 spatial and temporal convergence: compare N=128/256/512 and dt, dt/2
  at identical physical final times, plus a regularization delta sensitivity.
- G6 Ruban published benchmark: adequate paper-matched phase convention,
  numerical method and sustained quasi-stability; require independent audit.
- G7 full Euler/finite core/internal twist: OUT OF SCOPE; NEVER infer from G6.

The operational RMS threshold and sampling-quality stop are new explicit
benchmarks; they are NOT Ruban's unreported termination rule.

## Execution summary
'''
    message+=f"Mode: {run['mode']} | timestamp UTC: {run['timestamp_utc']} | configuration SHA256: {run['configuration_sha256']}\n\n"
    message+='| B0 | N | dt | attained t | stop reason | relative energy drift | shape RMS | status |\n|---:|---:|---:|---:|---|---:|---:|---|\n'
    for r in results:
        d=r['last'];message+=f"| {r['b0']:.4f} | {r['n']} | {r['dt']:.6g} | {r['attained_time']:.5f} | {r['stop_reason']} | {d['energy_rel']:.3e} | {d['shape_rms']:.3e} | UNRESOLVED |\n"
    message+='\n## Result interpretation\nA run that survives a short smoke interval is **NOT** evidence for Ruban\'s >300 lifetime. A long operational survivor is **NOT** certified until convergence and invariants pass.\n'
    (out/'FALSIFIER_REPORT.md').write_text(message,encoding='utf-8')

def archive_outputs(out,zip_path):
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=f'{out.name}/{p.relative_to(out).as_posix()}')
    zip_path.with_suffix(zip_path.suffix+'.sha256').write_text(hashfile(zip_path)+'  '+zip_path.name+'\n',encoding='utf-8')

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',nargs='?',choices=['SMOKE','BASIC','FULL','CERTIFY'],default='SMOKE')
    parser.add_argument('--n',type=int)
    parser.add_argument('--dt',type=float)
    parser.add_argument('--final-time',type=float)
    parser.add_argument('--snapshot-interval',type=float)
    parser.add_argument('--b0',type=float,nargs='+')
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args(argv)
    cfg=configure(args.mode)
    for key in ('n','dt','final_time','snapshot_interval','b0'):
        v=getattr(args,key)
        if v is not None:cfg[key]=v
    Lambda=1.4+0.5*math.log(200)
    cfg.update(mode=args.mode,Lambda=Lambda,delta=0.05,seed=20261030)
    cfg_bytes=json.dumps(cfg,sort_keys=True).encode()
    safe_stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output_root=args.output_root or ROOT/(PREFIX+'_'+VERSION+'-outputs')
    output_root=output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        output_root=output_root.parent/(output_root.name+'_'+safe_stamp)
    output_root.mkdir(parents=True,exist_ok=True)
    dump(output_root/'config.json',cfg)
    run={'mode':args.mode,'timestamp_utc':safe_stamp,'configuration_sha256':hashlib.sha256(cfg_bytes).hexdigest(),
       'code_version':VERSION,'python':platform.python_version(),'numpy':np.__version__,
       'code_sha256':{p.name:hashfile(p) for p in sorted((ROOT/'ruban_falsifier').glob('*.py'))},
       'platform':platform.platform(),'input_sha256':{f.name:hashfile(f) for f in sorted((ROOT/'inputs').iterdir()) if f.is_file()},
       'paper':'https://arxiv.org/abs/1801.04822',
       'qualification':'DEVELOPMENT_ONLY; finite-core Euler not tested'}
    dump(output_root/'source_manifest.json',run)
    model=RubanModel(Lambda,0.05)
    ring_diag=ring_test(model,min(cfg['n'],128))
    dump(output_root/'ring_benchmark.json',ring_diag)
    results=[]
    for b0 in cfg['b0']:
        print(f'Running B0={b0:.5f}, N={cfg["n"]}, final_time={cfg["final_time"]}...',flush=True)
        r=simulate(cfg['n'],b0,cfg['dt'],cfg['final_time'],cfg['snapshot_interval'],
          cfg['perturb'],Lambda,0.05,cfg['seed'],save_path=output_root/f'trace_B{b0:.5f}_N{cfg["n"]}.csv')
        results.append(r)
        print(f'  {r["stop_reason"]} t={r["attained_time"]:.5f} energy_error={r["last"]["energy_rel"]:.3e}',flush=True)
    dump(output_root/'results.json',results)
    gates={'G0_PROVENANCE':'PASS' if run['input_sha256'] else 'FAIL',
      'G1_RING_SYMMETRY':'PASS' if ring_diag['symmetry_pass'] else 'FAIL',
      'G2_NUMERIC_ENERGY':'PASS' if all(r['last']['energy_rel']<=1e-3 for r in results) else 'FAIL',
      'G3_RUBAN_T300_AND_TRAVEL1200':'PASS' if any(r['b0']==0.154 and r['attained_time']>=300 and abs(r['net_z_travel'])>=1200 and r['stop_reason']=='TIME_LIMIT' for r in results) else 'UNRESOLVED',
      'G3_PUBLICATION_ENERGY_7DIGITS':'UNRESOLVED' if not any(r['attained_time']>=300 for r in results) else ('PASS' if any(r['b0']==.154 and r['last']['energy_rel']<5e-8 for r in results) else 'FAIL'),
      'G4_STABILITY_WINDOW':'UNRESOLVED',
      'G5_CONVERGENCE':'UNRESOLVED',
      'G6_PAPER_REPRODUCTION':'UNRESOLVED',
      'G7_EULER_FINITE_CORE':'NOT_TESTED'}
    if cfg['include_convergence']:
        # Full convergence campaign deliberately not simulated in pilot mode.
        gates['G5_CONVERGENCE']='UNRESOLVED_REQUIRES_INDEPENDENT_GRID_TIME_STUDIES'
    dump(output_root/'gates.json',gates)
    write_report(output_root,run,results)
    try:
        from .reportgen import render
        pdf_external=output_root.parent/(PREFIX+'_'+VERSION+'_FALSIFIER_REPORT.pdf')
        if pdf_external.exists():
            pdf_external=output_root.parent/(PREFIX+'_'+VERSION+'_'+safe_stamp+'_FALSIFIER_REPORT.pdf')
        render(output_root,pdf_external)
    except ImportError:
        print('WARNING: reportlab unavailable, PDF report skipped. Markdown report retained.',flush=True)
    zip_path=output_root.parent/(PREFIX+'_'+VERSION+'_outputs.zip')
    if zip_path.exists():
        zip_path=output_root.parent/(PREFIX+'_'+VERSION+'_outputs_'+safe_stamp+'.zip')
    archive_outputs(output_root,zip_path)
    print('Outputs:',output_root,'\nZIP:',zip_path,'\nGates:',gates,flush=True)
    return 0 if gates['G0_PROVENANCE']=='PASS' and gates['G1_RING_SYMMETRY']=='PASS' else 2

if __name__=='__main__':sys.exit(main())
