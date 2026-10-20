"""A068 v0.4.3 real 3D torch-XPU FFT/RK4 on Intel Arc; no fallback.

This is separate from the framework's Biot-Savart SYCL/DD32 worker. The
third-party PyTorch XPU wheel must support FFT and device float64. If not,
return unavailable: NEVER label a CPU calculation as GPU execution.
"""
from __future__ import annotations
import numpy as np

def torch_available():
    try:
        import torch
        return {'torch':torch.__version__,'xpu_available':bool(hasattr(torch,'xpu') and torch.xpu.is_available()),
                'xpu_count':int(torch.xpu.device_count()) if hasattr(torch,'xpu') and torch.xpu.is_available() else 0}
    except (ImportError,RuntimeError) as exc:
        return {'xpu_available':False,'reason':str(exc)}

class TorchEuler3D:
    def __init__(self,n,device='xpu',dtype='float64'):
        import torch
        self.torch=torch
        if device=='xpu' and not (hasattr(torch,'xpu') and torch.xpu.is_available()):
            raise RuntimeError('Intel XPU is not available; refusing CPU fallback')
        self.device=device; self.dtype=torch.float64 if dtype=='float64' else torch.float32
        self.n=int(n)
        k=torch.fft.fftfreq(n,d=1./n,device=device,dtype=self.dtype)
        self.k=torch.stack(torch.meshgrid(k,k,k,indexing='ij'))
        k2=torch.sum(self.k*self.k,dim=0)
        self.inv_k2=torch.where(k2>0,1/torch.where(k2>0,k2,torch.ones_like(k2)),torch.zeros_like(k2))
        self.mask=torch.all(torch.abs(self.k)<=n//3,dim=0)
        self.mask[0,0,0]=False
    def from_numpy(self,U):return self.torch.as_tensor(np.asarray(U),device=self.device,dtype=self.dtype)
    def to_numpy(self,U):return U.detach().to('cpu').numpy()
    def fft(self,U):return self.torch.fft.fftn(U,dim=(-3,-2,-1))
    def ifft(self,U):return self.torch.fft.ifftn(U,dim=(-3,-2,-1)).real
    def curl(self,U):
        f=self.fft(U);k=self.k;stack=self.torch.stack
        return self.ifft(1j*stack([k[1]*f[2]-k[2]*f[1],k[2]*f[0]-k[0]*f[2],k[0]*f[1]-k[1]*f[0]]))
    def project(self,U):
        f=self.fft(U)*self.mask
        long=self.torch.sum(self.k*f,dim=0)*self.inv_k2
        return self.ifft((f-self.k*long)*self.mask)
    def cross(self,a,b):
        return self.torch.stack([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])
    def rhs(self,U):return self.project(self.cross(U,self.curl(U)))
    def rk4(self,U,dt):
        k1=self.rhs(U);k2=self.rhs(U+.5*dt*k1)
        k3=self.rhs(U+.5*dt*k2);k4=self.rhs(U+dt*k3)
        return self.project(U+dt*(k1+2*k2+2*k3+k4)/6)

def parity(U0,dt=.04,steps=4,device='xpu',dtype='float64',tolerance=None):
    """Actual independent 3D RK4 trajectory, equal seeds and time steps.

    Full velocity L2 + energy and helicity agreement. GPU device attestation is
    mandatory; CPU path allowed for regression tests only.
    """
    from .euler3d import Euler3D
    n=U0.shape[1]
    ref=Euler3D(n)
    v0=ref.project(np.asarray(U0,dtype=float))
    device_class='GPU_INTEL_XPU' if device=='xpu' else 'CPU_ORACLE_TEST_ONLY'
    try:
        g=TorchEuler3D(n,device=device,dtype=dtype)
        U=g.from_numpy(v0)
        if device=='xpu' and (U.device.type!='xpu'):
            raise RuntimeError(f'Hardware attestation failed: actual device {U.device}')
        V=v0.copy();e0=.5*np.mean(np.sum(V*V,axis=0))
        D=np.empty((0,*V.shape))
        for _ in range(steps):
            V,_=ref.rk4(V,D,dt);U=g.rk4(U,dt)
        gpu=g.to_numpy(U)
        err=float(np.linalg.norm(V-gpu)/max(np.linalg.norm(V),1e-30))
        energy_gpu=.5*np.mean(np.sum(gpu*gpu,axis=0))
        energy_ref=.5*np.mean(np.sum(V*V,axis=0))
        omega_ref=ref.curl(V);omega_gpu=ref.curl(gpu)
        h_ref=np.mean(np.sum(V*omega_ref,axis=0));h_gpu=np.mean(np.sum(gpu*omega_gpu,axis=0))
        thresh=(1e-9 if dtype=='float64' else 5e-4) if tolerance is None else tolerance
        return {'schema':'A068-GPU-TRIPLE-PARITY-v0.4.3','actual_device':str(U.device),
             'actual_backend':f'torch-{device}-{dtype}', 'authority':'MODEL_SOLVER_PARITY_DIAGNOSTIC_ONLY',
             'hardware_gpu_executed':device=='xpu' and U.device.type=='xpu',
             'n':n,'steps':steps,'dt':dt,'relative_velocity_L2':err,
             'relative_energy_difference':float(abs(energy_gpu-energy_ref)/max(abs(energy_ref),1e-30)),
             'relative_helicity_difference':float(abs(h_gpu-h_ref)/max(abs(h_ref),1e-30)),
             'reference_energy_drift':float(abs(energy_ref-e0)/max(abs(e0),1e-30)),
             'tolerance':thresh,'parity_pass':bool(err<thresh),
             'qualification':'SCREENING_ONLY_UNTIL_HARDWARE_AND_GRID_REFINEMENT',
             'must_not_substitute_for_sycl_dd32_framework_selftest':True}
    except (RuntimeError,ImportError,NotImplementedError) as exc:
        return {'schema':'A068-GPU-TRIPLE-PARITY-v0.4.3','actual_backend':'UNAVAILABLE',
                'hardware_gpu_executed':False,'parity_pass':False,'status':'UNAVAILABLE_NO_FALLBACK',
                'error':f'{type(exc).__name__}: {exc}',
                'environment':torch_available(),'requested_device':device}


def gpu_parity_campaign(U0,dt=.04,steps=12,device='xpu'):
    """Run screening FP32 and attempted confirming FP64 on the *same* GPU.

    CPU comparison performed in both lanes, never silently substituted as GPU.
    On Arc FP64 support is device/driver dependent; FP32 can remain screening.
    """
    fp32=parity(U0,dt,steps,device=device,dtype='float32')
    fp64=parity(U0,dt,steps,device=device,dtype='float64')
    ran=bool(fp32.get('hardware_gpu_executed') or fp64.get('hardware_gpu_executed'))
    return {'schema':'A068-GPU-2LANE-v0.4.3','hardware_gpu_executed':ran,
            'actual_backend':f'torch-{device}' if ran else 'UNAVAILABLE',
            'fp32_screen':fp32,'fp64_lane':fp64,
            'fp32_screen_pass':bool(fp32.get('parity_pass') and fp32.get('hardware_gpu_executed')),
            'fp64_parity_pass':bool(fp64.get('parity_pass') and fp64.get('hardware_gpu_executed')),
            'status':'EXECUTED' if ran else 'UNAVAILABLE_NO_FALLBACK',
            'qualification':'FP32_SCREENING_ONLY_FP64_REQUIRES_HARDWARE_PARITY_AND_FRAMEWORK_TESTS'}
