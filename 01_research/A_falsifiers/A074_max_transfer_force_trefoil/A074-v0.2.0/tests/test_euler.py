import json,math
from pathlib import Path
import numpy as np
from experiment.euler3d import Euler3D
from experiment.model import sample_seed,load_seed,ring
from experiment.run_euler import perturb_curve
ROOT=Path(__file__).resolve().parents[1]

def test_seed_provenance():
    seed=load_seed(ROOT/'seeds/trefoil_ideal_3_1_1.json')
    assert seed['id']=='3:1:1' and math.isclose(seed['L'],16.371637)
    assert len(sample_seed(seed,128))==128

def test_zero_mean_div_free_force():
    e=Euler3D(24,6)
    f=e.force(.6)
    assert np.linalg.norm(e.divhat(f).ravel())/np.linalg.norm(f.ravel())<1e-12
    assert abs(e.ifft(f).mean())<1e-14
    assert np.isclose(e.nominal_half_load(.6),.6*6**3/math.pi)

def test_roundtrip_projection():
    e=Euler3D(24,6)
    rng=np.random.default_rng(20261026)
    uhat=e.project(e.fft(rng.normal(size=(3,24,24,24))))
    assert np.linalg.norm(e.divhat(uhat))<1e-10*np.linalg.norm(uhat)
    assert np.linalg.norm(uhat-e.project(e.fft(e.ifft(uhat))))<1e-9*np.linalg.norm(uhat)

def test_rotational_convective_parity():
    e=Euler3D(24,6)
    u=e.omega_initial(ring(64),.38)
    a=e.rhs(u,form='rotational');b=e.rhs(u,form='convective')
    assert np.linalg.norm(a-b)/np.linalg.norm(a)<1e-12

def test_pressure_poisson_closure():
    e=Euler3D(24,6)
    u=e.omega_initial(ring(64),.38)
    p=e.pressure_report(u)
    assert p['poisson_relative_residual']<1e-10
    assert p['divergence_relative_residual']<1e-10

def test_unforced_conservation_short_time():
    e=Euler3D(24,6)
    u=e.omega_initial(ring(64),.38)
    E=e.diagnostics(u)['energy_J']
    for _ in range(4):u=e.timestep(u,.0125)
    assert abs(e.diagnostics(u)['energy_J']/E-1)<1e-4

def test_periodic_particle_sampling():
    e=Euler3D(24,6)
    u=e.ifft(e.omega_initial(ring(64),.38))
    x=np.array([[0.21,-1.2,2.5],[-2.2,1.1,.3]])
    assert np.allclose(e.sample(u,x),e.sample(u,x+np.array([6,-6,6])),rtol=1e-11)

def test_geometry_perturbations_distinct():
    x=ring(128)
    assert np.linalg.norm(perturb_curve(x,.01,'z2')-x)>0
    assert np.linalg.norm(perturb_curve(x,.01,'x3')-x)>0
