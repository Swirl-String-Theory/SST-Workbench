"""Shared Euler field/tracer resolution sweep for A075/A077; no frozen source edits."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,sys,time,zipfile
from pathlib import Path
import numpy as np
from .adapters import Adapter,hash_file,PINS

VERSION='v0.1.0'
GRID_PROFILES=(48,64,80,96)

def rk4_shared(s,uh,x,dt):
    # Tracer stages sample *the matching Euler RK4 stage*, not frozen field snapshots.
    k1=s.rhs(uh);v1=s.interp(uh,x)
    h2=s.proj(uh+.5*dt*k1)
    k2=s.rhs(h2);v2=s.interp(h2,x+.5*dt*v1)
    h3=s.proj(uh+.5*dt*k2)
    k3=s.rhs(h3);v3=s.interp(h3,x+.5*dt*v2)
    h4=s.proj(uh+dt*k3)
    k4=s.rhs(h4);v4=s.interp(h4,x+dt*v3)
    return s.proj(uh+dt*(k1+2*k2+2*k3+k4)/6),x+dt*(v1+2*v2+2*v3+v4)/6

def sha_payload(p):return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def record_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def output_zip(out):
    dest=out.with_suffix('.zip')
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out))
    digest=hash_file(dest);(Path(str(dest)+'.sha256')).write_text(digest+'  '+dest.name+'\n')
    return dest,digest

def estimate_gib(n):
    # Conservative empirical warning, NOT a platform-specific peak guarantee.
    return 0.35 + 0.9 * (n/80)**3

def run(args):
    root=Path(args.source).resolve()
    if not root.is_dir():raise FileNotFoundError('--source must be an existing source tree '+str(root))
    if args.n%2 or args.n<16:raise ValueError('even n>=16')
    if args.n>96 and not args.allow_large:raise ValueError('n>96 requires --allow-large')
    if args.time<=0 or args.dt<=0 or args.markers<1:raise ValueError('positive time/dt/markers required')
    if args.trials<1 or args.trials>1000:raise ValueError('1<=trials<=1000')
    if args.trials>1 and args.perturb<=0:raise ValueError('multiple trials require nonzero perturbations')
    if args.perturb<0 or args.perturb>=0.3:raise ValueError('perturb must be in [0,0.3)')
    if args.length_unit_m<=0 or args.speed_unit_m_s<=0:raise ValueError('nonpositive scale')
    steps=math.ceil(args.time/args.dt);dt=args.time/steps
    from .adapters import check_source
    hashes=check_source(args.provider,root)
    # Memory preflight must occur before large solvers allocate significant arrays.
    estimate=estimate_gib(args.n)
    if estimate>args.memory_limit_gib and not args.allow_memory:
        raise RuntimeError(f'MEMORY_PREFLIGHT: estimated {estimate:.2f} GiB, limit {args.memory_limit_gib} GiB; use --allow-memory to acknowledge')
    provider_key=args.provider+('_'+args.case if args.provider=='a077' else '_'+args.geometry)
    import datetime
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    outbase=Path(args.output_parent).resolve();out=outbase/(f'EulerTrajectoryResolutionGenerator_{VERSION}-outputs'+'/'+provider_key+'_n'+str(args.n)+'_'+stamp)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True,exist_ok=False)
    phases=[];manifest={'schema':'SST-EULER-TRAJECTORY-RESOLUTION-1','status':'DEVELOPMENT_DIAGNOSTIC_ONLY',
      'provider':args.provider,'case':args.case if args.provider=='a077' else args.geometry,
      'source_root_recorded':str(root),'source_sha256':hashes,'n':args.n,'t_final':args.time,'dt':dt,'steps':steps,
      'trials':args.trials,'seed':args.seed,'initial_perturbation_relative_rms':args.perturb,
      'length_unit_m':args.length_unit_m,'speed_unit_m_s':args.speed_unit_m_s,
      'scale_origin':'DECLARED_SIMILITUDE_NOT_ELECTRON_CALIBRATION',
      'memory_estimate_gib':estimate,'notes':['Passive tracers, not vortex tube centreline','Unwrapped periodic trajectories','Spatial resolution n is only one convergence axis','Euler solver does not prove infinite-domain or topology stability','SST spin claims not tested']}
    before=time.monotonic();sequences=np.random.SeedSequence(args.seed).spawn(args.trials)
    for trial,seq in enumerate(sequences):
        a=Adapter(args.provider,root,args.n,args.case,args.core,args.geometry)
        uh=a.initial_hat.copy();rg=np.random.default_rng(seq)
        if args.perturb>0:
            # Independent smooth divergence-free perturbations in Fourier space.
            shape=a.physical_velocity(uh).shape
            noise=rg.normal(size=shape)
            if args.provider=='a075':
                ph=a.proj(a.sim.fft(noise))
                kk=a.sim.k2;scale=np.exp(-.5*args.perturb_filter**2*kk)[...,None]
            else:
                ph=a.proj(a.sim.fft(np.moveaxis(noise,-1,0)))
                kk=a.sim.k2;scale=np.exp(-.5*args.perturb_filter**2*kk)[None,...]
            ph=a.proj(ph*scale)
            pn=float(np.sqrt(np.sum(np.abs(ph)**2)));un=float(np.sqrt(np.sum(np.abs(uh)**2)))
            if pn<=0 or un<=0:raise RuntimeError('DEGENERATE_SOLENOIDAL_PERTURBATION')
            uh=a.proj(uh+args.perturb*un/pn*ph)
        marks=a.marker_curve[np.linspace(0,len(a.marker_curve)-1,args.markers,dtype=int)].copy()
        if not np.isfinite(marks).all():raise ValueError('invalid marker points')
        init=marks.copy();x=marks.copy()
        pos=np.zeros((steps+1,len(x),3),dtype=np.float64)
        velocities=np.zeros_like(pos);pos[0]=x;velocities[0]=a.interp(uh,x)
        diag=[];d0=a.diagnostics(uh);diag.append({'t':0.,**d0});energy0=d0['energy'];cflmax=0.
        if a.provider=='a075':
            core_diagnostic=args.core; secondary_width=77/500 if args.geometry=='ruban' else None
        else:
            core_diagnostic=min(float(z['a']) for z in a.provenance['ring_spec']); secondary_width=None
        if args.n*core_diagnostic/a.L < 2:
            print(f'[WARNING] {args.provider} n={args.n} width/dx={core_diagnostic/a.dx:.2f} < 2 cells; unqualified',flush=True)
        for j in range(steps):
            maxu=a.diagnostics(uh)['max_velocity'] if j==0 else diag[-1]['max_velocity']
            cfl=maxu*dt/a.dx
            if cfl>args.cfl_limit:raise RuntimeError(f'CFL_FAIL step={j} CFL={cfl:.6g} > {args.cfl_limit}')
            uh,x=rk4_shared(a,uh,x,dt)
            v=a.interp(uh,x);pos[j+1]=x;velocities[j+1]=v
            if not np.isfinite(x).all() or not np.isfinite(v).all():raise FloatingPointError('NONFINITE_TRAJECTORY')
            d=a.diagnostics(uh);cflmax=max(cflmax,cfl);diag.append({'t':(j+1)*dt,**d})
            if not np.isfinite([d['energy'],d['helicity'],d['divergence_Linf']]).all():raise FloatingPointError('NONFINITE_EULER')
            if j==steps-1 or (j+1)%max(1,steps//5)==0:
                print(f'[{args.provider}] n={args.n} trial={trial+1}/{args.trials} step={j+1}/{steps}',flush=True)
        times=np.linspace(0,args.time,steps+1)
        rel=np.array([d['energy'] for d in diag]);harr=np.array([d['helicity'] for d in diag]);
        em=float(np.max(np.abs(rel-energy0))/max(abs(energy0),1e-30))
        hm=float(np.max(np.abs(harr-harr[0])))
        tdir=out/f'trial_{trial:04d}';tdir.mkdir()
        np.savez_compressed(tdir/'trajectory.npz',times_solver=times,positions_unwrapped_solver=pos,
          velocity_solver=velocities,initial_seed_positions_solver=init,
          times_s=times*args.length_unit_m/args.speed_unit_m_s,
          positions_m=pos*args.length_unit_m,velocities_m_s=velocities*args.speed_unit_m_s,
          trial_id=np.array(f'trial_{trial:04d}'))
        record_csv(tdir/'conservation.csv',diag)
        report={'trial_id':trial,'spawn_key':list(seq.spawn_key),'energy_drift_max_rel':em,
          'helicity_drift_max_abs':hm,'max_divergence_Linf':float(max(d['divergence_Linf'] for d in diag)),
          'max_cfl':cflmax,'min_core_width_grid_cells':float(core_diagnostic/a.dx),
          'ruban_minor_radius_grid_cells':None if secondary_width is None else secondary_width/a.dx,
          'initial_provenance':a.provenance,'n_samples':steps+1,'n_tracers':len(x),
          'invalidity_status':'NOT_CERTIFIED_FINITE_CORE_EULER'}
        (tdir/'diagnostics.json').write_text(json.dumps(report,indent=2,default=str,allow_nan=False)+'\n')
        phases.append(report)
        del a,uh
    manifest['trials_summary']=[{k:p[k] for k in ('trial_id','energy_drift_max_rel','helicity_drift_max_abs','max_divergence_Linf','max_cfl','min_core_width_grid_cells','ruban_minor_radius_grid_cells')} for p in phases]
    manifest['runtime_wall_s']=round(time.monotonic()-before,3)
    manifest['source_contract_sha256']=sha_payload(hashes)
    manifest['physics_status']='UNQUALIFIED: space/time/core/domain and material vorticity trajectory gates not closed'
    (out/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    digest={str(p.relative_to(out)):hash_file(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'OUTPUT_MANIFEST.json').write_text(json.dumps({'schema':'SST-OUTPUT-HASHES-1','files':digest},indent=2)+'\n')
    arch,h=output_zip(out)
    print('OUTPUT:',out,'\nARCHIVE:',arch,'\nSHA256:',h,flush=True)
    return out

def main():
    p=argparse.ArgumentParser(description='SST full Euler 3D passive-trajectory generator for pinned A075/A077 sources')
    p.add_argument('--provider',choices=('a075','a077'),required=True);p.add_argument('--source',required=True)
    p.add_argument('--grid',dest='n',type=int,default=48);p.add_argument('--all',action='store_true',help='run 48,64,80,96 serially at identical final time and dt')
    p.add_argument('--temporal',action='store_true',help='run same grid with dt, dt/2, dt/4 at identical final time')
    p.add_argument('--case',default='toroidal_plus');p.add_argument('--geometry',choices=('ruban','coupled_ring_trefoil'),default='ruban')
    p.add_argument('--core',type=float,default=.42,help='A075 spectral Gaussian core width')
    p.add_argument('--time',type=float,default=.02);p.add_argument('--dt',type=float,default=.001)
    p.add_argument('--markers',type=int,default=8);p.add_argument('--trials',type=int,default=1);p.add_argument('--seed',type=int,default=77075)
    p.add_argument('--perturb',type=float,default=0.0);p.add_argument('--perturb-filter',type=float,default=.5)
    p.add_argument('--length-unit-m',type=float,default=1.0);p.add_argument('--speed-unit-m-s',type=float,default=1.0)
    p.add_argument('--output-parent',default='..');p.add_argument('--memory-limit-gib',type=float,default=8.)
    p.add_argument('--allow-memory',action='store_true');p.add_argument('--allow-large',action='store_true')
    p.add_argument('--cfl-limit',type=float,default=.20)
    a=p.parse_args()
    if a.all and a.temporal:raise ValueError('run --all and --temporal in separate campaigns')
    if a.all:
        for n in GRID_PROFILES:
            a.n=n;run(a)  # fixed dt and final time (spatial/representation ladder)
    elif a.temporal:
        dt0=a.dt
        for scale in (1,2,4):
            a.dt=dt0/scale;run(a)  # fixed n and final time (temporal ladder)
    else:run(a)
if __name__=='__main__':main()
