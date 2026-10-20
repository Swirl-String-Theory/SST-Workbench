"""A069 v0.6.2: memory-guarded real 3D GP campaign (DEVELOPMENT only).

The GP state is evolved in x,y,z. G32 is geometric preflight, never a
certificate of topology. All knot eigenmodes remain UNRESOLVED.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys,time,datetime,traceback
from pathlib import Path
import numpy as np
from a069_v061.geometry_gate import geometry_screen,readiness
from a069_v061.subgrid import subgrid_filaments,compare_filaments,spectral_grid_shift
from a069_v061.campaign_v062 import CASES,screening,resource_forecast,case_payload
from a069_v061.projection_topology_v062 import numerical_projection_audit
from a069_v061.gp_core_v062 import coupling_from_xi,conserved_mu,step_mu,kinetic

ROOT=Path(__file__).resolve().parent
UPSTREAM_SHA='bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e'


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def runtime_root():
    archive=ROOT/'upstream'/'v0.5.0_SOURCE_PUBLIC_PINNED.zip'
    if sha(archive)!=UPSTREAM_SHA:raise RuntimeError('PUBLIC v0.5.0 archive hash mismatch; REFUSE RUN')
    candidate=ROOT/'upstream_runtime'/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0'
    if not (candidate/'experiment'/'knotted_gp3d.py').is_file():
        import subprocess
        subprocess.run([sys.executable,str(ROOT/'bootstrap_upstream.py')],cwd=ROOT,check=True)
    if not (candidate/'experiment'/'knotted_gp3d.py').is_file():raise RuntimeError('v0.5.0 GP solver absent')
    return candidate


def strip(d):
    t={k:v for k,v in d.items() if k!='components'}
    t['components']=[{k:v for k,v in c.items() if k!='subgrid_polyline'} for c in d['components']]
    return t


def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(temp,p)


def inspect(psi,box,shifts):
    base=subgrid_filaments(psi,box)
    for c in base['components']:
        c['projection_diagnostic']=numerical_projection_audit(c['subgrid_polyline']) if c['simple_oriented_cycle'] else {'status':'UNRESOLVED_NON_SIMPLE_GRAPH','topology_certified':False}
    offset=[]
    for o in shifts:
        r=subgrid_filaments(spectral_grid_shift(psi,box,o),box)
        offset.append({'offset_in_grid_cells':list(o),'components':r['components_count'],
                       'junctions':r['ambiguous_lattice_junctions'],
                       'unlocalized_faces':r['unlocalized_faces'],
                       'simple_cycles':sum(int(z['simple_oriented_cycle']) for z in r['components']),
                       'qualified':r['subgrid_reconstruction_qualified']})
    return strip(base),offset


def calculate(case, args, actual_memory):
    src=runtime_root()
    sys.path.insert(0,str(src))
    from experiment.knotted_gp3d import _seed,initialize
    c=case
    mu=1.0 if args.legacy_normalized_gp else coupling_from_xi(c.xi)
    _poly,full=_seed(c.kind,nb=max(c.segments,32))
    geom=geometry_screen(full)
    g=readiness(geom,xi=c.xi,n=c.n,box=c.box)
    if args.audit_only:
        return {'schema':'A069-V062-AUDIT-1','status':'PREFLIGHT_AUDIT_ONLY',
          'case':vars(c),'mu':mu,'physical_core_consistency_mode':not args.legacy_normalized_gp,'geometry':geom,'readiness':g,
          'resource_forecast':resource_forecast(c.n,actual_memory),
          'precomputed_preview':screening(c.kind,c.n,c.xi,c.box),
          'intrinsic_mode':None,'physical_clock':None}
    if not g['qualified'] and not args.allow_unqualified_geometry:
        raise RuntimeError('G32 FAIL_CLOSED. Diagnostic run requires explicit --allow-unqualified-geometry')
    # safety guard is applied before costly initial-state allocation
    budget=resource_forecast(c.n,actual_memory)
    if budget['fits_budget'] is False and not args.allow_memory_overcommit:
        raise RuntimeError(f'RAM guard: forecast {budget["conservative_peak_gib"]} GiB, available {budget["available_gib"]} GiB. Use a different grid or explicitly override.')
    shifts=[(.37,.29,.41),(-.23,.19,-.31)]
    tstart=time.monotonic()
    step_start=0
    if args.resume_from is not None:
        with np.load(args.resume_from,allow_pickle=False) as ck:
            step_start=int(ck['step']); old_dt=float(ck['dt']); old_box=float(ck['box']);old_xi=float(ck['xi'])
            old_case=str(ck['case']);old_source=str(ck['source_sha256']);old_n=int(ck['grid_n']);old_mu=float(ck['mu'])
            if old_case!=c.case_id or old_dt!=c.dt or old_box!=c.box or old_xi!=c.xi or old_n!=c.n or old_mu!=mu or old_source!=UPSTREAM_SHA:
                raise RuntimeError('checkpoint immutable-science configuration mismatch')
            if step_start>=c.steps:raise RuntimeError('resume step must be less than target steps')
            psi=ck['psi'].copy()
        init={'restarted_from':str(args.resume_from),'checkpoint_sha256':sha(args.resume_from),
              'resuming_at_step':step_start,'not_independent_run':True}
    else:
        psi,init=initialize(kind=c.kind,mirror=False,n=c.n,box=c.box,xi=c.xi,segments=c.segments)
    initial,masks0=inspect(psi,c.box,shifts)
    m0,e0=conserved_mu(psi,c.box,mu)
    kin=kinetic(c.n,c.box,c.dt)
    trace=[{'step':step_start,'T':float(step_start*c.dt),'mass_drift':0.,'energy_drift':0.}]
    snapshots=[]
    try:
        for i in range(step_start+1,c.steps+1):
            psi=step_mu(psi,c.box,c.dt,mu,kin)
            if i%args.diagnostic_every==0 or i==c.steps:
                mass,energy=conserved_mu(psi,c.box,mu)
                trace.append({'step':i,'T':float(i*c.dt),
                       'mass_drift':float((mass-m0)/m0),
                       'energy_drift':float((energy-e0)/e0)})
                if args.save_checkpoints:
                    folder=args.output_dir/'checkpoints'/c.case_id/args.run_id
                    folder.mkdir(parents=True,exist_ok=True)
                    dest=folder/f'T{i:06d}.npz'
                    if dest.exists():raise RuntimeError(f'will not overwrite checkpoint {dest}')
                    np.savez_compressed(dest,psi=psi,step=i,dt=c.dt,box=c.box,xi=c.xi,case=c.case_id,grid_n=c.n,mu=mu,source_sha256=UPSTREAM_SHA)
                    snapshots.append({'path':str(dest.relative_to(args.output_dir)), 'sha256':sha(dest), 'step':i})
        final,masks1=inspect(psi,c.box,shifts)
    finally:
        del psi
    result={'schema':'A069-V062-GP-CAMPAIGN-1','status':'DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED',
      'case':vars(c),'mu':mu,'physical_core_consistency_mode':not args.legacy_normalized_gp,
      'physical_core_qualification':'PLANAR_GP_SOLITON_CONVENTION_ONLY_NOT_KNOT_STATIONARITY',
      'source_archive_sha256':UPSTREAM_SHA,
      'physical_model':'3D_COMPRESSIBLE_GP_NOT_EULER','geometry':geom,'G32':g,
      'initialization':init,'initial':initial,'final':final,
      'grid_offsets_initial':masks0,'grid_offsets_final':masks1,
      'comparison':compare_filaments(initial,final),
      'trace':trace,'checkpoint_manifests':snapshots,
      'partial_resumed_segment':bool(args.resume_from is not None),
      'resource_forecast':budget,'wall_seconds':round(time.monotonic()-tstart,3),
      'numerically_qualified_knot_trajectory':False,'physical_reconnection':None,
      'intrinsic_mode':None,'swirl_clock_frequency':None,
      'gates':{'G32':'PASS_GEOMETRY_SCREEN_ONLY' if g['qualified'] else 'FAIL_PRECONDITION',
               'G33':'PASS_RECONSTRUCTION_DIAGNOSTIC_ONLY' if initial['subgrid_reconstruction_qualified'] and final['subgrid_reconstruction_qualified'] else 'UNRESOLVED',
               'G34':'UNRESOLVED','G35':'UNRESOLVED'},
      'claim_guard':'Subgrid cycles and conserved norm/energy do NOT certify trefoil topology, GP stability or Swirl Clock.'}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=tuple(CASES),required=True)
    p.add_argument('--audit-only',action='store_true')
    p.add_argument('--allow-unqualified-geometry',action='store_true')
    p.add_argument('--allow-memory-overcommit',action='store_true',help='dangerous; RAM estimator is conservative but OOM possible')
    p.add_argument('--steps',type=int,default=None)
    p.add_argument('--dt',type=float,default=None)
    p.add_argument('--diagnostic-every',type=int,default=8)
    p.add_argument('--save-checkpoints',action='store_true')
    p.add_argument('--resume-from',type=Path,default=None)
    p.add_argument('--legacy-normalized-gp',action='store_true',help='mu=1 historical regression, not xi-consistent physical-core study')
    p.add_argument('--output-dir',type=Path,default=ROOT/'results')
    a=p.parse_args()
    c=CASES[a.case]
    from dataclasses import replace
    if a.steps is not None:c=replace(c,steps=a.steps)
    if a.dt is not None:c=replace(c,dt=a.dt)
    if c.steps<1 or c.dt<=0 or a.diagnostic_every<1:p.error('invalid time integration settings')
    import psutil
    mem=int(psutil.virtual_memory().available)
    a.output_dir=a.output_dir.resolve()
    audit=resource_forecast(c.n,mem)
    print(json.dumps({'case':vars(c),'screen':screening(c.kind,c.n,c.xi,c.box),
                     'resource':audit,'audit_only':a.audit_only,'gp_mu':1.0 if a.legacy_normalized_gp else coupling_from_xi(c.xi)},indent=2),flush=True)
    if not a.audit_only and not args_safe(c,a,mem):return 2
    run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    a.run_id=run_id
    out=a.output_dir/f'{c.case_id}__{run_id}.json'
    result=calculate(c,a,mem)
    result['run_id']=run_id
    if out.exists():raise RuntimeError('immutable case output collision')
    atomic_json(out,result)
    print(json.dumps({'file':str(out),'G32':result.get('gates',{}).get('G32'),'status':result['status'],
                      'G34':'UNRESOLVED','G35':'UNRESOLVED'},indent=2))
    return 0


def args_safe(c,a,mem):
    from a069_v061.campaign_v062 import resource_forecast,screening
    if not screening(c.kind,c.n,c.xi,c.box)['all_preconditions_met'] and not a.allow_unqualified_geometry:
        print('REJECTED: geometry FAIL_CLOSED; use --allow-unqualified-geometry for diagnostic-only execution',file=sys.stderr)
        return False
    if resource_forecast(c.n,mem)['fits_budget'] is False and not a.allow_memory_overcommit:
        print('REJECTED: predicted RAM pressure; choose smaller grid or explicit override',file=sys.stderr)
        return False
    return True

if __name__=='__main__':raise SystemExit(main())
