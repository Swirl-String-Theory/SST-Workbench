"""Ruban 2018 reproducibility study, safe step control and fail-closed gates."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,platform,sys,time,zipfile,shutil
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .model import RubanModel,torus_knot,ring
from .metrics import length,shape_drift,segment_stats,nonlocal_clearance,is_regular
VERSION='v0.1.1'; PREFIX='Ruban_T23_Reproduction';ROOT=Path(__file__).resolve().parents[1]

def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def configure(mode):
    return {
      'SMOKE':dict(n=64,dt=0.001,final_time=.025,snapshot_interval=.005,b0=[.154],perturb=1e-5,include_convergence=False),
      'BASIC':dict(n=128,dt=.002,final_time=.5,snapshot_interval=.05,b0=[.14,.154,.17],perturb=1e-4,include_convergence=False),
      'FULL':dict(n=256,dt=.002,final_time=320.,snapshot_interval=.5,b0=[.14,.148,.152,.154,.156,.16,.168],perturb=1e-4,include_convergence=False),
      'CERTIFY':dict(n=256,dt=.002,final_time=320.,snapshot_interval=.5,b0=[.154],perturb=1e-4,include_convergence=True),
    }[mode].copy()

def ring_test(model,n=128):
    u=model.velocity(ring(n));return {'n':n,'mean_uz':float(np.mean(u[:,2])),
      'max_transverse_velocity':float(np.linalg.norm(u[:,:2],axis=1).max()),
      'std_uz':float(np.std(u[:,2])),
      'symmetry_pass':bool(np.linalg.norm(u[:,:2],axis=1).max()<2e-9 and np.std(u[:,2])<2e-9)}

def local_induction_dt_cap(x,lambda_tilde,safety=.4):
    """Conservative necessary screening bound, not full nonlocal spectrum certificate.
    RK4 imaginary-axis stability |omega dt| <= 2 sqrt(2), omega~lt*k^2/2.
    k_max~pi/ds_min. This is a heuristic necessary cap in dimensionaless units.
    """
    ds=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    if not np.all(np.isfinite(ds)) or ds.min()<1e-9: return 0.
    if abs(lambda_tilde)<1e-14:return math.inf
    return float(safety*4*math.sqrt(2)/abs(lambda_tilde)*(float(ds.min())/math.pi)**2)

def simulate(n,b0,dt,final_time,snapshot_interval,perturb,Lambda,delta,seed,
             max_drift=.25,max_energy_rel=1e-3,max_ds_ratio=10.,save_path=None,
             snapshot_path=None,dt_safety=.4,diagnostic_interval=.025):
    if n<24 or dt<=0 or final_time<=0 or snapshot_interval<=0:raise ValueError('bad n/dt/t')
    model=RubanModel(Lambda,delta)
    x0=torus_knot(n,b0,perturbation=perturb,seed=seed);ref=torus_knot(n,b0)
    e0=model.energy(x0);l0=length(x0)
    x=x0.copy();t=0.;steps=0;max_steps=math.ceil(final_time/(dt*1e-4))+10
    records=[];frames=[];times=[];stop='TIME_LIMIT';min_dt=dt; min_stability_cap=math.inf
    def sample():
        energy=model.energy(x);drift=shape_drift(x,ref,quick=True)
        seg=segment_stats(x)
        return dict(step=steps,time=round(t,12),energy=energy,energy_rel=abs(energy-e0)/max(abs(e0),1e-12),
           length=length(x),length_rel=length(x)/l0-1.,shape_rms=drift,
           z_mean=float(x[:,2].mean()),min_nonlocal_vertex_distance=nonlocal_clearance(x,skip=max(4,n//40)),**seg)
    records.append(sample());times.append(t);frames.append(x.copy());tstart=time.perf_counter()
    next_diag=min(diagnostic_interval,final_time)
    next_snapshot=min(snapshot_interval,final_time)
    while t < final_time-1e-12:
        if steps>=max_steps:stop='MAX_STEPS';break
        if not is_regular(x):stop='DEGENERATE_GEOMETRY';break
        seg=segment_stats(x)
        if seg['ds_ratio']>max_ds_ratio:stop='SAMPLING_QUALITY_STOP';break
        stepcap=local_induction_dt_cap(x,model.lambda_tilde,safety=dt_safety)
        min_stability_cap=min(min_stability_cap,stepcap)
        if stepcap<dt*1e-4:stop='TIMESTEP_UNDERFLOW';break
        h=min(dt,stepcap,final_time-t,next_diag-t,next_snapshot-t)
        if h<=1e-13:stop='TIMESTEP_UNDERFLOW';break
        min_dt=min(min_dt,h)
        try:x=model.rk4(x,h)
        except (FloatingPointError,OverflowError,ZeroDivisionError):stop='NONFINITE_FIELD';break
        t+=h;steps+=1
        if not is_regular(x):stop='DEGENERATE_GEOMETRY';break
        check=t>=next_diag-1e-10 or t>=next_snapshot-1e-10 or t>=final_time-1e-10
        if check:
            d=sample();records.append(d)
            if t>=next_snapshot-1e-10 or t>=final_time-1e-10:
                frames.append(x.copy());times.append(t)
                next_snapshot=min(final_time,next_snapshot+snapshot_interval)
            if d['energy_rel']>max_energy_rel:stop='ENERGY_DRIFT_STOP';break
            if d['ds_ratio']>max_ds_ratio:stop='SAMPLING_QUALITY_STOP';break
            if d['shape_rms']>max_drift:stop='OPERATIONAL_DEFORMATION_STOP';break
            next_diag=min(final_time,next_diag+diagnostic_interval)
    if records[-1]['step']!=steps and is_regular(x):
        try:records.append(sample());frames.append(x.copy());times.append(t)
        except Exception:pass
    if save_path:
        p=Path(save_path);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    if snapshot_path:
        p=Path(snapshot_path);p.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(p,times=np.asarray(times),xyz=np.stack(frames))
    last=records[-1]
    return dict(n=n,b0=b0,lambda_value=Lambda,delta=delta,lambda_tilde=model.lambda_tilde,
        dt_requested=dt,dt_min_observed=min_dt,min_stability_cap=min_stability_cap,dt_safety=dt_safety,target_final_time=final_time,
        attained_time=t,steps_taken=steps,elapsed_s=time.perf_counter()-tstart,initial_energy=e0,
        initial_length=l0,last=last,stop_reason=stop,net_z_travel=float(last['z_mean']-records[0]['z_mean']),
        operational_survival_only=stop=='TIME_LIMIT' and t>=final_time-1e-10,
        paper_reproduced='UNRESOLVED',euler_stability='NOT_TESTED')

def archive_outputs(out,path):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file() and p.suffix not in {'.aux','.log','.out','.toc'}:z.write(p,arcname=f'{out.name}/{p.relative_to(out).as_posix()}')
    path.with_suffix(path.suffix+'.sha256').write_text(hashfile(path)+'  '+path.name+'\n',encoding='utf-8')

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('mode',nargs='?',default='SMOKE')
    for k,t in [('n',int),('dt',float),('final-time',float),('snapshot-interval',float)]:p.add_argument('--'+k,type=t)
    p.add_argument('--b0',type=float,nargs='+');p.add_argument('--output-root',type=Path)
    a=p.parse_args(argv)
    if a.mode in ('FREEZE','CERTIFY','REVEAL'):
        print('REFUSED: native Framework v1.1.0 RC2 runtime is not installed and audited in this release.',file=sys.stderr);return 4
    if a.mode not in ('SMOKE','BASIC','FULL'):print('Unsupported mode',file=sys.stderr);return 4
    cfg=configure(a.mode)
    for key in ('n','dt','final_time','snapshot_interval','b0'):
        v=getattr(a,key,None)
        if v is not None:cfg[key]=v
    Lambda=1.4+.5*math.log(200);cfg.update(mode=a.mode,Lambda=Lambda,delta=.05,seed=20261030,dt_safety=.4,diagnostic_interval=.025)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=(a.output_root or ROOT/(PREFIX+'_'+VERSION+'-outputs')).resolve()
    if out.exists() and any(out.iterdir()):out=out.parent/(out.name+'_'+stamp)
    out.mkdir(parents=True,exist_ok=True)
    dump(out/'config.json',cfg)
    manifest={'mode':a.mode,'utc':stamp,'configuration_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
       'code_version':VERSION,'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),
       'code_sha256':{str(p.relative_to(ROOT)):hashfile(p) for p in sorted((ROOT/'ruban_falsifier').glob('*.py'))},
       'input_sha256':{f.name:hashfile(f) for f in sorted((ROOT/'inputs').iterdir()) if f.is_file()},
       'framework_template':'1.1.0 RC2','framework_runtime':'NOT_EXECUTED','qualification':'DEVELOPMENT_ONLY'}
    dump(out/'source_manifest.json',manifest)
    model=RubanModel(Lambda,.05);ringdiag=ring_test(model,min(cfg['n'],128));dump(out/'ring_benchmark.json',ringdiag)
    from .plotgen import seed_quad,evolution_plot
    figs=out/'figures';figs.mkdir(exist_ok=True);seed_quad(figs/'seed_quad.png')
    results=[]
    for b0 in cfg['b0']:
        print(f'Ruban {a.mode}: B0={b0:.5f} n={cfg["n"]} requested_dt={cfg["dt"]} tmax={cfg["final_time"]}',flush=True)
        trace=out/f'trace_B{b0:.5f}_N{cfg["n"]}.csv';snap=out/f'snapshots_B{b0:.5f}_N{cfg["n"]}.npz'
        result=simulate(cfg['n'],b0,cfg['dt'],cfg['final_time'],cfg['snapshot_interval'],cfg['perturb'],Lambda,.05,cfg['seed'],
            save_path=trace,snapshot_path=snap,dt_safety=cfg['dt_safety'],diagnostic_interval=cfg['diagnostic_interval'])
        results.append(result)
        if abs(b0-.154)<1e-10:evolution_plot(figs/'evolution.png',snap,trace)
        print(f'  {result["stop_reason"]} t={result["attained_time"]:.6f} energy={result["last"]["energy_rel"]:.4g} min_dt={result["dt_min_observed"]:.4g}',flush=True)
    dump(out/'results.json',results)
    good=all(r['last']['energy_rel']<=1e-3 and r['stop_reason'] not in ('ENERGY_DRIFT_STOP','SAMPLING_QUALITY_STOP','TIMESTEP_UNDERFLOW','DEGENERATE_GEOMETRY','NONFINITE_FIELD','MAX_STEPS') for r in results)
    canonical=[r for r in results if abs(r['b0']-.154)<1e-9]
    gates={'G0_PROVENANCE':'PASS' if manifest['input_sha256'] else 'FAIL','G1_RING_SYMMETRY':'PASS' if ringdiag['symmetry_pass'] else 'FAIL',
       'G2_NUMERIC_ENERGY':'PASS' if good else 'FAIL',
       'G3_RUBAN_T300_AND_TRAVEL1200':'UNRESOLVED','G3_PUBLICATION_ENERGY_7DIGITS':'UNRESOLVED',
       'G4_STABILITY_WINDOW':'UNRESOLVED','G5_CONVERGENCE':'UNRESOLVED',
       'G6_PAPER_REPRODUCTION':'UNRESOLVED','G7_EULER_FINITE_CORE':'NOT_TESTED',
       'FRAMEWORK_RUNTIME_CERTIFICATION':'NOT_EXECUTED'}
    # Operational pass is distinct from peer-reviewed replication and needs converged field.
    if canonical and canonical[0]['attained_time']>=300 and canonical[0]['operational_survival_only'] and abs(canonical[0]['net_z_travel'])>=1200 and good:
        gates['G3_RUBAN_T300_AND_TRAVEL1200']='OPERATIONAL_PASS_NOT_CERTIFIED'
    dump(out/'gates.json',gates)
    from .reportgen import render
    try:pdf=render(out,ROOT,stamp)
    except Exception as exc:
        dump(out/'report_error.json',{'error':str(exc),'status':'PDF_FAILED'});pdf=None
        print('REPORT ERROR:',exc,file=sys.stderr)
    archive=out.parent/(PREFIX+'_'+VERSION+'_outputs.zip')
    if archive.exists():archive=out.parent/(PREFIX+'_'+VERSION+'_outputs_'+stamp+'.zip')
    archive_outputs(out,archive)
    print('OUTPUT',out,'ARCHIVE',archive,'PDF',pdf,'GATES',gates,flush=True)
    return 0 if gates['G0_PROVENANCE']=='PASS' and gates['G1_RING_SYMMETRY']=='PASS' and gates['G2_NUMERIC_ENERGY']=='PASS' and pdf is not None else 2
if __name__=='__main__':sys.exit(main())
