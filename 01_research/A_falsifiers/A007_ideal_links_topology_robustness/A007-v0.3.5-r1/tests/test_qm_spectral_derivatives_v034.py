import numpy as np
from sst_link_suite.qm_energy import _periodic_derivatives

def test_fft_derivative_exact_for_resolved_fourier_mode():
    n=128
    t=np.arange(n)*2*np.pi/n
    curve=np.column_stack([np.cos(17*t),np.sin(17*t),0*t])
    d1,d2,_=_periodic_derivatives(curve,"spectral_fft")
    expected1=np.column_stack([-17*np.sin(17*t),17*np.cos(17*t),0*t])
    expected2=np.column_stack([-17**2*np.cos(17*t),-17**2*np.sin(17*t),0*t])
    assert np.max(np.abs(d1-expected1)) < 1e-10
    assert np.max(np.abs(d2-expected2)) < 1e-8
