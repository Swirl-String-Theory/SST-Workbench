"""Pinned A075/A077 3D spectral Euler field on a torch device.

Authentic XPU mode is FP32 FFT and FFT-derived Euler, NOT DD32 full Euler.
The optional double-single (DD32) compensation is used for tracer positions only.
CPU-test mode is restricted to testing and cannot attest Intel Arc execution.
"""
from __future__ import annotations
import math
import numpy as np
from .adapters import Adapter

BYTES_PER_CELL_PEAK_BUDGET=960  # conservative planning heuristic, not measured allocation

def estimate_vram_gib(n:int, *, safety:float=1.35)->float:
    return safety*BYTES_PER_CELL_PEAK_BUDGET*n**3/2**30

def device_preflight(device_kind:str='xpu', requested_gib:float=12., n:int=48, *, cpu_test:bool=False):
    import torch
    if device_kind=='xpu':
        if not hasattr(torch,'xpu') or not torch.xpu.is_available():
            raise RuntimeError('XPU_UNAVAILABLE: no Intel torch.xpu device, refusing CPU fallback')
        dev=torch.device('xpu:0')
        prop=torch.xpu.get_device_properties(0)
        memory_bytes=getattr(prop,'total_memory',0)
        total_gib=memory_bytes/2**30 if memory_bytes else None
        # Reserve at least 25% device memory for driver, FFT workspaces and other apps.
        hard=min(requested_gib,0.75*total_gib) if total_gib else requested_gib
        name=getattr(prop,'name','Intel XPU')
        if 'Intel' not in name and 'Arc' not in name:
            raise RuntimeError('UNEXPECTED_XPU_PROVIDER '+name)
    elif device_kind=='cpu-test' and cpu_test:
        dev=torch.device('cpu');hard=requested_gib;total_gib=None;name='CPU_TEST_ONLY_NOT_GPU'
    else:raise RuntimeError('UNSUPPORTED_GPU_PROVIDER: select xpu; cpu-test requires explicit test permission')
    estimate=estimate_vram_gib(n)
    if estimate>hard:
        raise MemoryError(f'VRAM_PREFLIGHT_FAIL n={n} peak_budget={estimate:.3f} GiB > limit={hard:.3f} GiB')
    return dev,{'schema':'SST-XPU-PREFLIGHT-1','device':str(dev),'device_name':name,
                'torch_version':torch.__version__,'device_total_gib':total_gib,
                'user_limit_gib':requested_gib,'effective_limit_gib':hard,
                'planning_budget_gib':estimate,'estimate_is_measurement':False,
                'actual_xpu':device_kind=='xpu','scientific_execution':False}

def _ds_add(a, low, delta):
    """TwoSum and QuickTwoSum-style compensated FP32 addition on the active device.

    DD32 represents accumulated positions only; interpolation and spectral Euler
    remain FP32. Avoid fast-math transformations that discard compensation.
    """
    s=a+delta
    bb=s-a
    e=(a-(s-bb))+(delta-bb)+low
    hi=s+e
    lo=e-(hi-s)
    return hi,lo

class TorchField:
    """Convert a source-pinned solver state and evolve all 3D arrays on device."""
    def __init__(self, cpu:Adapter, device):
        import torch
        self.t=torch;self.device=device;self.cpu=cpu;self.n=cpu.sim.c.n if cpu.provider=='a075' else cpu.sim.n
        self.L=cpu.L;self.dx=cpu.dx;self.provider=cpu.provider
        if cpu.provider=='a075':
            k=np.stack([np.broadcast_to(ki,(self.n,)*3) for ki in cpu.sim.k],axis=-1)
            denom=cpu.sim.k2safe
            mask=cpu.sim.mask
            init=cpu.initial_hat
        else:
            k=np.moveaxis(cpu.sim.k,0,-1)
            denom=cpu.sim.nz
            mask=cpu.sim.mask
            init=np.moveaxis(cpu.initial_hat,0,-1)
        self.k=torch.as_tensor(np.array(k),dtype=torch.float32,device=device)
        self.den=torch.as_tensor(np.array(denom),dtype=torch.float32,device=device)
        self.mask=torch.as_tensor(np.array(mask),dtype=torch.float32,device=device)
        self.uh=self.proj(torch.as_tensor(np.array(init),dtype=torch.complex64,device=device))
        # Do not retain CPU full-grid arrays during GPU evolution; initialization may
        # still need substantial host RAM and cannot be reported as GPU-native.
        cpu.initial_hat=None
        self.grid_origin=-self.L/2+(self.dx/2 if self.provider=='a075' else 0.)
    def fft(self,x):return self.t.fft.fftn(x,dim=(0,1,2))
    def ifft(self,x):return self.t.fft.ifftn(x,dim=(0,1,2)).real
    def proj(self,uh):
        dot=self.t.sum(self.k*uh,dim=-1)/self.den
        out=(uh-self.k*dot[...,None])*self.mask[...,None]
        if self.provider=='a075':out[0,0,0]=0
        return out
    def curl(self,uh):
        k=self.k;t=self.t
        return 1j*t.stack((k[...,1]*uh[...,2]-k[...,2]*uh[...,1],
                           k[...,2]*uh[...,0]-k[...,0]*uh[...,2],
                           k[...,0]*uh[...,1]-k[...,1]*uh[...,0]),dim=-1)
    def rhs(self,uh):
        uh=self.proj(uh)
        u=self.ifft(uh);w=self.ifft(self.curl(uh))
        return self.proj(self.fft(self.t.cross(u,w,dim=-1)))
    def physical(self,uh):return self.ifft(uh)
    def interpolate(self,uh,pos):
        # All velocity interpolation, grid indexing and periodic wrap occur on GPU.
        u=self.physical(uh);t=self.t;n=self.n
        q=(pos-self.grid_origin)/self.dx
        lo=t.floor(q).to(t.int64);f=q-lo.to(t.float32)
        acc=t.zeros_like(pos,dtype=t.float32)
        for i in (0,1):
            for j in (0,1):
                for k in (0,1):
                    ii=(lo[:,0]+i)%n;jj=(lo[:,1]+j)%n;kk=(lo[:,2]+k)%n
                    w=(f[:,0] if i else 1-f[:,0])*(f[:,1] if j else 1-f[:,1])*(f[:,2] if k else 1-f[:,2])
                    acc=acc+u[ii,jj,kk]*w[:,None]
        return acc
    def diagnostics(self,uh):
        t=self.t;u=self.ifft(uh);w=self.ifft(self.curl(uh))
        e=(.5*t.sum(u*u)*self.dx**3)
        h=t.sum(u*w)*self.dx**3
        z=(.5*t.sum(w*w)*self.dx**3)
        div=self.ifft(1j*t.sum(self.k*uh,dim=-1))
        mag=t.sqrt(t.sum(u*u,dim=-1))
        return {'energy':float(e.item()),'helicity':float(h.item()),'enstrophy':float(z.item()),
                'divergence_Linf':float(t.max(t.abs(div)).item()),'max_velocity':float(t.max(mag).item())}
    def perturb(self,uh,relative,seed,filter_length=.3):
        if relative<=0:return uh
        t=self.t
        generator=t.Generator(device=str(self.device));generator.manual_seed(int(seed))
        noise=t.randn((self.n,self.n,self.n,3),dtype=t.float32,device=self.device,generator=generator)
        noisehat=self.proj(self.fft(noise))
        filterfactor=t.exp(-.5*filter_length**2*t.sum(self.k*self.k,dim=-1))
        noisehat=self.proj(noisehat*filterfactor[...,None])
        p=t.linalg.vector_norm(noisehat).item();q=t.linalg.vector_norm(uh).item()
        if p<=0 or q<=0:raise ValueError('DEGENERATE_GPU_PERTURBATION')
        return self.proj(uh+float(relative*q/p)*noisehat)
    def step(self,uh,xhi,xlo,dt,dd32_tracer):
        # RK4 reference algorithm; no low-storage model substitution.
        def addpos(xh,xl,v,coeff):
            delta=(float(coeff)*v).to(self.t.float32)
            return _ds_add(xh,xl,delta) if dd32_tracer else (xh+delta,self.t.zeros_like(xh))
        k1=self.rhs(uh);v1=self.interpolate(uh,xhi+xlo)
        q2=self.proj(uh+.5*dt*k1);xh2,xl2=addpos(xhi,xlo,v1,.5*dt)
        k2=self.rhs(q2);v2=self.interpolate(q2,xh2+xl2)
        q3=self.proj(uh+.5*dt*k2);xh3,xl3=addpos(xhi,xlo,v2,.5*dt)
        k3=self.rhs(q3);v3=self.interpolate(q3,xh3+xl3)
        q4=self.proj(uh+dt*k3);xh4,xl4=addpos(xhi,xlo,v3,dt)
        k4=self.rhs(q4);v4=self.interpolate(q4,xh4+xl4)
        result=self.proj(uh+dt*(k1+2*k2+2*k3+k4)/6.)
        v=(v1+2*v2+2*v3+v4)/6.
        xx,xy=addpos(xhi,xlo,v,dt)
        return result,xx,xy
