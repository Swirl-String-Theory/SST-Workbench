"""A065 v0.4.3: independent post-export gate & longer RK4 time series.

A003 remains a geometric seed and Gaussian width is ASSUMED. GPU results
are screened against independent NumPy FP64 and audited after serialization.
"""
from __future__ import annotations
import hashlib,json,os,time,sys,importlib.metadata as md
from pathlib import Path
import numpy as np
from .export_audit_v043 import load_protocol,audit_files,inspect_array_bytes,relative,source_hash,EvidenceError
from .gpu_euler_v041 import require_arc,GPUUnavailable
from .volume_v040 import selected_sources,preflight as old_preflight
from .native_core_v038 import gaussian_vorticity,spectral_helmholtz
from .security import verify_all

def not_run(why):return {'status':'NOT_RUN_PREREQUISITE','reason':why,'execution_status':'NOT_EXECUTED'}

def _hash_stream(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def registered_framework_gates(root):
    # Deliberate: no old *v0.4.2* file from other runs is silently promoted.
    from .export_audit_v043 import load_protocol
    cfg,pin=load_protocol(root)
    # Optional explicit evidence import: hash and independently recompute the
    # selected exported arrays, never consult another run implicitly.
    external=os.environ.get('SST_A065_V043_EVIDENCE_ZIP','').strip()
    if external:
        from .export_audit_v043 import audit_files
        path=Path(external)
        if not path.is_file():raise EvidenceError('EXPLICIT_V043_EVIDENCE_NOT_FOUND:'+str(path))
        audited=audit_files(root,[path])
        gates={'G49':not_run('No independently authenticated Arc runtime operator build attestation supplied by post-export fields'),
               'G50':audited['gates']['G50'],
               'G51':audited['gates']['G51'],
               'G52':audited['gates']['G52'],
               'G53':audited['gates']['G53'],
               'G54':audited['gates']['G54']}
        return {'schema':'A065-V043-FRAMEWORK-IMPORTED-EVIDENCE-1','v043_prereg_sha256':pin,
                'external_archive_sha256':_hash_stream(path),
                'gates':gates,'volume_pairs':audited['volume_pairs'],
                'source_consistency':audited['source_consistency'],
                'authority':'INDEPENDENT_NUMERICAL_POST_EXPORT_ONLY'}
    found=Path(root)/'outputs/POST_EXPORT_V043_RESULT.json' 
    if found.is_file():
        r=json.loads(found.read_text())
        if r.get('v043_prereg_sha256')!=pin:raise EvidenceError('V043_EXPORT_PRECOMMIT_MISMATCH')
        return r
    gates={g:not_run('Separate v0.4.3 GPU_EXTENDED or POST_EXPORT evidence not yet executed in this isolated framework run')
           for g in ('G49','G50','G51','G52','G53')}
    gates['G54']={'status':'UNRESOLVED','reason':'No independent physical PKLSA vortex-core and pressure observations'}
    return {'schema':'A065-V043-FRAMEWORK-GATES-1','v043_prereg_sha256':pin,'gates':gates}

def operators_fingerprint(root,dpnp=None,dpctl=None,device=None):
    """Hash local operator code plus importable binary library payloads.

    This does NOT certify the complete linked Intel driver/oneMKL stack;
    driver/compiler runtime fingerprints need a device-side build record.
    """
    root=Path(root)
    source={k:source_hash((root/k).read_bytes()) for k in
          ('triadic/gpu_euler_v041.py','triadic/gpu_trace_v043.py','triadic/export_audit_v043.py')}
    res={'operator_source_sha256':source,'python_executable':sys.executable,'python_version':sys.version,
         'numpy_version':np.__version__,'device':device or {},'runtime_packages':{},
         'compiled_binary_sha256':{},'complete_driver_and_onemkl_provenance':False}
    for pkg,obj in (('dpnp',dpnp),('dpctl',dpctl)):
        if obj is None:continue
        res['runtime_packages'][pkg]={'version':getattr(obj,'__version__',md.version(pkg))}
        path=Path(obj.__file__).parent
        libs=sorted([p for p in path.rglob('*') if p.suffix.lower() in ('.pyd','.dll','.so') and p.is_file()])
        for p in libs[:100]:
            res['compiled_binary_sha256'][f'{pkg}/{p.relative_to(path).as_posix()}']=source_hash(p.read_bytes())
        res['runtime_packages'][pkg]['candidate_binary_count']=len(libs)
        res['runtime_packages'][pkg]['fully_scanned']=(len(libs)<=100)
    blob=json.dumps(res,sort_keys=True,default=str,ensure_ascii=False).encode()
    res['fingerprint_sha256']=source_hash(blob)
    return res

def solve_trace(xp,u0,L,T,steps,*,queue=None,snapshot_indices=(0,8,16),trace_indices=(0,4,8,12,16),rho=1.):
    """Numerically equivalent dealiased rotational Euler RK4 used by v0.4.1.

    Native device FFT/RK4 resident on Arc, extracts only preregistered steps.
    Explicitly rederives p and omega at each observation.
    """
    if steps<1 or any(j<0 or j>steps for j in snapshot_indices):raise ValueError('TRACE_INDEX_INVALID')
    if len(set(u0.shape[1:]))!=1 or u0.shape[0]!=3:raise ValueError('TRACE_SHAPE_INVALID')
    n=u0.shape[1];gpu=queue is not None;dt_dtype=np.float32 if gpu else np.float64
    def host(x):return xp.asarray(x,sycl_queue=queue,usm_type='device') if gpu else np.asarray(x)
    k=(2*np.pi*np.fft.fftfreq(n,d=L/n)).astype(dt_dtype)
    kx,ky,kz=host(k[:,None,None]),host(k[None,:,None]),host(k[None,None,:])
    k2=kx*kx+ky*ky+kz*kz
    inv=xp.where(k2>0,1/xp.where(k2>0,k2,1),0)
    m=np.fft.fftfreq(n)*n;b=np.abs(m)<n/3
    mask=b[:,None,None]&b[None,:,None]&b[None,None,:]
    mask[0,0,0]=False;mask=host(mask)
    def project(U):
        s=(kx*U[0]+ky*U[1]+kz*U[2])*inv
        return xp.stack((U[0]-kx*s,U[1]-ky*s,U[2]-kz*s),axis=0)*mask
    def curl(U):return xp.stack((1j*(ky*U[2]-kz*U[1]),1j*(kz*U[0]-kx*U[2]),1j*(kx*U[1]-ky*U[0])),axis=0)
    def cross(a,b):return xp.stack((a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]),axis=0)
    fft=lambda x:xp.fft.fftn(x,axes=(-3,-2,-1))
    ifft=lambda x:xp.fft.ifftn(x,axes=(-3,-2,-1)).real
    def rhs(U):
        u=ifft(U);w=ifft(curl(U))
        return project(fft(cross(u,w)))
    U=project(fft(u0));dt=dt_dtype(T/steps)
    checkpoints={};summary=[]
    to_host=xp.asnumpy if gpu else np.asarray
    started=time.perf_counter()
    def capture(i):
        u=ifft(U);w=ifft(curl(U));C=fft(cross(u,w))
        qhat=-1j*(kx*C[0]+ky*C[1]+kz*C[2])*inv
        p=ifft(qhat)-.5*xp.sum(u*u,axis=0)
        p=p-xp.mean(p)
        div=ifft(1j*(kx*U[0]+ky*U[1]+kz*U[2]))
        Eu=.5*rho*xp.mean(xp.sum(u*u,axis=0))*L**3
        Zu=.5*xp.mean(xp.sum(w*w,axis=0))*L**3
        if gpu:queue.wait()
        summary.append({'index':i,'t':float(T*i/steps),'energy':float(to_host(Eu)),
                'enstrophy':float(to_host(Zu)), 'divergence_in_run_rms':float(np.sqrt(np.mean(to_host(div)**2)))})
        if i in snapshot_indices:
            # Export exact float32/float64 arrays, not float64 recasts.
            dtype=np.float32 if gpu else np.float64
            checkpoints[i]={'u':np.asarray(to_host(u),dtype=dtype),
                            'omega':np.asarray(to_host(w),dtype=dtype),
                            'p':np.asarray(to_host(p),dtype=dtype)}
    for i in range(steps+1):
        if i in trace_indices or i in snapshot_indices:capture(i)
        if i==steps:break
        k1=rhs(U);k2v=rhs(project(U+dt*k1/2));k3=rhs(project(U+dt*k2v/2));k4=rhs(project(U+dt*k3))
        U=project(U+(dt/6)*(k1+2*k2v+2*k3+k4))
    if gpu:queue.wait()
    return {'snapshots':checkpoints,'trace':summary,'seconds':time.perf_counter()-started,
            'backend':'ARC_DPNP_FP32' if gpu else 'NUMPY_FP64'}

def run_extended(root):
    root=Path(root);verify_all(root)
    cfg,pin=load_protocol(root);old,oldsha=old_preflight(root)
    results={'schema':'A065-V043-EXTENDED-GPU-1','v043_prereg_sha256':pin,'protocol':cfg,
             'gates':{},'source_class':'A003_GAUSSIAN_SEEDED_EULER_NOT_PHYSICAL_PKLSA','seeds':{},'fingerprint':None}
    try:dpnp,queue,device=require_arc()
    except GPUUnavailable as exc:
        results['gates']={g:not_run(str(exc)) for g in ('G49','G50','G51','G52','G53')}
        results['gates']['G54']={'status':'UNRESOLVED','reason':'No independent physical PKLSA source'}
        results['device_error']=str(exc);_store(root,results);return results
    import dpctl
    device={**device,'driver_version':str(getattr(queue.sycl_device,'driver_version','UNKNOWN')),
        'platform_name':str(getattr(getattr(queue.sycl_device,'sycl_platform',None),'name','UNKNOWN')),
        'device_vendor':str(getattr(queue.sycl_device,'vendor','UNKNOWN'))}
    fp=operators_fingerprint(root,dpnp,dpctl,device);results['fingerprint']=fp
    results['gates']['G49']={'status':'PASS' if len(fp['compiled_binary_sha256'])>0 and all(x['fully_scanned'] for x in fp['runtime_packages'].values()) else 'UNRESOLVED',
        'reason':'Local operator source and installed dpnp/dpctl binaries hashed. Driver/oneMKL full build chain NOT certified',
        'metrics':{'fingerprint_sha256':fp['fingerprint_sha256'],'binaries':len(fp['compiled_binary_sha256']),'device':device}}
    sources,missing=selected_sources(root,old)
    if missing:
        for gid in ('G50','G51','G52','G53'):results['gates'][gid]=not_run(missing)
        results['gates']['G54']={'status':'UNRESOLVED','reason':'No independent physical PKLSA source'}
        _store(root,results);return results
    output=root/'outputs';output.mkdir(parents=True,exist_ok=True)
    statuses={'cpu':[],'gpu':[]};refinements=[];counts=0
    for sid,src in sources.items():
        rows=[]
        for n in cfg['grids']:
            omega=gaussian_vorticity(src['xyz'],n,cfg['L'],cfg['Gaussian_a_assumed'],old['gamma_assumed'])
            initial=spectral_helmholtz(omega,cfg['L'],cfg['rho'])['u']
            pair={}
            for backend in ('cpu','gpu'):
                xp,queue_arg=(np,None) if backend=='cpu' else (dpnp,queue)
                x0=np.asarray(initial,dtype=np.float64 if backend=='cpu' else np.float32)
                if backend=='gpu':x0=dpnp.asarray(x0,sycl_queue=queue,usm_type='device')
                run=solve_trace(xp,x0,cfg['L'],cfg['T'],cfg['coarse_steps'],queue=queue_arg,
                                snapshot_indices=cfg['field_snapshots_indices'],trace_indices=cfg['trace_indices'])
                refined=solve_trace(xp,x0,cfg['L'],cfg['T'],cfg['refined_steps'],queue=queue_arg,
                                    snapshot_indices=(cfg['refined_steps'],),trace_indices=(cfg['refined_steps'],))
                a=run['snapshots'];q=a[cfg['coarse_steps']];r=refined['snapshots'][cfg['refined_steps']]
                terr={k:relative(q[k],np.asarray(r[k],dtype=np.float64)) for k in ('u','omega','p')}
                ref_ok=all(terr[k]<=cfg['time_refinement_tolerance'][k] for k in terr)
                refinements.append(ref_ok)
                idx=cfg['field_snapshots_indices']
                kw={k:q[k] for k in ('u','omega','p')}
                kw.update({k+'0':a[0][k] for k in ('u','omega','p')})
                kw.update({'trace_'+k:np.stack([a[t][k] for t in idx]) for k in ('u','omega','p')})
                kw.update({k+'_refined':r[k] for k in ('u','omega','p')})
                kw.update({'times':np.array([cfg['T']*j/cfg['coarse_steps'] for j in idx]),'L':cfg['L'],
                           'rho':cfg['rho'],'time':cfg['T'],'time0':0.,'source_sha256':src['sha256'],
                           'source_class':'NUMERICAL_EULER_GAUSSIAN_NOT_PHYSICAL_PKLSA'})
                filename=f'V043_{sid}_N{n}_{"CPU_FP64" if backend=="cpu" else "ARC_FP32"}.npz'
                dst=output/filename
                if dst.exists():raise FileExistsError(dst)
                np.savez_compressed(dst,**kw)
                blob=dst.read_bytes()
                audit=inspect_array_bytes(blob,backend,cfg)
                statuses[backend].append(audit['status']);counts+=1
                pair[backend]={'field_path':str(dst.relative_to(root)),'sha256':source_hash(blob),
                                'audit_status':audit['status'],'audits':{'initial':audit['initial'],'final':audit['final'],
                                'energy_relative_drift':audit['energy_relative_drift'], 'checks':audit['checks']},
                                'trace_summary':run['trace'],'time_refinement':terr,'time_refinement_pass':ref_ok,
                                'wall_seconds':run['seconds'],'refined_wall_seconds':refined['seconds']}
            rows.append({'n':n,**pair})
        results['seeds'][sid]={'source_sha256':src['sha256'],'grids':rows}
    def gate(vals):return 'PASS' if len(vals)==6 and all(v=='PASS' for v in vals) else 'FAIL' if 'FAIL' in vals else 'UNRESOLVED'
    results['gates']['G50']={'status':gate(statuses['cpu']),'reason':'Post-export independently recomputed CPU FP64 divergence/curl/Poisson/energy on 6 files'}
    results['gates']['G51']={'status':gate(statuses['gpu']),'reason':'Post-export independently recomputed Arc FP32 divergence/curl/Poisson/energy on 6 files'}
    results['gates']['G52']={'status':'PASS' if counts==12 else 'FAIL','reason':'All 12 start/final volumes, 3 saved field times and 5 time-summary steps serialized'}
    results['gates']['G53']={'status':'PASS' if len(refinements)==12 and all(refinements) else 'FAIL','reason':'T=0.08 CPU and Arc, 16-vs-32 RK4 time-step comparison for all 6 geometries'}
    results['gates']['G54']={'status':'UNRESOLVED','reason':'No source-native physically derived PKLSA core or separately measured pressure holdout'}
    _store(root,results);return results

def _store(root,data):
    dest=Path(root)/'outputs'/'POST_EXPORT_V043_RESULT.json';dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf8') as f:json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def run_post_export(root,args):
    root=Path(root);verify_all(root)
    cfg,pin=load_protocol(root)
    paths=[Path(a) for a in args] if args else [root/'outputs']
    audited=audit_files(root,paths)
    gates={
       'G49':not_run('POST_EXPORT consumes arrays; GPU code/operator fingerprint available only from GPU_EXTENDED'),
       'G50':audited['gates']['G50'],'G51':audited['gates']['G51'],
       'G52':audited['gates']['G52'],
       'G53':audited['gates']['G53'],
       'G54':audited['gates']['G54']}
    data={'schema':'A065-V043-POST-EXPORT-RESULT-1','v043_prereg_sha256':pin,'gates':gates,
          'external_evidence':audited,'physical_PKLSA':'UNRESOLVED'}
    _store(root,data);return data
