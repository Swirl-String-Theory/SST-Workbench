"""A065-v0.4.1: actual SYCL XPU *volume FFT/RK4* implementation via Intel dpnp.

The frozen v1.0.10 SYCL-worker is separately certified for regularized
Biot-Savart; its DD32 parity DOES NOT certify dpnp FFT/Euler. This new lane
must prove its own device, precision, trajectory, pressure, and curl parity.

Fail-closed: requires real Intel Arc A770 Level Zero SYCL GPU, not iGPU, CPU,
or NumPy fallback. Uses device-resident dpnp arrays for every RK4 stage and FFT.
The assumed Gaussian geometry-to-vorticity initialization runs on host FP64,
then initial projected velocity is transferred only once onto the device.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import numpy as np

from .euler3d_v040 import integrate as reference_euler, taylor_green
from .volume_v040 import preflight as v040_preflight, selected_sources, relerr
from .native_core_v038 import gaussian_vorticity, spectral_helmholtz

class GPUUnavailable(RuntimeError): pass
class GPUImplementationError(RuntimeError): pass


def require_arc():
    try:
        import dpctl, dpnp
    except ImportError as exc:
        raise GPUUnavailable('MISSING_DPNP_DPCTL: install compatible Intel dpnp and dpctl into active venv') from exc
    try:
        candidates=list(dpctl.get_devices())
        arc=[d for d in candidates if bool(getattr(d,'is_gpu',False))
             and 'a770' in str(getattr(d,'name','')).lower()
             and 'level_zero' in str(getattr(d,'backend','')).lower()]
        if len(arc)!=1:
            raise GPUUnavailable('ARC_A770_LEVEL_ZERO_REQUIRED: found '+repr([
                {'device':str(getattr(d,'name','?')),'gpu':str(getattr(d,'is_gpu',None)),
                 'backend':str(getattr(d,'backend',None))} for d in candidates]))
        q=dpctl.SyclQueue(arc[0])
        if not q.sycl_device.is_gpu or 'a770' not in q.sycl_device.name.lower():
            raise GPUUnavailable('SYCL_QUEUE_NOT_ARC_A770')
        return dpnp,q,{'device_name':q.sycl_device.name,
            'backend':str(q.sycl_device.backend),
            'has_native_fp64':bool(getattr(q.sycl_device,'has_aspect_fp64',False)),
            'sycl_selector':'EXPLICIT_INTEL_ARC_A770_LEVEL_ZERO',
            'dpnp_version':getattr(dpnp,'__version__','unknown'),
            'dpctl_version':getattr(dpctl,'__version__','unknown')}
    except GPUUnavailable: raise
    except Exception as exc:
        raise GPUUnavailable('ARC_DEVICE_SELECTION_FAILED: '+str(exc)) from exc


def _euler_generic(xp,u0,L,T,steps,*,queue=None):
    """Same Fourier rotational Euler operator under NumPy or dpnp.

    No silent host conversion occurs inside the timestep loop. All wavevectors
    are derived from the same numpy integer fftfreq convention and moved once.
    """
    if not isinstance(steps,int) or steps<1 or T<=0 or L<=0:raise ValueError('INVALID_EULER_PARAMS')
    if u0.ndim!=4 or u0.shape[0]!=3 or len(set(u0.shape[1:]))!=1:raise ValueError('INVALID_EULER_SHAPE')
    n=u0.shape[1]
    isgpu=queue is not None
    float_dt=np.float32 if isgpu else np.float64
    if isgpu:
        def hostarr(x):return xp.asarray(x,sycl_queue=queue,usm_type='device')
    else:
        def hostarr(x):return np.asarray(x)
    k=(2*np.pi*np.fft.fftfreq(n,d=L/n)).astype(float_dt)
    modes=np.fft.fftfreq(n)*n
    kx=hostarr(k.reshape(n,1,1));ky=hostarr(k.reshape(1,n,1));kz=hostarr(k.reshape(1,1,n))
    k2=kx*kx+ky*ky+kz*kz
    inv=xp.where(k2>0,1/xp.where(k2>0,k2,1),0)
    mask1=(np.abs(modes)<n/3)
    mask_cpu=mask1[:,None,None]&mask1[None,:,None]&mask1[None,None,:]
    mask_cpu[0,0,0]=False
    mask=hostarr(mask_cpu)
    def project(U):
        q=(kx*U[0]+ky*U[1]+kz*U[2])*inv
        return xp.stack((U[0]-kx*q,U[1]-ky*q,U[2]-kz*q),axis=0)*mask
    def curl(U):
        return xp.stack((1j*(ky*U[2]-kz*U[1]),
                         1j*(kz*U[0]-kx*U[2]),
                         1j*(kx*U[1]-ky*U[0])),axis=0)
    def cross(u,w):
        return xp.stack((u[1]*w[2]-u[2]*w[1],
                         u[2]*w[0]-u[0]*w[2],
                         u[0]*w[1]-u[1]*w[0]),axis=0)
    fft=lambda a:xp.fft.fftn(a,axes=(-3,-2,-1))
    ifft=lambda a:xp.fft.ifftn(a,axes=(-3,-2,-1)).real
    def rhs(U):
        u=ifft(U);omega=ifft(curl(U))
        return project(fft(cross(u,omega)))
    U=project(fft(u0))
    dt=float_dt(T/steps)
    begin=time.perf_counter()
    for _ in range(steps):
        k1=rhs(U)
        k2h=rhs(project(U+dt*k1/2))
        k3=rhs(project(U+dt*k2h/2))
        k4=rhs(project(U+dt*k3))
        U=project(U+dt*(k1+2*k2h+2*k3+k4)/6)
    u=ifft(U);omega=ifft(curl(U))
    ch=fft(cross(u,omega))
    qhat=-1j*(kx*ch[0]+ky*ch[1]+kz*ch[2])*inv
    pressure=ifft(qhat)-0.5*xp.sum(u*u,axis=0)
    pressure=pressure-xp.mean(pressure)
    div=ifft(1j*(kx*U[0]+ky*U[1]+kz*U[2]))
    # Device synchronization for honest kernel wall time and complete outputs.
    if isgpu:
        queue.wait()
        to_host=xp.asnumpy
    else:to_host=np.asarray
    elapsed=time.perf_counter()-begin
    return {'u':to_host(u),'omega':to_host(omega),'p':to_host(pressure),
            'div_u_rms':float(np.sqrt(np.mean(to_host(div)**2))),
            'wall_seconds':elapsed,'numeric_precision':'FP32' if isgpu else 'FP64',
            'actual_backend':'SYCL_DPNP_FFT' if isgpu else 'NUMPY_FFT'}


def gpu_euler(u0,L,T,steps,*,device=None):
    xp,q,dev=(device if device is not None else require_arc())
    try:
        d=xp.asarray(np.asarray(u0,dtype=np.float32),sycl_queue=q,usm_type='device')
        result=_euler_generic(xp,d,L,T,steps,queue=q)
    except GPUUnavailable:raise
    except Exception as exc:
        raise GPUImplementationError('ARC_EULER_KERNEL_ERROR '+repr(exc)) from exc
    result['device']=dev
    return result


def cpu_generic(u0,L,T,steps):
    return _euler_generic(np,np.asarray(u0,dtype=np.float64),L,T,steps)


def parity(gpu,cpu):
    return {field:relerr(gpu[field],cpu[field]) for field in ('u','omega','p')}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight(root):
    root=Path(root)
    raw=(root/'preregistration'/'ARC_GPU_V041.json').read_bytes()
    pin=(root/'preregistration'/'ARC_GPU_V041.sha256').read_text().strip()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('V041_PREREGISTRATION_TAMPERED')
    cfg=json.loads(raw);old,oldsha=v040_preflight(root)
    if cfg['v040_prereg_sha256']!=oldsha or cfg['grids']!=old['grids'] or cfg['assumed_gaussian_a']!=old['gaussian_a_assumed']:
        raise ValueError('V041_V040_CONTRACT_CHANGED')
    return cfg,old,pin


def _status_not_executed(reason):
    return {'status':'NOT_RUN_PREREQUISITE','reason':reason,'execution_status':'NOT_EXECUTED'}


def run(root,*,save_fields=False,smoke_only=False,persist=True):
    root=Path(root);cfg,prior,pin=preflight(root)
    results={'schema':'A065-ARC-EULER-V041-1','version':'v0.4.1','prereg_sha256':pin,
             'v040_frozen':True,'source_class':'GPU_NUMERICAL_EULER_ASSUMED_GAUSSIAN_NOT_PHYSICAL_PKLSA',
             'physical_pklsa_qualified':False,'independent_physical_holdout':False,
             'backend':'ARC_A770_LEVEL_ZERO_DPNP_FP32','gates':{},'taylor_green':{},'a003':{}}
    try:device=require_arc()
    except GPUUnavailable as exc:
        results['gates']={k:_status_not_executed(str(exc)) for k in ('G43','G44','G45','G46','G47')}
        results['gates']['G48']={'status':'UNRESOLVED','reason':'No independently calibrated PKLSA physical vortex core / heldout velocity and pressure'}
        results['device_error']=str(exc)
        if persist:_save(root,results)
        return results
    xp,q,dev=device;results['device']=dev
    results['gates']['G43']={'status':'PASS','metrics':dev,'reason':'Explicit Arc A770 Level Zero GPU queue; no fallback'}
    control=cpu_generic(taylor_green(cfg['smoke_n']),2*np.pi,cfg['smoke_T'],cfg['smoke_steps'])
    gpu=gpu_euler(taylor_green(cfg['smoke_n']),2*np.pi,cfg['smoke_T'],cfg['smoke_steps'],device=device)
    errors=parity(gpu,control)
    results['taylor_green']={'grid':cfg['smoke_n'],'error':errors,'gpu_div_u_rms':gpu['div_u_rms'],
                             'gpu_seconds':gpu['wall_seconds'],'cpu_seconds':control['wall_seconds']}
    passes=all(errors[k]<=cfg['parity_tolerance'][k] for k in errors) and gpu['div_u_rms']<=cfg['divergence_tolerance']
    results['gates']['G44']={'status':'PASS' if passes else 'FAIL','metrics':results['taylor_green'],
       'reason':'Same operator/initial data GPU FP32 vs independent NumPy FP64 Taylor-Green (not a PKLSA physical test)'}
    if smoke_only:
        for g in ('G45','G46','G47'):results['gates'][g]=_status_not_executed('SMOKE_ONLY_NO_A003_CAMPAIGN')
    else:
        sources,missing=selected_sources(root,prior)
        if missing:
            for g in ('G45','G46','G47'):results['gates'][g]=_status_not_executed(missing)
        else:
            allgood=True;pgood=True;fields=[]
            for sid,s in sources.items():
                rr=[]
                for n in cfg['grids']:
                    # Independently generated for each grid from same authenticated A003 geometry.
                    om=gaussian_vorticity(s['xyz'],n,prior['box_length'],prior['gaussian_a_assumed'],prior['gamma_assumed'])
                    init=spectral_helmholtz(om,prior['box_length'],prior['density'])['u']
                    fp64=reference_euler(init,prior['box_length'],prior['euler_T'],prior['euler_steps'],prior['density'])
                    xpu=gpu_euler(init,prior['box_length'],prior['euler_T'],prior['euler_steps'],device=device)
                    errors=parity(xpu,fp64)
                    r={'grid':n,'source_sha256':s['sha256'],'u_error':errors['u'],
                       'omega_error':errors['omega'],'p_error':errors['p'],
                       'gpu_div_u_rms':xpu['div_u_rms'],'gpu_wall_seconds':xpu['wall_seconds'],
                       'source_class':'A003_ASSUMED_GAUSSIAN_IVP_NOT_INDEPENDENT_PHYSICAL_PKLSA'}
                    pass_other=all(errors[k]<=cfg['parity_tolerance'][k] for k in ('u','omega')) and xpu['div_u_rms']<=cfg['divergence_tolerance']
                    pass_pressure=errors['p']<=cfg['parity_tolerance']['p']
                    allgood=allgood and pass_other
                    pgood=pgood and pass_pressure
                    if save_fields:
                        dst=root/'outputs'/f'V041_{sid}_N{n}_ARC_FP32.npz'
                        dst.parent.mkdir(parents=True,exist_ok=True)
                        if dst.exists():raise FileExistsError(dst)
                        np.savez_compressed(dst,u=xpu['u'],omega=xpu['omega'],p=xpu['p'],
                           source_sha256=np.array(s['sha256']),time=np.float64(prior['euler_T']),
                           assumed_core=np.float64(prior['gaussian_a_assumed']),
                           source_class=np.array('GPU_EULER_GAUSSIAN_GEOMETRY_SEEDED_NOT_PKLSA'))
                        r['field_sha256']=sha(dst);r['field_path']=str(dst.relative_to(root)).replace(chr(92),'/')
                    rr.append(r)
                results['a003'][sid]={'source_sha256':s['sha256'],'grids':rr}
            results['gates']['G45']={'status':'PASS' if allgood else 'FAIL','reason':'A003 trajectories GPU FP32 vs NumPy FP64 at frozen 48/64/96','metrics':{'seeds':list(results['a003']),'grids':cfg['grids']}}
            results['gates']['G46']={'status':'PASS' if pgood else 'FAIL','reason':'Periodically reconstructed Euler pressure GPU FP32 vs CPU FP64; no independent physical pressure measurement'}
            results['gates']['G47']={'status':'PASS' if (allgood and pgood) else 'FAIL','reason':'Full three-resolution dual-backend result/manifest with explicit A770 identity; source-hash fingerprint required'}
    results['gates']['G48']={'status':'UNRESOLVED','reason':'Gaussian initialization from A003 geometry and dependent numerical pressure cannot qualify native PKLSA physics'}
    if persist:_save(root,results)
    return results


def _save(root,r):
    dest=root/'outputs'/'ARC_GPU_V041_RESULT.json';dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x',encoding='utf8') as f:json.dump(r,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
