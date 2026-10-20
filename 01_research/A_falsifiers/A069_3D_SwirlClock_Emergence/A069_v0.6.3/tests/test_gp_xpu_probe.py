import pathlib,sys,types
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import torch
import pytest
import gp_xpu_probe as p


def test_synthetic_is_3d_complex():
    z=p.synthetic_initial(16,10)
    assert z.shape==(16,16,16) and z.dtype==np.complex128
    assert np.abs(z).std()>0.005
    assert np.angle(z).std()>0.005


def test_torch_numpy_3d_fft_cpu_parity():
    z=p.synthetic_initial(16,10)
    a=torch.from_numpy(z.astype(np.complex64))
    b=torch.fft.fftn(a).numpy().astype(np.complex128)
    c=np.fft.fftn(z.astype(np.complex64).astype(np.complex128))
    assert p.relative_l2(b,c)<3e-6


def test_strang_cpu_reference():
    n=16; box=10;dt=.002; mu=6.377551
    z=p.synthetic_initial(n,box)
    k=torch_k=p.torch_k2(torch,n,box,torch.device('cpu'))
    kin=torch.exp((-0.5j*dt)*k)
    t=torch.from_numpy(z.astype(np.complex64))
    s=p.torch_step(torch,t,kin,dt,mu).numpy()
    ref=p.numpy_step(z,p.kinetic_numpy(n,box,dt),dt,mu)
    assert p.relative_l2(s.astype(np.complex128),ref)<3e-6


def test_explicit_xpu_must_fail_on_absent_gpu(monkeypatch):
    class FakeXpu:
        def is_available(self):return False
    class FakeTorch:
        xpu=FakeXpu()
    with pytest.raises(RuntimeError,match='NO_XPU'):
        p.select_torch_device(FakeTorch(),'xpu','A770')


def test_device_no_integrated_gpu_fallback():
    class FakeXpu:
        def is_available(self):return True
        def device_count(self):return 1
        def get_device_name(self,i):return 'Intel UHD 770'
    class FakeTorch:
        xpu=FakeXpu()
        def device(self,v):return v
    with pytest.raises(RuntimeError,match='EXPECTED_GPU_NOT_FOUND'):
        p.select_torch_device(FakeTorch(),'xpu','A770')


def test_bulk_mass_drift_cpu():
    n=16;z=p.synthetic_initial(n,10);mu=6.377551;dt=.003
    initial=np.sum(abs(z)**2)
    for _ in range(10):z=p.numpy_step(z,p.kinetic_numpy(n,10,dt),dt,mu)
    assert abs(np.sum(abs(z)**2)/initial-1)<2e-12


def test_checkpoint_roundtrip(tmp_path):
    z=p.synthetic_initial(12,10)
    f=tmp_path/'in.npz'
    np.savez(f,psi=z,dt=.003,box=10.,xi=.28,mu=6.377551,case='B160',step=8,source_sha256='fake',grid_n=12)
    out,meta=p.checkpoint_state(f)
    assert meta['case']=='B160' and np.array_equal(out,z)


def test_no_cpu_gpu_claim():
    d,m=p.select_torch_device(torch,'cpu','A770')
    assert d.type=='cpu' and m['xpu_used'] is False
