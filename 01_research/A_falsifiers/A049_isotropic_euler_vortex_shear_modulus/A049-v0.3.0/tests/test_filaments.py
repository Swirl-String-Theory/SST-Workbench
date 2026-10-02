import numpy as np
from sst_vortex_shear.filaments import hopf_cell, gauss_linking_number, rk4_step, shape_relative_rms
from sst_vortex_shear.backend import filament_energy


def test_hopf_and_unlinked_controls():
    h=hopf_cell(1.0,24,True); u=hopf_cell(1.0,24,False)
    assert abs(abs(gauss_linking_number(h[0],h[1]))-1.0) < 0.03
    assert abs(gauss_linking_number(u[0],u[1])) < 0.03


def test_regularized_energy_positive():
    h=hopf_cell(1.0,24,True)
    assert filament_energy(h,[1.0,1.0],0.18) > 0.0


def test_rk4_reversibility_short():
    h=hopf_cell(1.0,20,True)
    x=h.copy()
    for _ in range(4): x=rk4_step(x,0.01,[1.0,1.0],0.18)
    for _ in range(4): x=rk4_step(x,-0.01,[1.0,1.0],0.18)
    assert shape_relative_rms(x,h) < 1e-10
