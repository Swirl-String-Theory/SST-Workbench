import numpy as np
from sst_finite_core_falsifier.sst_lagrangian import (
    ModeField, material_specific_lagrangian_coefficient, relative_frequency,
    analytic_lagrangian_mode, phase_align,
)


def toy(phase=0.0,k=0.2):
    r=np.linspace(0,2,33); U=np.exp(-r*r); V=r/np.sqrt(1+r**4)
    q=np.exp(1j*phase)
    ur=q*(0.2+0.1*r); ut=q*(0.3-0.05*r); uz=q*(0.4+0.02*r); pi=q*(0.1+0.03*r)
    return ModeField(r,U,V,ur,ut,uz,pi,0.0,1.2,k,1)


def test_first_order_specific_lagrangian_coefficient():
    f=toy()
    C=material_specific_lagrangian_coefficient(f)
    assert np.allclose(C, f.U*f.uz + f.V*f.ut - f.pi)


def test_material_relative_frequency():
    f=toy(k=0.0)
    w=relative_frequency(f)
    assert np.all(np.isfinite(w))
    assert w.shape==f.r.shape


def test_analytic_kernel_t0_is_coefficient():
    f=toy()
    C=material_specific_lagrangian_coefficient(f)
    L=analytic_lagrangian_mode(f,np.array([0.0,0.1]))
    assert np.allclose(L[:,0],C)


def test_phase_alignment_removes_arbitrary_eigenvector_phase():
    a=toy(0.0); b=toy(0.73)
    bb,rot,ov=phase_align(a,b)
    z=np.trapezoid((np.conj(a.ur)*bb.ur+np.conj(a.ut)*bb.ut+np.conj(a.uz)*bb.uz)*a.r,a.r)
    assert abs(np.angle(z))<1e-12
    assert ov>0.999999999
