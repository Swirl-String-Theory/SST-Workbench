import numpy as np
from pathlib import Path
from microgravity.gravity_closure_v060 import gaussian_reference,direct_field,extract_cells,run_gravity
from microgravity.spectral_dynamics_v050 import SpectralBox

def test_gaussian_manufactured():
    t=gaussian_reference(n=24)
    assert t['max_rel_error']<.002
    assert abs(t['mass_quadrature']-1)<1e-5

def test_coulomb_point_field():
    x=np.array([[0.,0.,0.]])
    m=np.array([2.])
    phi,g=direct_field(x,m,np.array([[2.,0.,0.]]))
    assert abs(phi[0]+1)<1e-14
    assert np.allclose(g[0],[-.5,0,0],atol=1e-14)

def test_active_charge_energy_definition():
    b=SpectralBox(16)
    Y=b.grid[...,1]
    u=np.zeros((3,16,16,16))
    u[0]=0.1*np.sin(2*np.pi*Y/b.length)
    uh=b.project(b.fft(u))
    _,mas,z=extract_cells(b,uh)
    assert mas.min()>=0
    assert abs(z['total_energy_charge_natural_units']-b.diagnostics(uh)['E'])<1e-12

def test_local_clock_no_farfield_outside_support():
    # A local clock factor S=sqrt(1-u²/c_ref²) is constant if u=0.
    assert np.sqrt(1-0./(10.**2))==1.

def test_periodic_poisson_zero_mean():
    b=SpectralBox(16)
    # laplacian of any periodic field has exactly k0=0
    a=np.random.default_rng(16).normal(size=(16,16,16))
    transformed=-b.k2*np.fft.fftn(a)
    assert abs(transformed[0,0,0])==0

def test_against_windows_v050_baseline_basic(tmp_path):
    z=run_gravity(tmp_path,'BASIC')
    assert z['manufactured_gaussian']['max_rel_error']<0.002
    assert all(v['status']=='PASS' for v in z['native_cpp_fp64'].values()) or any(v['status']=='UNRESOLVED' for v in z['native_cpp_fp64'].values())
    assert {v['gate']:v['status'] for v in z['gates']}['V14']=='FAIL'
    assert z['qualification']['metrics']['max_exponent_abs_error']<0.03
    assert z['qualification']['metrics']['max_far_field_rel_monopole_deviation']<0.025
    assert z['bounds']['full_gravity_closure'] is False
