"""True torch-XPU Euler spectral implementation; optional torch CPU parity sandbox.

Array state, RK4, spectral derivatives, FFT, Leray projection, pressure and
local window flux are computed on the selected torch device.  The initial
vorticity deposition uses the common CPU input constructor, and only scalar
ledger values and marker samples transfer back during the run.
"""
from __future__ import annotations
from dataclasses import replace
import numpy as np
from .euler3d import Euler3D

class TorchEuler3D(Euler3D):
    def __init__(self,cfg):
        import torch
        self.torch=torch
        if cfg.backend == 'arc-xpu':
            if not hasattr(torch,'xpu') or not torch.xpu.is_available():
                raise RuntimeError('XPU_UNAVAILABLE: install an XPU-enabled PyTorch and Intel GPU driver; no CPU fallback')
            self.device=torch.device('xpu')
        elif cfg.backend=='torch-cpu-reference':
            self.device=torch.device('cpu')
        else:raise RuntimeError('Unsupported torch Euler backend')
        native_cfg=replace(cfg,backend='cpu-scipy-fft')
        super().__init__(native_cfg)
        self._init_cpu=Euler3D(native_cfg)
        self.c=cfg
        ftype=torch.float64 if cfg.backend=='torch-cpu-reference' or cfg.gpu_precision=='fp64' else torch.float32
        self.float_dtype=ftype
        self.complex_dtype=torch.complex128 if ftype==torch.float64 else torch.complex64
        self.k=tuple(torch.as_tensor(a,dtype=ftype,device=self.device) for a in self.k)
        self.k2safe=torch.as_tensor(self.k2safe,dtype=ftype,device=self.device)
        self.mask=torch.as_tensor(self.mask,dtype=ftype,device=self.device)
        self.X=tuple(torch.as_tensor(a,dtype=ftype,device=self.device) for a in self.X)
    def to_device(self,x):
        return self.torch.as_tensor(np.asarray(x),dtype=self.complex_dtype,device=self.device)
    def initial_velocity(self):
        a,prov=self._init_cpu.initial_velocity()
        return self.to_device(a),prov
    def fft(self,x):return self.torch.fft.fftn(x,dim=(0,1,2))
    def ifft(self,x):return self.torch.fft.ifftn(x,dim=(0,1,2)).real
    def project(self,uh):
        dot=sum(self.k[j]*uh[...,j] for j in range(3))/self.k2safe
        out=self.torch.stack([uh[...,j]-self.k[j]*dot for j in range(3)],dim=-1)
        out=out*self.mask[...,None]
        out[0,0,0,:]=0
        return out
    def curl_hat(self,uh):
        k=self.k
        return 1j*self.torch.stack([k[1]*uh[...,2]-k[2]*uh[...,1],
                                     k[2]*uh[...,0]-k[0]*uh[...,2],
                                     k[0]*uh[...,1]-k[1]*uh[...,0]],dim=-1)
    def rhs(self,uh):
        uh=self.project(uh)
        u=self.ifft(uh);o=self.ifft(self.curl_hat(uh))
        return self.project(self.fft(self.torch.cross(u,o,dim=-1)))
    def pressure(self,uh):
        u=self.ifft(uh);o=self.ifft(self.curl_hat(uh))
        b=self.fft(self.torch.cross(u,o,dim=-1))
        qhat=-1j*sum(self.k[j]*b[...,j] for j in range(3))/self.k2safe
        qhat[0,0,0]=0
        return self.c.rho*(self.ifft(qhat)-.5*self.torch.sum(u*u,dim=-1))
    def window(self,center):
        t=self.torch;c=self.c
        W=t.ones_like(self.X[0]);center=np.asarray(center)
        for j in range(3):
            d=t.remainder(self.X[j]-float(center[j])+c.box/2,c.box)-c.box/2
            W=W*.5*(1-t.tanh((t.abs(d)-c.window_halfwidth)/c.window_edge))
        grad=t.stack([self.ifft(1j*self.k[j]*self.fft(W)) for j in range(3)],dim=-1)
        return W,grad
    def stats(self,uh,center,w):
        t=self.torch;c=self.c;dx3=self.dx**3
        u=self.ifft(uh);omega=self.ifft(self.curl_hat(uh));p=self.pressure(uh)
        e=c.rho*.5*t.sum(u*u,dim=-1)
        W,grad=self.window(center)
        w=t.as_tensor(w,dtype=self.float_dtype,device=self.device)
        flux=t.sum(t.sum(grad*((e+p)[...,None]*u-e[...,None]*w),dim=-1))*dx3
        div=self.ifft(sum(1j*self.k[j]*uh[...,j] for j in range(3)))
        vals={'E_global':t.sum(e)*dx3,'E_window':t.sum(W*e)*dx3,'rhs_flux':flux,
              'omega_window_l1':t.sum(W*t.linalg.vector_norm(omega,dim=-1))*dx3,
              'omega_z2_window':t.sum(W*omega[...,2]**2)*dx3,
              'div_rms':t.sqrt(t.mean(div**2)),
              'max_speed':t.max(t.linalg.vector_norm(u,dim=-1))}
        d={key:float(v.item()) for key,v in vals.items()}
        d['cfl']=d['max_speed']*c.dt/self.dx
        return d
    def probe_u(self,uh,center):
        t=self.torch;u=self.ifft(uh)
        grid=(np.asarray(center)+self.c.box/2)/self.dx-.5
        idx=np.floor(grid).astype(int);frac=grid-idx;out=np.zeros(3)
        for a in (0,1):
          for b in (0,1):
           for c in (0,1):
            ind=(idx+np.array([a,b,c]))%self.c.n
            wt=np.prod(np.where(np.array([a,b,c])==1,frac,1-frac))
            out+=wt*u[tuple(ind)].detach().cpu().numpy()
        return out
    def global_energy_hat(self,uh):
        return float((.5*self.c.rho*self.dx**3/self.c.n**3 *
                      self.torch.sum(self.torch.abs(uh)**2)).item())
    def adapt_metrics(self,uh):
        u=self.ifft(uh);o=self.ifft(self.curl_hat(uh));t=self.torch
        return (float(t.max(t.linalg.vector_norm(u,dim=-1)).item()),
                float(t.max(t.linalg.vector_norm(o,dim=-1)).item()))
