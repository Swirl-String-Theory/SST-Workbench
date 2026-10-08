from pathlib import Path
import json
import numpy as np
from a056_science.spectral import circular_fourier_metrics, spectral_qualification

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'configs'/'e010_real_score.json').read_text())['spectral']

def base_phi(nt=80, ns=128):
    t=np.linspace(0,1,nt)
    s=np.linspace(0,2*np.pi,ns,endpoint=False)
    return 0.7*np.cos(3*s[None,:]-1.1*t[:,None]) + 0.16*np.cos(5*s[None,:]+0.4*t[:,None])

def blocking(phi):
    m,_,_=spectral_qualification(phi,CFG,.65)
    return m['blocking']

def test_integer_2pi_wrap_invariance():
    phi=base_phi(); rng=np.random.default_rng(123)
    wrapped=phi+2*np.pi*rng.integers(-3,4,size=phi.shape)
    a,b=blocking(phi),blocking(wrapped)
    for key in ('circular_top_energy_fraction','circular_orthogonality_residual','fourier_power_overlap'):
        assert np.isclose(a[key],b[key],rtol=1e-12,atol=1e-12)

def test_time_dependent_global_phase_invariance():
    phi=base_phi(); psi=np.linspace(-2.2,3.1,len(phi))[:,None]
    a,b=blocking(phi),blocking(phi+psi)
    for key in ('circular_top_energy_fraction','circular_orthogonality_residual','fourier_power_overlap'):
        assert np.isclose(a[key],b[key],rtol=1e-12,atol=1e-12)

def test_fixed_cyclic_spatial_relabelling_invariance():
    phi=base_phi(); shifted=np.roll(phi,17,axis=1)
    a,b=blocking(phi),blocking(shifted)
    for key in ('circular_top_energy_fraction','circular_orthogonality_residual','fourier_power_overlap'):
        assert np.isclose(a[key],b[key],rtol=1e-12,atol=1e-12)

def test_fourier_overlap_rejects_true_sector_change():
    nt,ns=100,140; s=np.linspace(0,2*np.pi,ns,endpoint=False)
    phi=np.empty((nt,ns))
    phi[:65]=0.9*np.cos(2*s)[None,:]
    phi[65:]=0.9*np.cos(7*s)[None,:]
    inv,_,_=circular_fourier_metrics(phi,3,.65)
    assert inv['fourier_power_overlap'] < 0.90

def test_all_bundled_synthetic_controls_pass_new_g2():
    for p in sorted((ROOT/'data'/'synthetic_blind').glob('*.npz')):
        a=np.load(p); m,_,_=spectral_qualification(a['phi'],CFG,.65)
        assert m['pass'], (p.name,m)
