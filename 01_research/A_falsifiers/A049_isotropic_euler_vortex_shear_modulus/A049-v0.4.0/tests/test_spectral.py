import numpy as np
from sst_vortex_shear.euler_spectral import (
    EulerSpectral3D, random_isotropic_background, helical_probe_field,
    probe_descriptor, probe_amplitude
)


def test_projected_background_is_incompressible_and_energy_normalized():
    g=EulerSpectral3D(9)
    u=random_isotropic_background(g,123,shell_min=2.0,shell_max=2.9,urms=1.0)
    assert g.divergence_fourier_rel(u) < 1e-12
    assert abs(g.urms(u)-1.0) < 1e-12


def test_helical_probe_is_transverse():
    g=EulerSpectral3D(9)
    d=helical_probe_field(g,'x',1,+1,1e-5)
    desc=probe_descriptor(g,'x',1,+1)
    assert g.divergence_fourier_rel(d) < 1e-12
    assert abs(probe_amplitude(d,desc)) > 0.0


def test_rk4_energy_small_short_step():
    g=EulerSpectral3D(9)
    u=random_isotropic_background(g,456,shell_min=2.0,shell_max=2.9,urms=1.0)
    d=np.stack([helical_probe_field(g,'x',1,h,1e-5) for h in (-1,+1)])
    e0=g.energy(u)
    u,d=g.rk4_step(u,d,0.005)
    assert abs(g.energy(u)-e0)/e0 < 1e-7
