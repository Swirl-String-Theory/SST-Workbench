"""Intel XPU full-grid Euler + RK4 passive trajectories. FP32 spectral math,
optional DD32 compensated tracer positions (not DD32 Euler). Fail closed.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,math,time,sys
from pathlib import Path
import numpy as np
from .adapters import Adapter,check_source,hash_file
from .gpu_core import TorchField,device_preflight,estimate_vram_gib
from .run import output_zip,record_csv

VERSION='v0.3.0'

def run(a):
    if a.grid<16 or a.grid%2:raise ValueError('grid must be even and >=16')
    if a.time<=0 or a.dt<=0 or a.markers<1 or a.trials<1:raise ValueError('positive parameters required')
    if not (0<=a.perturb<0.3):raise ValueError('invalid perturbation')
    from framework_bootstrap import resolve_framework_root
    runtime=resolve_framework_root()  # Framework v1.1.0 original 142-file integrity gate
    root=Path(a.source).resolve(); hashes=check_source(a.provider,root)
    # CPU initialization (pinned source-specific deposition) must also fit host RAM.
    estimated_host_gib=1.5+384*a.grid**3/2**30
    if estimated_host_gib>a.ram_limit_gib:
        raise MemoryError(f'HOST_INIT_RAM_PREFLIGHT_FAIL n={a.grid} estimate={estimated_host_gib:.2f} GiB > budget={a.ram_limit_gib:.2f} GiB')
    device,preflight=device_preflight(a.device,a.vram_limit_gib,a.grid,cpu_test=a.cpu_test)
    preflight['estimated_initialization_host_gib']=estimated_host_gib
    preflight['host_ram_limit_gib']=a.ram_limit_gib
    if not a.execute:
        preflight.update({'action':'PLAN_ONLY','provider':a.provider,'precision':a.precision,'source_hashes':hashes})
        print(json.dumps(preflight,indent=2));return None
    if a.device!='xpu' and not a.cpu_test:raise RuntimeError('NO_GPU_FALLBACK')
    steps=math.ceil(a.time/a.dt);dt=a.time/steps
    case=a.case if a.provider=='a077' else a.geometry
    key=a.provider+'_'+case
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=Path(a.output_parent).resolve()/f'EulerTrajectoryResolutionGenerator_{VERSION}-outputs'/f'{key}_n{a.grid}_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    preflight['scientific_execution']=False
    manifest={'schema':'SST-EULER-XPU-TRAJECTORY-1','version':VERSION,'provider':a.provider,'case':case,
      'source_hashes':hashes,'source_root':str(root),'framework_runtime_version':'1.1.0',
      'framework_runtime_verified_files':142,'grid':a.grid,'box_length':a.box_length,
      'core_factor':a.core_factor,'t_final':a.time,'dt':dt,'n':a.grid,'steps':steps,'n_tracers':a.markers,
      'n_trials':a.trials,'perturbation':a.perturb,'random_seed':a.seed,'precision':a.precision,
      'precision_authority':'FP32_FFT_EULER_SCREENING_ONLY',
      'dd32_scope':'COMPENSATED_TRACER_POSITION_ADDITION_ONLY' if a.precision=='dd32-tracer' else 'NONE',
      'preflight':preflight,'conservation_is_not_physical_stability':True,
      'physics_status':'UNRESOLVED','actual_xpu_run':a.device=='xpu','runs':[]}
    seeds=np.random.SeedSequence(a.seed).spawn(a.trials)
    for trial,seq in enumerate(seeds):
        # Deliberately source-locked CPU *initial condition*; field is then transferred
        # once to torch. Memory preflight for host initialization remains separate.
        cpu=Adapter(a.provider,root,a.grid,a.case,a.core,a.geometry,a.box_length,a.core_factor)
        field=TorchField(cpu,device);uh=field.uh
        trialseed=int(seq.generate_state(1)[0])
        uh=field.perturb(uh,a.perturb,trialseed)
        idx=np.linspace(0,len(cpu.marker_curve)-1,a.markers,dtype=np.int64)
        marks=np.asarray(cpu.marker_curve[idx],dtype=np.float64)
        t=field.t
        xhi=t.as_tensor(marks.astype('float32'),device=device)
        xlo=t.as_tensor((marks-marks.astype('float32')).astype('float32'),device=device)
        pos=np.empty((steps+1,a.markers,3),dtype=np.float64)
        vel=np.empty_like(pos)
        def sample_position():
            return xhi.detach().cpu().numpy().astype('float64')+xlo.detach().cpu().numpy().astype('float64')
        pos[0]=sample_position()
        vel[0]=field.interpolate(uh,xhi+xlo).detach().cpu().numpy()
        d0=field.diagnostics(uh);diag=[{'t':0.,**d0}];maxcfl=0.
        for i in range(steps):
            cfl=diag[-1]['max_velocity']*dt/field.dx
            if cfl>a.cfl_limit:
                raise RuntimeError(f'CFL_FAIL trial={trial} step={i} CFL={cfl} > {a.cfl_limit}')
            uh,xhi,xlo=field.step(uh,xhi,xlo,dt,a.precision=='dd32-tracer')
            pos[i+1]=sample_position()
            vel[i+1]=field.interpolate(uh,xhi+xlo).detach().cpu().numpy()
            if not np.isfinite(pos[i+1]).all() or not np.isfinite(vel[i+1]).all():
                raise FloatingPointError('NONFINITE_TRAJECTORIES')
            d=field.diagnostics(uh);diag.append({'t':dt*(i+1),**d})
            if not np.isfinite([d['energy'],d['helicity'],d['divergence_Linf']]).all():
                raise FloatingPointError('NONFINITE_EULER_FIELD')
            maxcfl=max(maxcfl,cfl)
            if (i+1)%max(1,steps//4)==0 or i==steps-1:
                print(f'[GPU:{a.device}/{a.precision}] {a.provider} N={a.grid} trial={trial+1}/{a.trials} step={i+1}/{steps}',flush=True)
        sub=out/f'trial_{trial:04d}';sub.mkdir()
        times=np.linspace(0,a.time,steps+1)
        np.savez_compressed(sub/'trajectory.npz',times_solver=times,positions_unwrapped_solver=pos,
                            velocity_solver=vel,initial_seed_positions_solver=marks,
                            trial_id=np.array(f'trial_{trial:04d}'))
        record_csv(sub/'conservation.csv',diag)
        # The 77/500 Ruban minor radius, not the wide Gaussian deposition width.
        small=(77/500) if a.provider=='a075' and a.geometry=='ruban' else (
           min(z['a'] for z in cpu.provenance['ring_spec']) if a.provider=='a077' else a.core*a.core_factor)
        drifts={'max_energy_relative_drift':max(abs(d['energy']-d0['energy']) for d in diag)/max(abs(d0['energy']),1e-30),
                'max_helicity_absolute_drift':max(abs(d['helicity']-d0['helicity']) for d in diag),
                'max_divergence_Linf':max(d['divergence_Linf'] for d in diag),
                'max_cfl':maxcfl,'core_radius_over_dx':float(small/field.dx),
                'spectral_effective_core_radius_cells':float((2/3)*small/field.dx)}
        (sub/'diagnostics.json').write_text(json.dumps({**drifts,'seed':trialseed,
           'scientific_status':'GPU_FP32_MODEL_SCREENING_ONLY',
           'source_initialization':'PINNED_CPU_SOURCE_TRANSFERRED_TO_DEVICE',
           'initial_provenance':cpu.provenance},indent=2,allow_nan=False,default=str)+'\n')
        manifest['runs'].append({'trial_id':trial,'diagnostics':drifts})
        manifest.setdefault('trials_summary',[]).append({'trial_id':trial,'energy_drift_max_rel':drifts['max_energy_relative_drift'],
          'max_divergence_Linf':drifts['max_divergence_Linf'],'max_cfl':drifts['max_cfl'],
          'min_core_width_grid_cells':drifts['core_radius_over_dx'],
          'spectral_effective_cells_per_smallest_radius':drifts['spectral_effective_core_radius_cells']})
        if a.device=='xpu':t.xpu.synchronize()
        del cpu,field,uh,xhi,xlo
    manifest['preflight']['scientific_execution']=True
    gates=[{'gate':'TG0','status':'PASS','authority':'TECHNICAL','reason':'Original Framework v1.1.0 runtime hash inventory 142/142 verified'},
      {'gate':'TG1','status':'PASS','authority':'TECHNICAL','reason':'Source-pinned solver inputs and initial geometry verified'},
      {'gate':'TG2','status':'PASS' if a.device=='xpu' else 'NOT_EXECUTED',
       'authority':'GPU_FP32_SCREENING_ONLY','reason':'Actual XPU Euler kernel executed' if a.device=='xpu' else 'CPU test; no XPU execution'},
      {'gate':'TG3','status':'UNRESOLVED','authority':'NONE','reason':'Complete spectral Euler DD32 arithmetic and parity NOT implemented'},
      {'gate':'TG4','status':'UNRESOLVED','authority':'NONE','reason':'Independent scientific GPU-versus-FP64 Euler parity at matched final time pending'},
      {'gate':'TG5','status':'UNRESOLVED','authority':'NONE','reason':'Material vortex-core stability not established'}]
    (out/'FRAMEWORK_DIAGNOSTIC_GATE_LEDGER.json').write_text(json.dumps({'schema':'SST-EXTERNAL-TOOL-DIAGNOSTIC-GATES-1','official_falsifier_CERTIFY':'NOT_EXECUTED',
       'framework_template_used':True,'source_framework':str(runtime),'gates':gates},indent=2)+'\n')
    (out/'GPU_BACKEND_EVIDENCE.json').write_text(json.dumps({'schema':'SST-EXPLORATORY-GPU-EVIDENCE-1',
       'actual_backend':'torch_xpu' if a.device=='xpu' else 'torch_cpu_test',
       'executed':a.device=='xpu','precision':'FP32_COMPLEX64_FFT',
       'dd32_tracer_accumulation':a.precision=='dd32-tracer',
       'scientific_2of3_qualification':'NOT_ASSESSED','source_sha256':hash_file(Path(__file__).parent/'gpu_core.py'),
       'solver_input_sha256':hashes,'device':preflight['device_name']},indent=2)+'\n')
    manifest['status']='GPU_EXECUTED_SCREEN_ONLY' if a.device=='xpu' else 'CPU_TEST_NO_GPU_AUTHORITY'
    (out/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    files={str(p.relative_to(out)):hash_file(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'OUTPUT_MANIFEST.json').write_text(json.dumps({'schema':'SST-OUTPUT-HASHES-1','files':files},indent=2)+'\n')
    arch,sha=output_zip(out)
    print('OUTPUT:',out,'ARCHIVE:',arch,'SHA256:',sha)
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description='True Intel XPU Euler 3D; FP32 FFT and optionally DD32 compensated tracer addition')
    p.add_argument('--provider',required=True,choices=['a075','a077']);p.add_argument('--source',required=True)
    p.add_argument('--grid',type=int,default=48);p.add_argument('--time',type=float,default=.02);p.add_argument('--dt',type=float,default=.002)
    p.add_argument('--markers',type=int,default=16);p.add_argument('--trials',type=int,default=1)
    p.add_argument('--seed',type=int,default=77075);p.add_argument('--perturb',type=float,default=0.)
    p.add_argument('--core-factor',type=float,default=1.);p.add_argument('--core',type=float,default=.42)
    p.add_argument('--box-length',type=float,default=None)
    p.add_argument('--geometry',default='ruban',choices=['ruban','coupled_ring_trefoil'])
    p.add_argument('--case',default='toroidal_plus',choices=['no_toroidal','toroidal_plus','toroidal_minus'])
    p.add_argument('--precision',default='dd32-tracer',choices=['fp32','dd32-tracer'])
    p.add_argument('--device',default='xpu',choices=['xpu','cpu-test']);p.add_argument('--cpu-test',action='store_true',help='development regression only; NEVER certify as GPU')
    p.add_argument('--vram-limit-gib',type=float,default=12.0)
    p.add_argument('--ram-limit-gib',type=float,default=16.0);p.add_argument('--cfl-limit',type=float,default=.16)
    p.add_argument('--output-parent',default='..');p.add_argument('--execute',action='store_true',help='otherwise safe preflight only')
    a=p.parse_args(argv)
    if a.vram_limit_gib<=0 or a.ram_limit_gib<=0 or a.cfl_limit<=0:p.error('invalid limits')
    run(a)
if __name__=='__main__':main()
