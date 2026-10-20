"""Reference TSSP GPE; not an Euler/PKLSA solver.
Dimensionless: i psi_t = -(1/2) Delta psi + g(|psi|^2-n0)psi.
Periodic grid, dt scaled by chosen time unit, L by chosen length unit.
"""
from __future__ import annotations
import math
import numpy as np


def _initial(n, L, modes=(2, 1), amp=1.0):
    axes=[np.arange(n, dtype=np.float64) * (L/n) for _ in modes]
    phase=sum(2*np.pi*m*x.reshape([n if i==j else 1 for i in range(len(modes))])/L
              for j,(m,x) in enumerate(zip(modes,axes)))
    return amp * np.exp(1j*phase)


def _k2_numpy(shape,L):
    kk=np.meshgrid(*(2*np.pi*np.fft.fftfreq(s,d=L/s) for s in shape), indexing='ij')
    return sum(k*k for k in kk)


def solve_numpy(psi0, *, g=0.7,n0=1.0,L=2*math.pi,dt=0.001,steps=50):
    psi=np.array(psi0,dtype=np.complex128,copy=True)
    kinetic=np.exp(-0.5j*dt*_k2_numpy(psi.shape,L))
    for _ in range(steps):
        psi*=np.exp(-0.5j*dt*g*(np.abs(psi)**2-n0))
        psi=np.fft.ifftn(np.fft.fftn(psi)*kinetic)
        psi*=np.exp(-0.5j*dt*g*(np.abs(psi)**2-n0))
    return psi


def norm(psi):
    return float(np.vdot(psi,psi).real)


def plane_wave_test(n=32,L=2*math.pi,steps=32,dt=0.005,g=0.7):
    modes=(2,1);psi0=_initial(n,L,modes)
    final=solve_numpy(psi0,L=L,dt=dt,steps=steps,g=g)
    # n0=1, amplitude=1 => nonlinear term vanishes
    omega=0.5*sum((2*math.pi*m/L)**2 for m in modes)
    exact=psi0*np.exp(-1j*omega*steps*dt)
    err=float(np.linalg.norm(final-exact)/np.linalg.norm(exact))
    drift=abs(norm(final)/norm(psi0)-1)
    return {'plane_wave_relative_l2':err,'norm_relative_drift':drift,'n':n,'steps':steps,'dt':dt,
            'expected_omega':omega,'units':'dimensionless'}


def convergence_test(n=24,final_time=0.12,g=0.8):
    # Non-plane initial state ensures noncommuting operators. Compare against dt/8 surrogate,
    # not analytic truth. Use fixed final time and identical spatial grid.
    L=2*math.pi
    x=np.arange(n)*L/n
    X,Y=np.meshgrid(x,x,indexing='ij')
    psi0=(1.0+0.16*np.cos(X)+0.11*np.sin(2*Y))*np.exp(0.32j*np.sin(X+Y))
    steps=(8,16,32,128)
    vals=[solve_numpy(psi0,L=L,dt=final_time/s,steps=s,g=g) for s in steps]
    reference=vals[-1]
    errs=[float(np.linalg.norm(v-reference)/np.linalg.norm(reference)) for v in vals[:3]]
    # effective convergence order from successive errors, reference error nonzero
    orders=[math.log(errs[i]/errs[i+1],2) if errs[i+1]>0 else math.inf for i in range(2)]
    return {'steps':list(steps),'errors_l2':errs,'orders':orders,'min_order':min(orders),
            'reference_kind':'fine-grid numerical surrogate','units':'dimensionless'}


def reversibility_test(n=32,steps=24,dt=0.003,g=0.7):
    x=np.arange(n)*2*np.pi/n
    X,Y=np.meshgrid(x,x,indexing='ij')
    psi0=(1+0.1*np.cos(X)+0.09*np.sin(Y))*np.exp(1j*0.35*np.sin(X-Y))
    fwd=solve_numpy(psi0,steps=steps,dt=dt,g=g)
    bwd=solve_numpy(fwd,steps=steps,dt=-dt,g=g)
    return {'roundtrip_relative_l2':float(np.linalg.norm(bwd-psi0)/np.linalg.norm(psi0)),
            'norm_relative_drift':abs(norm(fwd)/norm(psi0)-1), 'units':'dimensionless'}


def solve_torch_xpu(psi0, *, g=0.7, n0=1., L=2*math.pi, dt=0.001, steps=50):
    import torch
    if not hasattr(torch,'xpu') or not torch.xpu.is_available():
        raise RuntimeError('PyTorch XPU is unavailable: Intel Arc device, XPU wheel, or driver missing')
    device=torch.device('xpu')
    # Intentional FP32 on Intel Arc: screening only (not FP64 certification).
    psi=torch.as_tensor(np.asarray(psi0,dtype=np.complex64),dtype=torch.complex64,device=device).clone()
    k=np.meshgrid(*(2*np.pi*np.fft.fftfreq(s,d=L/s) for s in psi.shape),indexing='ij')
    k2=torch.as_tensor(sum(a*a for a in k),device=device,dtype=torch.float32)
    kinetic=torch.exp((-0.5j*dt)*k2)
    for _ in range(steps):
        psi=psi*torch.exp((-0.5j*dt*g)*(torch.abs(psi)**2-n0))
        psi=torch.fft.ifftn(torch.fft.fftn(psi)*kinetic)
        psi=psi*torch.exp((-0.5j*dt*g)*(torch.abs(psi)**2-n0))
    torch.xpu.synchronize()
    return psi.cpu().numpy(), str(torch.xpu.get_device_name(0)),str(torch.__version__)


def ring_seed(n=40,L=2*math.pi,R=1.25,xi=0.22):
    # Illustrative 3D closed ring phase singularity, not a relaxed stationary GP vortex.
    x=(np.arange(n)-n//2)*L/n
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    q=np.sqrt(X*X+Y*Y)-R
    d=np.sqrt(q*q+Z*Z)
    return np.tanh(d/(math.sqrt(2)*xi))*np.exp(1j*np.arctan2(Z,q))


def xpu_parity(n=32,steps=24,dt=0.002,full3d=False):
    import torch
    psi=_initial(n,2*math.pi,(2,1))
    cpu=solve_numpy(psi,steps=steps,dt=dt)
    gpu,name,version=solve_torch_xpu(psi,steps=steps,dt=dt)
    err=float(np.linalg.norm(gpu.astype(np.complex128)-cpu)/np.linalg.norm(cpu))
    gpu_norm_drift=abs(norm(gpu)/norm(psi)-1)
    result={'gpu_cpu_relative_l2':err,'gpu_norm_relative_drift':gpu_norm_drift,
            'requested_backend':'pytorch-xpu-fp32','actual_backend':'pytorch-xpu-fp32',
            'device_name':name,'torch_version':version,'n':n,'steps':steps,
            'reference_kind':'independent numpy FFT fp64 implementation', 'units':'dimensionless'}
    if full3d:
        ring=ring_seed(n=40)
        cr=solve_numpy(ring,steps=8,dt=0.0015)
        gr,_,_=solve_torch_xpu(ring,steps=8,dt=0.0015)
        result['ring3d']={'gpu_cpu_relative_l2':float(np.linalg.norm(gr-cr)/np.linalg.norm(cr)),
                          'n':40,'steps':8,'seed_kind':'illustrative_closed_ring_not_relaxed_or_validated_topology'}
    return result
