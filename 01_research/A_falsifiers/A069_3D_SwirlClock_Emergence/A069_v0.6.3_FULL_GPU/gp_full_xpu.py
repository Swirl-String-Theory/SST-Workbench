#!/usr/bin/env python3
"""A069 v0.6.3 FULL GPU DEVELOPMENT -- XPU Strang GP engine, not physical certification.

Strict Arc selection, immutable checkpoint continuation, chunked independent
v0.5.0 trefoil seeding, on-device GP and invariants, periodic checkpoint export.
No false framework 1.0.10 hardware qualification, source independence or clock.
"""
from __future__ import annotations
import argparse, datetime, hashlib, importlib, json, math, os, sys, time
from pathlib import Path
import numpy as np
from a069_v061.campaign_v062 import CASES,screening
from a069_v061.gp_core_v062 import coupling_from_xi
from gp_xpu_probe_v063_baseline import select_torch_device, sync, checkpoint_state

ROOT=Path(__file__).resolve().parent
SOURCE_SHA='bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e'
SCHEMA='A069-V063-FULL-GPU-DEVELOPMENT-1'

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def json_exclusive(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with open(p,'x',encoding='utf8') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False,default=str);f.write('\n')


def load_numpy_checkpoint(path,case):
    path=Path(path)
    if not path.is_file(): raise FileNotFoundError(f'checkpoint missing: {path}')
    psi,meta=checkpoint_state(path)
    expected_mu=coupling_from_xi(case.xi)
    checks={'case':(str(meta['case']),case.case_id),
            'grid_n':(int(meta['grid_n']),case.n),
            'box':(float(meta['box']),case.box),
            'xi':(float(meta['xi']),case.xi),
            'mu':(float(meta['mu']),expected_mu),
            'dt':(float(meta['dt']),case.dt),
            'source_sha256':(str(meta['source_sha256']),SOURCE_SHA)}
    bad={k:[v[0],v[1]] for k,v in checks.items() if v[0]!=v[1]}
    if bad:raise ValueError('FAIL_CLOSED_CHECKPOINT_SCIENCE_IDENTITY: '+json.dumps(bad))
    return psi,{'kind':'v0.6.2_readonly_continuation','checkpoint':str(path.absolute()),'sha256':sha256(path),
                'step':int(meta['step']),'meta':meta,'not_independent':True}


def load_generated_checkpoint(path,case):
    p=Path(path)
    side=p.with_suffix('.json')
    if not p.is_file() or not side.is_file(): raise FileNotFoundError('need both .npy and .json sidecar')
    info=json.loads(side.read_text(encoding='utf8'))
    if info.get('state_sha256')!=sha256(p):raise ValueError('checkpoint SHA-256 mismatch')
    sci=info['science']
    ref={'case':case.case_id,'n':case.n,'box':case.box,'xi':case.xi,'dt':case.dt,
         'mu':coupling_from_xi(case.xi),'source_sha256':SOURCE_SHA}
    mismatch={k:[sci.get(k),v] for k,v in ref.items() if sci.get(k)!=v}
    if mismatch:raise ValueError('checkpoint science identity mismatch: '+str(mismatch))
    arr=np.load(p,mmap_mode='r',allow_pickle=False)
    if arr.dtype!=np.complex64 or arr.shape!=(case.n,)*3:raise ValueError('checkpoint dtype/shape mismatch')
    return arr,{'kind':'v0.6.3_checkpoint_continuation','checkpoint':str(p.absolute()),
                'sha256':sha256(p),'step':int(info['step']),'not_independent':True}


def source_geometry_screen(case):
    """Recalculate immutable v0.6.1 geometry screen from native original centerline."""
    archive=ROOT/'upstream'/'v0.5.0_SOURCE_PUBLIC_PINNED.zip'
    if sha256(archive)!=SOURCE_SHA:raise ValueError('original public source ZIP SHA invalid')
    up=ROOT/'upstream_runtime'/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0'
    if not (up/'experiment'/'knotted_gp3d.py').is_file():
        import subprocess
        subprocess.run([sys.executable,str(ROOT/'bootstrap_upstream.py')],cwd=ROOT,check=True)
    if str(up) not in sys.path:sys.path.insert(0,str(up))
    module=importlib.import_module('experiment.knotted_gp3d')
    from a069_v061.geometry_gate import geometry_screen
    _poly,full=module._seed(case.kind,False,case.segments)
    geom=geometry_screen(full)
    screen=screening(case.kind,case.n,case.xi,case.box,geometry={
         'd_screen':geom['approx_min_nonlocal_segment_distance'],
         'kappa_max':geom['max_discrete_curvature']})
    return geom,screen


def seed_chunked(case,out_path,planes=2):
    """Byte-pinned v0.5.0 oriented solid angle and taper, but 3D positions in thin slabs.

    Writes memory-mapped complex64 field; NEVER resamples an evolved coarse state
    and calls it independent spatial convergence. Original source sample+segment
    geometry and exact phase prescription are preserved to FP32 storage accuracy.
    """
    archive=ROOT/'upstream'/'v0.5.0_SOURCE_PUBLIC_PINNED.zip'
    if sha256(archive)!=SOURCE_SHA:raise RuntimeError('pinned v0.5.0 source archive mismatch')
    up=ROOT/'upstream_runtime'/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0'
    if not (up/'experiment'/'knotted_gp3d.py').exists():
        import subprocess
        subprocess.run([sys.executable,str(ROOT/'bootstrap_upstream.py')],check=True,cwd=ROOT)
    sys.path.insert(0,str(up))
    m=importlib.import_module('experiment.knotted_gp3d')
    from scipy.spatial import cKDTree
    poly,raw=m._seed(case.kind,False,case.segments)
    anchor=np.asarray(raw.mean(axis=0),float)
    if np.max(np.linalg.norm(raw,axis=1))+2*case.xi >= .32*case.box:
        raise ValueError('core overlaps periodic taper')
    kd=cKDTree(raw)
    p=Path(out_path);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise FileExistsError(f'refuse to replace seeded field {p}')
    n=case.n;box=case.box;dx=box/n
    # atomic create-only: incomplete initialization is removed, never promoted.
    tmp=p.with_suffix('.part.npy')
    if tmp.exists():raise FileExistsError(f'stale incomplete field {tmp}')
    a=np.lib.format.open_memmap(tmp,mode='w+',dtype=np.complex64,shape=(n,n,n))
    pos=(np.arange(n,dtype=float)-n/2)*dx
    try:
        for i in range(0,n,planes):
            xs=pos[i:i+planes]
            xx,yy,zz=np.meshgrid(xs,pos,pos,indexing='ij')
            xyz=np.column_stack((xx.ravel(),yy.ravel(),zz.ravel()))
            theta=m._solid_angle_points(xyz,poly,anchor)
            distance=kd.query(xyz,workers=1)[0]
            amp=np.tanh(distance/(math.sqrt(2)*case.xi))
            radius=np.linalg.norm(xyz,axis=1)
            v=np.clip((.44*box-radius)/(.12*box),0.,1.)
            taper=v**3*(10-15*v+6*v*v)
            z=1+taper*(amp*np.exp(1j*theta)-1)
            a[i:i+len(xs)]=z.reshape((len(xs),n,n)).astype(np.complex64)
            if (i//planes)%max(1,32//planes)==0:print(f'[seed] {case.case_id}: {i+len(xs)}/{n} planes',flush=True)
        a.flush();del a
        os.rename(tmp,p)
    except BaseException:
        del a
        try:tmp.unlink()
        except OSError:pass
        raise
    return np.load(p,mmap_mode='r',allow_pickle=False), {'kind':'independent_2015_source_native_seed',
       'seed_file':str(p.absolute()),'sha256':sha256(p),'step':0,
       'source_sha256':SOURCE_SHA,'segments':case.segments,'stored_dtype':'complex64',
       'not_independent_physical_provider':True}


def metrics(torch,z,k2,box,mu):
    """Hamiltonian GP invariants with GPU reductions; FFT Parseval, no 3 inverse gradients."""
    density=torch.abs(z)**2
    norm=torch.mean(density)
    potential=(0.5*mu)*torch.mean((density-1)**2)
    freq=torch.fft.fftn(z)
    # Parseval: mean(|grad z|^2) = sum(k² |FFT|²)/N^6.
    # torch.mean reduces first by N³ and FFT magnitude squared by N³.
    n=z.shape[0]
    kinetic=0.5*torch.mean(k2*(torch.abs(freq)**2))/(n**3)
    res={'mass':float(norm.item()*box**3),
         'energy':float((kinetic+potential).item()*box**3),
         'energy_kinetic':float(kinetic.item()*box**3),
         'energy_potential':float(potential.item()*box**3),
         'energy_reduction_dtype':'torch.float32'}
    return res


def step(torch,z,kin,dt,mu):
    # Preserve the exact v0.6.2 Strang map; no unvalidated in-place aliasing.
    z=z*torch.exp((-0.5j*dt*mu)*(torch.abs(z)**2-1))
    z=torch.fft.ifftn(torch.fft.fftn(z)*kin)
    return z*torch.exp((-0.5j*dt*mu)*(torch.abs(z)**2-1))


def memory_guard(torch,dev,n,estimate_per_voxel=112,reserve_gib=0.75,utilization=.88):
    free,total=torch.xpu.mem_get_info(dev)
    estimate=round(n**3*estimate_per_voxel+reserve_gib*(2**30))
    guard={'n':n,'estimate_bytes':estimate,'estimate_bytes_per_voxel':estimate_per_voxel,
           'reserve_gib':reserve_gib,'utilization_fraction':utilization,
           'free_bytes':int(free),'total_bytes':int(total),'empirical_peak_calibrated':False,
           'passes':estimate<=free*utilization}
    if not guard['passes']:
        raise MemoryError(f'FAIL_CLOSED_XPU_VRAM: estimated {estimate/2**30:.2f} GiB; free {free/2**30:.2f} GiB; '
                           'start with B160/B256 before attempting A512; no override in this runner')
    return guard


def calibrated_vram_bytes_per_voxel(path):
    """Optional conservative estimate from a REAL B256 Arc run, not assumed hardware parity."""
    r=json.loads(Path(path).read_text(encoding='utf8'))
    if (r.get('schema')!=SCHEMA or not r.get('xpu_used') or
        r.get('case',{}).get('case_id')!='B256' or
        r.get('case',{}).get('n')!=256 or
        not isinstance(r.get('peak_reserved_bytes'),int) or r['peak_reserved_bytes']<=0):
        raise ValueError('VRAM calibration requires a real B256 XPU FULL GPU result with peak_reserved_bytes')
    if r.get('end_step',0)<=r.get('start_step',0):
        raise ValueError('VRAM calibration requires actual GP steps')
    observed=r['peak_reserved_bytes']/256**3
    # Platform FFT workspaces can be unaccounted; 25% is a screening margin,
    # NOT proof that larger grids fit. Lack of hardware counters remains explicit.
    return max(90,math.ceil(1.25*observed)),observed


def save_field(torch,z,p,case,step,source):
    """Create-once checkpoint with cryptographic sidecar. Never change a prior file."""
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    side=p.with_suffix('.json')
    if p.exists() or side.exists():raise FileExistsError(f'checkpoint collision {p}')
    field=z.detach().cpu().numpy()
    # Atomic file publication: write .part and rename with exclusive precheck.
    part=p.with_suffix('.part.npy')
    if part.exists():raise FileExistsError(f'stale partial checkpoint {part}')
    try:
        with open(part,'xb') as f:np.save(f,field,allow_pickle=False)
        os.rename(part,p)
        sci={'case':case.case_id,'n':case.n,'box':case.box,'dt':case.dt,'xi':case.xi,
             'mu':coupling_from_xi(case.xi),'source_sha256':SOURCE_SHA}
        content={'schema':'A069-V063-IMMUTABLE-CHECKPOINT-1','step':int(step),
                 'science':sci,'continuation_of':source,'state_sha256':sha256(p),
                 'dtype':'complex64','shape':list(field.shape),'not_independent':True}
        json_exclusive(side,content)
    except BaseException:
        if part.exists():part.unlink()
        raise
    return {'field':str(p),'metadata':str(side),'field_sha256':sha256(p),'step':step}


def fp64_parity(torch,start,case,dev,steps,tol):
    """Run a short FP64 CPU reference on the same input state; no official native SYCL certification."""
    from gp_xpu_probe_v063_baseline import numpy_step,kinetic_numpy,relative_l2
    src=np.asarray(start,dtype=np.complex128)
    kin=kinetic_numpy(case.n,case.box,case.dt)
    ref=src.copy()
    for _ in range(steps):ref=numpy_step(ref,kin,case.dt,coupling_from_xi(case.xi))
    src_gpu=torch.as_tensor(np.asarray(start,dtype=np.complex64).copy(),device=dev)
    k2_gpu=torch_k2(torch,case.n,case.box,dev)
    kin_gpu=torch.exp((-0.5j*case.dt)*k2_gpu)
    for _ in range(steps):src_gpu=step(torch,src_gpu,kin_gpu,case.dt,coupling_from_xi(case.xi))
    sync(torch,dev)
    candidate=src_gpu.cpu().numpy().astype(np.complex128)
    err=relative_l2(candidate,ref)
    return {'execution_status':'EXECUTED','relative_l2':err,'tolerance':tol,
            'status':'PASS_NUMERICAL_SCREENING' if err<tol else 'FAIL_PARITY',
            'steps':steps,'relative_to':'same-input NumPy FP64 Strang map',
            'not_full_trajectory_or_topology_certified':True}


def torch_k2(torch,n,box,dev):
    k=torch.fft.fftfreq(n,d=box/n,device=dev,dtype=torch.float32)*(2*math.pi)
    return k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2


def execute(args):
    import torch
    dev,info=select_torch_device(torch,args.backend,args.expected_name)
    if args.backend=='xpu' and not info['xpu_used']:raise RuntimeError('strict XPU mandatory; no fallback')
    case=CASES[args.case]
    if args.dt is not None:
        if args.init!='seed':
            raise ValueError('time-step variation requires independent source-native --init seed, never change checkpoint immutable dt')
        from dataclasses import replace
        case=replace(case,dt=args.dt)
    if case.dt<=0:raise ValueError('dt must be positive')
    if args.total_steps<1 or args.diagnostic_every<1 or args.checkpoint_every<1 or args.cpu_parity_steps<0:raise ValueError('steps and sampling invalid')
    if args.init not in ('checkpoint','generated','seed'):raise ValueError('bad init')
    if args.init in ('checkpoint','generated') and not args.checkpoint:raise ValueError('provide --checkpoint path')
    if args.init=='checkpoint':
        field,source=load_numpy_checkpoint(args.checkpoint,case)
    elif args.init=='generated':
        field,source=load_generated_checkpoint(args.checkpoint,case)
    else:
        # reserve and allocate before expensive Numba seed initialization.
        source=None;field=None
    if args.init!='seed' and source['step']>=args.total_steps:
        raise ValueError('total_steps must exceed checkpoint step')
    geometry,g32=source_geometry_screen(case)
    if not g32['all_preconditions_met'] and not args.allow_unqualified_geometry:
        raise RuntimeError('G32 FAIL_PRECONDITION: specify --allow-unqualified-geometry for diagnostic-only execution')
    calibration=None
    estimate_per_voxel=112
    if args.vram_calibration_run:
        estimate_per_voxel,observed=calibrated_vram_bytes_per_voxel(args.vram_calibration_run)
        calibration={'file':str(args.vram_calibration_run.absolute()),'sha256':sha256(args.vram_calibration_run),
                     'observed_peak_reserved_bytes_per_voxel':observed,'guard_estimate_bytes_per_voxel':estimate_per_voxel,
                     'source':'B256 measured XPU allocator, FFT external allocations may be excluded'}
    vram=(memory_guard(torch,dev,case.n,estimate_per_voxel=estimate_per_voxel) if dev.type=='xpu' else {'status':'CPU_DEVELOPMENT_SMOKE_NO_GPU_VRAM_CLAIM'})
    utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=args.output_dir/case.case_id/utc
    folder.mkdir(parents=True,exist_ok=False)
    if args.init=='seed':
        field,source=seed_chunked(case,folder/'initial_complex64.npy',args.seed_chunk_planes)
    step0=int(source['step']);mu=coupling_from_xi(case.xi)
    k2=torch_k2(torch,case.n,case.box,dev)
    kin=torch.exp((-0.5j*case.dt)*k2)
    z=torch.as_tensor(np.asarray(field,dtype=np.complex64).copy(),device=dev)
    if z.device!=dev or z.dtype!=torch.complex64:raise RuntimeError('incompatible GPU dtype/device')
    del field
    # Reference is prepared from original source only for manageable cases;
    # reopening from source handles streaming initialization or original checkpoint.
    parity={'execution_status':'NOT_EXECUTED','status':'UNRESOLVED','reason':'not requested'}
    if args.cpu_parity_steps:
        if case.n>args.cpu_parity_max_n:
            parity={'execution_status':'NOT_EXECUTED','status':'UNRESOLVED',
                    'reason':f'n={case.n} exceeds --cpu-parity-max-n={args.cpu_parity_max_n}'}
        else:
            if args.init=='checkpoint':ref_field,_=load_numpy_checkpoint(args.checkpoint,case)
            elif args.init=='generated':ref_field,_=load_generated_checkpoint(args.checkpoint,case)
            else:ref_field=np.load(folder/'initial_complex64.npy',mmap_mode='r',allow_pickle=False)
            parity=fp64_parity(torch,ref_field,case,dev,args.cpu_parity_steps,args.parity_tolerance)
            del ref_field
    start=time.perf_counter()
    trace=[];saved=[]
    initial=metrics(torch,z,k2,case.box,mu)
    trace.append(dict(step=step0,T=case.dt*step0,mass_relative_change=0.,energy_relative_change=0.,**initial))
    for j in range(step0+1,args.total_steps+1):
        z=step(torch,z,kin,case.dt,mu)
        if j%args.diagnostic_every==0 or j==args.total_steps:
            now=metrics(torch,z,k2,case.box,mu)
            trace.append(dict(step=j,T=case.dt*j,
                mass_relative_change=(now['mass']-initial['mass'])/initial['mass'],
                energy_relative_change=(now['energy']-initial['energy'])/max(abs(initial['energy']),1e-30),**now))
            print(f'[{args.backend}] {case.case_id} step {j} Δmass={trace[-1]["mass_relative_change"]:.3e} Δenergy={trace[-1]["energy_relative_change"]:.3e}',flush=True)
        if j%args.checkpoint_every==0 or j==args.total_steps:
            saved.append(save_field(torch,z,folder/f'T{j:06d}.npy',case,j,source))
    sync(torch,dev)
    wall=time.perf_counter()-start
    try:peak_alloc=int(torch.xpu.max_memory_allocated(dev));peak_reserved=int(torch.xpu.max_memory_reserved(dev))
    except Exception:peak_alloc=peak_reserved=None
    result={'schema':SCHEMA,'status':'DEVELOPMENT_NUMERICAL_NOT_CERTIFIED',
      'framework_target':'SST_Falsifier_Framework_v1.0.10_LOCAL_VALIDATED_CANDIDATE',
      'backend':('PyTorch-XPU-complex64-FFT' if dev.type=='xpu' else 'CPU_TORCH_COMPLEX64_SMOKE_ONLY'),'precision_authority':'CPU-FP64-reference-required',
      'device':info,'torch_version':torch.__version__,'case':case.__dict__,'source':source,
      'mu':mu,'model':'iψ_T=-(1/2)∇²ψ+μ(|ψ|²-1)ψ; compressible GP, not Euler',
      'g32_screen':g32,'source_geometry':geometry,'start_step':step0,'end_step':args.total_steps,
      'duration_segment':(args.total_steps-step0)*case.dt,
      'trace':trace,'cpu_fp64_parity':parity,'gpu_vram_forecast':vram,'gpu_vram_calibration':calibration,'xpu_used':bool(info['xpu_used']),
      'peak_allocated_bytes':peak_alloc,'peak_reserved_bytes':peak_reserved,
      'wall_seconds':wall,'checkpoint_manifest':saved,
      'gate_ledger':{'G32':{'status':'PASS' if g32['all_preconditions_met'] else 'FAIL',
                             'qualification':'DIAGNOSTIC_ONLY'},
                     'G33':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
                             'reason':'run separate offline subgrid snapshots'},
                     'G34':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
                             'reason':'no temporal isotopy proof'},
                     'G35':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
                             'reason':'no stationary/RPO mode or heldout clock'}},
      'physical_reconnection':None,'knot_type_preserved':None,'intrinsic_eigenmode_frequency':None,
      'swirl_clock_frequency':None,'claim_guard':'Numeric GPU GP and checkpoint continuation only; no clock, physical stability, or 3D Euler qualification.'}
    json_exclusive(folder/'RUN_RESULT.json',result)
    print(json.dumps({'result':str(folder/'RUN_RESULT.json'),'start_step':step0,'end_step':args.total_steps,
                      'cpu_parity':parity['status'],'g32':result['gate_ledger']['G32'],
                      'G34':'UNRESOLVED','G35':'UNRESOLVED','evolution_and_checkpoint_wall_seconds':wall},indent=2),flush=True)
    return result


def parse(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True,choices=list(CASES))
    p.add_argument('--backend',choices=('xpu','cpu'),default='xpu',help='CPU only for explicit development smoke; never GPU evidence')
    p.add_argument('--init',choices=('checkpoint','generated','seed'),required=True,
                   help='checkpoint=v0.6.2 NPZ; generated=v0.6.3 NPY+sidecar; seed=source-native new initialization')
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--expected-name',default='A770')
    p.add_argument('--vram-calibration-run',type=Path,help='OPTIONAL actual B256 XPU RUN_RESULT.json for 512^3 guarded estimate')
    p.add_argument('--dt',type=float,default=None,help='seed-only time-step refinement; NOT permitted when resuming')
    p.add_argument('--total-steps',type=int,default=32,help='ABSOLUTE timestep, including existing checkpoint steps')
    p.add_argument('--diagnostic-every',type=int,default=4)
    p.add_argument('--checkpoint-every',type=int,default=8)
    p.add_argument('--cpu-parity-steps',type=int,default=2)
    p.add_argument('--cpu-parity-max-n',type=int,default=160)
    p.add_argument('--parity-tolerance',type=float,default=3e-5)
    p.add_argument('--seed-chunk-planes',type=int,default=2)
    p.add_argument('--allow-unqualified-geometry',action='store_true')
    p.add_argument('--output-dir',type=Path,default=ROOT/'results')
    a=p.parse_args(argv)
    if a.parity_tolerance<=0 or a.seed_chunk_planes<1: p.error('invalid parity tolerance or seed chunk')
    if a.init!='seed' and not a.checkpoint:p.error('--checkpoint required with --init checkpoint/generated')
    if a.init=='seed' and a.checkpoint:p.error('--checkpoint is not allowed with --init seed')
    return a

if __name__=='__main__':execute(parse())
