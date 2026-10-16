from hicks_hill.analytic import SphereVortex,J,root_families
import numpy as np

def test_roots():
    r=root_families(3)
    assert abs(r['lambda1'][0]-4.4934094579)<2e-9
    assert abs(r['lambda2'][0]-5.7634591969)<2e-9
    for x in r['lambda1']:assert abs(J(x))<1e-12
    for x in r['lambda2']:assert abs(3*J(x)-x*np.sin(x))<1e-12

def test_hill_boundary_and_euler():
    f=SphereVortex(lam=0)
    assert f.surface_residual()['normal_velocity_abs_max']<1e-12
    assert f.numerical_residual(0.3,0.4)['euler_norm']<1e-5

def test_beltrami_boundary_euler():
    f=SphereVortex(lam=root_families(1)['lambda1'][0])
    assert f.surface_residual()['normal_velocity_abs_max']<1e-11
    for x,y in [(0.3,0.1),(0.4,0.3),(0.5,-0.1)]:
        v=f.numerical_residual(x,y)
        assert v['divergence']<2e-5
        assert v['euler_norm']<2e-5
        assert v['beltrami_norm']<2e-5

def test_rest_family_zero_U():
    f=SphereVortex(lam=root_families(1)['lambda2'][0])
    assert abs(f.U)<1e-12

def test_pressure_continuity():
    f=SphereVortex(lam=root_families(1)['lambda1'][0]);s=0.6;z=(1-s*s)**0.5
    assert abs(f.pressure(s,z)-f.pressure(s*1.0000001,z*1.0000001))<0.0002


def test_a046_poisson_bridge():
    from hicks_hill.bridges import strain_and_pressure_poisson
    f=SphereVortex(lam=root_families(1)['lambda1'][0])
    a=strain_and_pressure_poisson(f,.4,.25,.2)
    assert abs(a['divergence'])<1e-4
    assert abs(a['pressure_poisson_residual'])<0.005


def test_a057_volume_energy_bridge():
    from hicks_hill.bridges import volume_energy
    for f in (SphereVortex(),SphereVortex(lam=root_families(1)['lambda1'][0])):
        a=volume_energy(f,order=34);b=volume_energy(f,order=54)
        assert a['total_lab_kinetic_energy']>0
        assert abs(a['total_lab_kinetic_energy']-b['total_lab_kinetic_energy'])/b['total_lab_kinetic_energy']<5e-5
