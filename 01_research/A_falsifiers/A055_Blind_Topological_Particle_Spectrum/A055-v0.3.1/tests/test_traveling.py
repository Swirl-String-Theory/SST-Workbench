import numpy as np
from a055_science.traveling import (
    signed_harmonic_powers_series, analytic_selftest, periodic_bishop_frame,
    eigenvalue_multiset_relative_error, analyze_eigensystem,
)


def test_analytic_signed_direction_selftest():
    r=analytic_selftest()
    assert r['pass']
    assert r['chi_plus'] > 0.999999999
    assert r['chi_minus'] < -0.999999999
    assert abs(r['chi_standing']) < 1e-12
    assert r['conjugate_direction_invariant']


def test_signed_harmonic_nonuniform_phase():
    n=127
    u=np.linspace(0,1,n,endpoint=False)
    theta=2*np.pi*(u + 0.025*np.sin(2*np.pi*u)/(2*np.pi))
    z=np.exp(1j*3*theta)
    p=signed_harmonic_powers_series(theta,z,np.zeros(n,dtype=complex),3)
    chi=(p[2,0]-p[2,1])/(p[2].sum())
    assert chi > 0.999


def test_eigenvalue_multiset_assignment_is_permutation_invariant():
    a=np.array([1+2j,1-2j,-0.1+0j])
    b=np.array([-0.1+0j,1-2j,1+2j])
    assert eigenvalue_multiset_relative_error(a,b) < 1e-15


def test_positive_temporal_representatives_do_not_count_conjugate_as_opposite_pair():
    n=96
    th=2*np.pi*np.arange(n)/n
    c=np.c_[np.cos(th),np.sin(th),0.2*np.sin(2*th)]
    # Two basis vectors carrying cos/sin at k=2 in z.  The eigensystem is one
    # conjugate pair only.  Positive-frequency representative alone cannot
    # manufacture a bidirectional pair.
    B=np.zeros((2,n,3),float)
    B[0,:,2]=np.cos(2*th)
    B[1,:,2]=np.sin(2*th)
    vals=np.array([1j,-1j])
    vecs=np.array([[1,1],[1j,-1j]],complex)/np.sqrt(2)
    r=analyze_eigensystem(vals,vecs,B,[c],families=['kelvin','kelvin'],harmonics=(2,),min_kelvin_basis_fraction=.5,min_harmonic_participation=.1,
                          min_traveling_purity=.5,max_re_over_im=1,max_pair_frequency_asymmetry=.25)
    assert r['positive_frequency_mode_count']==1
    assert not r['qualified_bidirectional_pair']


def test_periodic_bishop_frame_is_orthonormal_and_closes():
    n=160; th=2*np.pi*np.arange(n)/n
    c=np.c_[(1+.15*np.cos(3*th))*np.cos(th),(1+.15*np.cos(3*th))*np.sin(th),.15*np.sin(3*th)]
    t,nv,b,meta=periodic_bishop_frame(c)
    assert meta['closure_error'] < 1e-10
    assert np.max(np.abs(np.einsum('ij,ij->i',t,nv))) < 1e-10
    assert np.max(np.abs(np.einsum('ij,ij->i',t,b))) < 1e-10
    assert np.max(np.abs(np.linalg.norm(nv,axis=1)-1)) < 1e-10
