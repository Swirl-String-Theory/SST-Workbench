import numpy as np
from sst_finite_core_falsifier.eigen import solve_spectrum,select_hybrid_mode,dispersion_branch
from sst_finite_core_falsifier.delay import wavepacket_return,loop_wavenumber

def test_finite_core_generalized_eigenproblem_has_resolved_hybrid_mode():
    sp=solve_spectrum('gaussian',0.75,1,0.08,32,5.0)
    md=select_hybrid_mode(sp,min_localization=.2,min_axial=.02,max_axial=.98,max_residual=1e-6)
    assert md is not None
    assert md['residual']<1e-6
    assert 0<md['axial_energy_fraction']<1
    assert md['core_localization']>.2

def test_dispersion_generates_group_velocity_without_delay_parameter():
    d=dispersion_branch('gaussian',0.75,1,0.08,32,5.0,.15,2,{'min_localization':.2,'min_axial':.02,'max_axial':.98,'max_residual':1e-6,'min_overlap':.02,'dispersion_dk_floor':.008})
    assert d['available']
    assert np.isfinite(d['group_velocity'])

def test_wavepacket_return_recovers_linear_group_delay():
    # omega(k0+q)-omega(k0)=v_g q => exact periodic return L/|v_g|
    L=40.0;vg=1.7;k0=.2;omega0=.9;co=[vg,omega0]  # polyval in q: vg*q + omega0
    r=wavepacket_return(L,k0,omega0,co,vg,31,501)
    assert r['available']
    assert r['tau_relative_error']<.03

def test_bishop_loop_closure_formula():
    k=loop_wavenumber(100,2,3,.4,0.0)
    assert abs(k*100+2*.4-2*np.pi*3)<1e-12
