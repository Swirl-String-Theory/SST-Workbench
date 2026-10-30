import math
from pathlib import Path
import numpy as np
import pytest
from ruban_equilibrium.high_order import field,residual,make_shape,fit,refine_check
from ruban_equilibrium.full_spectrum import normal_frame,jacobian,evaluate_spectrum,compare_matrices
from ruban_equilibrium.runner import load_a007_at_uniform_theta,verify


def test_anchor_hash_and_paper_constants():
    data=verify()
    assert data['A007_primary_sha256']=='127de915c8eaae59325b8bd2697a0ab50c71eb1c5cf0a91fc55ed44de70fcc89'


def test_a007_actual_seed_compares_with_exact_formula():
    x=load_a007_at_uniform_theta(64)
    y=make_shape(.154,64,[])
    assert x.shape==(64,3)
    assert np.max(np.abs(x-y))<1e-7


def test_two_quadratures_approximate_same_smooth_model_as_n_grows():
    def diff(n):
        x=make_shape(.154,n,[])
        return np.linalg.norm(field(x,'midpoint')-field(x,'trapezoid'))/np.sqrt(n)
    assert diff(128)<diff(64)


def test_rigid_translation_does_not_change_field():
    x=make_shape(.154,48,[])
    d=np.array([1.2,-.8,.1]);a=field(x)
    assert np.max(np.abs(field(x+d)-a))<1e-9


def test_normal_frame_is_orthonormal():
    x=make_shape(.154,32,[]);e1,e2=normal_frame(x)
    assert np.max(np.abs(np.einsum('ij,ij->i',e1,e2)))<1e-12
    assert np.max(np.abs(np.linalg.norm(e1,axis=1)-1))<1e-12
    assert np.max(np.abs(np.linalg.norm(e2,axis=1)-1))<1e-12


def test_full_finite_n_matrix_and_all_discrete_eigenvalues():
    x=make_shape(.154,32,[])
    J,meta=jacobian(x,step=2e-5)
    assert J.shape==(64,64) and meta['dof']==64
    z=evaluate_spectrum(J)
    assert z['n_eigenvalues']==64
    assert np.all(np.isfinite(J))


def test_finite_difference_step_check():
    x=make_shape(.154,32,[])
    J,_=jacobian(x,step=2e-5)
    K,_=jacobian(x,step=1e-5)
    assert compare_matrices(J,K)<.01


def test_invalid_modes_and_bad_geometry_rejected():
    with pytest.raises(ValueError):field(np.zeros((24,3)))
    with pytest.raises(ValueError):fit(.154,48,reference_points=np.zeros((32,3)))
    with pytest.raises(ValueError):jacobian(make_shape(.154,32,[]),step=0)


def test_fitted_original_is_not_fake_equilibrium():
    x=load_a007_at_uniform_theta(48)
    fit0=fit(.154,48,harmonics=0,reference_points=x)
    assert fit0['final']['epsilon']>.01
    assert fit0['optimizer_success'] is False


def test_even_number_modes_and_periodic_consistency():
    x=make_shape(.154,64,np.zeros(8))
    assert np.max(np.abs(x-make_shape(.154,64,[])))<1e-15
    assert residual(x,'trapezoid')['epsilon']>0
