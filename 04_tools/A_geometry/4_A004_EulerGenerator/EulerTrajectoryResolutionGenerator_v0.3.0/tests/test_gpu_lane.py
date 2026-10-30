"""GPU lane regressions: CPU-test math is NOT evidence of XPU execution."""
from __future__ import annotations
import numpy as np, pytest
import torch
from resolver.gpu_core import TorchField,device_preflight,estimate_vram_gib,_ds_add

class TinySim:
    def __init__(self,n=16,L=8):
        self.n=n;self.L=L
        d=L/n
        axes=2*np.pi*np.fft.fftfreq(n,d=d)
        self.k=np.stack(np.meshgrid(axes,axes,axes,indexing='ij'))
        kk=(self.k**2).sum(axis=0)
        self.nz=np.where(kk>0,kk,1)
        self.mask=np.ones((n,n,n),dtype=bool)

class TinyAdapter:
    provider='a077'
    def __init__(self,n=16,L=8,velocity=(.125,0.,0.)):
        self.sim=TinySim(n,L);self.dx=L/n;self.L=L
        u=np.zeros((3,n,n,n));u[:]=np.asarray(velocity)[:,None,None,None]
        self.initial_hat=np.fft.fftn(u,axes=(-3,-2,-1))

def test_gpu_memory_estimate_monotonic_and_blocks_large_grid():
    assert estimate_vram_gib(96)<estimate_vram_gib(170)<estimate_vram_gib(260)
    with pytest.raises(MemoryError,match='VRAM_PREFLIGHT_FAIL'):
        device_preflight('cpu-test',.5,260,cpu_test=True)

def test_cpu_fallback_forbidden():
    with pytest.raises(RuntimeError,match='UNSUPPORTED_GPU_PROVIDER'):
        device_preflight('cpu-test',4,16,cpu_test=False)

def test_dd32_position_accumulator_retains_subulp_increment():
    x=torch.tensor([[10000.]],dtype=torch.float32)
    lo=torch.zeros_like(x)
    delta=torch.tensor([[0.0001]],dtype=torch.float32)
    for _ in range(100):x,lo=_ds_add(x,lo,delta)
    assert abs(float(x.item()+lo.item())-10000.01)<2e-6
    naive=torch.tensor([[10000.]],dtype=torch.float32)
    for _ in range(100):naive+=delta
    assert float(naive.item())==10000.0

def test_torch_cpu_uniform_field_stationary_rhs_and_tracer_advects():
    f=TorchField(TinyAdapter(),torch.device('cpu'))
    x=torch.tensor([[0.2,0.3,-0.5]],dtype=torch.float32)
    low=torch.zeros_like(x)
    initial=f.uh
    assert torch.linalg.vector_norm(f.rhs(initial)).item()<1e-4
    u,x,l=f.step(initial,x,low,dt=.1,dd32_tracer=True)
    assert abs(float(x[0,0]+l[0,0])-(.2+.0125))<1e-6
    assert torch.linalg.vector_norm(f.rhs(u)).item()<1e-4

def test_cpu_test_is_not_real_xpu():
    dev,info=device_preflight('cpu-test',4,16,cpu_test=True)
    assert str(dev)=='cpu' and not info['actual_xpu'] and not info['scientific_execution']

def test_grid_kspace_layouts_from_both_providers_are_supported():
    class FakeA075:
        provider='a075'
        def __init__(self,n=16):
            self.L=8.;self.dx=.5
            self.sim=type('Fake',(),{})();self.sim.c=type('Conf',(),{'n':n})()
            axes=2*np.pi*np.fft.fftfreq(n,d=.5)
            self.sim.k=np.meshgrid(axes,axes,axes,indexing='ij')
            k2=sum(k*k for k in self.sim.k)
            self.sim.k2safe=np.where(k2>0,k2,1.)
            self.sim.mask=np.ones((n,n,n))
            self.initial_hat=np.zeros((n,n,n,3),dtype=np.complex128)
    f=TorchField(FakeA075(),torch.device('cpu'))
    assert f.uh.shape==(16,16,16,3)
    assert float(torch.linalg.vector_norm(f.rhs(f.uh)))==0.
