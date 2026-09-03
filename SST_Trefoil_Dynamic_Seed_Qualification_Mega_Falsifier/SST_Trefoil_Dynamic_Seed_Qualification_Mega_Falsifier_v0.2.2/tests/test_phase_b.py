import json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from sst_seed_falsifier.phase_b import (FlowContract, ReturnAction, central_jacobian,
    flow_rhs, integrate, symmetry_basis, quotient_diagnostics, floquet_certificate, intervention_panel,
    refine_full_state, run_ladders)
from sst_seed_falsifier.geometry import arclength
from sst_seed_falsifier.dynamics import _long_rhs
from sst_seed_falsifier.candidates import analytic_trefoil
from sst_seed_falsifier.topology_witness import trefoil_witness


def protocol():
    return json.loads((Path(__file__).resolve().parents[1]/'config/phase_b.json').read_text())


def ring(n=8):
    t=np.arange(n)*2*np.pi/n
    return np.c_[np.cos(t),np.sin(t),np.zeros(n)]


def contract(x):
    return FlowContract(len(x),arclength(x),require_native=False,guard_stride=4)


def test_full_fd_covers_every_coordinate():
    rng=np.random.default_rng(10); a=rng.normal(size=(12,12)); x=rng.normal(size=(4,3))
    actual=central_jacobian(lambda z:(a@z.ravel()).reshape(z.shape),x,1e-5)
    np.testing.assert_allclose(actual,a,atol=1e-9)


def test_fixed_group_action_is_not_refitted_per_perturbation():
    x=ring(); rotation=((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.))
    action=ReturnAction(2,rotation,(.1,.2,.3))
    m=central_jacobian(action.apply,x,1e-5)
    d=np.arange(x.size).reshape(x.shape)/10
    np.testing.assert_allclose((m@d.ravel()).reshape(x.shape),np.roll(d,2,axis=0)@np.asarray(rotation).T,atol=1e-9)


def test_native_alpha_one_matches_inherited_rhs_with_frozen_volume():
    x=ring(12); x[0]*=1.03; c=contract(x)
    old=_long_rhs(x,c.gamma,c.core0,False,c.reference_length,c.mesh_rate,c.mesh_method,c.mesh_cap)[0]
    np.testing.assert_allclose(flow_rhs(x,c),old,atol=1e-14)
    perturbed=x*1.03
    reset=replace(c,reference_length=arclength(perturbed))
    assert np.linalg.norm(flow_rhs(perturbed,c)-flow_rhs(perturbed,reset))>1e-6


def test_trivial_modes_rank_and_noninvariance_are_checked():
    x=ring(); q=symmetry_basis(x,np.broadcast_to([0,0,1.],x.shape))
    assert q.shape==(24,6)
    assert quotient_diagnostics(np.eye(24),q)['symmetry_leakage']<1e-12
    from scipy.linalg import null_space
    z=null_space(q.T)[:,0]
    bad=np.eye(24)+np.outer(z,q[:,0])
    assert quotient_diagnostics(bad,q)['symmetry_leakage']>.1


def test_ring_full_state_metrology_and_sham():
    x=ring(); c=contract(x); p=protocol()
    cert=floquet_certificate(x,1.2,24,c,p)
    assert cert['status']=='NUMERICALLY_VALIDATED_AT_DISCRETIZATION',cert
    assert cert['symmetry_rank']==6
    assert cert['quotient_dimension']==18
    assert cert['physics_verdict']=='NOT_ESTABLISHED'
    panel=intervention_panel(x,1.2,24,c,p,baseline_certificate=cert)
    assert panel['status']=='PAIRED_MODEL_INTERVENTION_COMPLETED'
    assert panel['sham_max_abs_error']==0
    assert max(abs(a['paired_primary_effect']) for a in panel['arms'])<1e-10
    assert not panel['causal_language_allowed']
    with pytest.raises(ValueError,match='CONTRACT_MISMATCH'):
        intervention_panel(x,1.2,24,replace(c,mesh_rate=3.),p,baseline_certificate=cert)
    with pytest.raises(ValueError,match='STATE_MISMATCH'):
        intervention_panel(x*1.01,1.2,24,c,p,baseline_certificate=cert)
    with pytest.raises(ValueError,match='TIME_GRID_MISMATCH'):
        intervention_panel(x,1.3,24,c,p,baseline_certificate=cert)


def test_no_accurate_rpo_no_certificate_or_intervention():
    x=ring(); x[0,2]=.05; c=contract(x); p=protocol()
    early=floquet_certificate(x,.1,8,c,p)
    assert early['status']=='BLOCKED_EARLY_RETURN'
    cert=floquet_certificate(x,1.2,48,c,p)
    assert cert['status']=='BLOCKED_NO_ACCURATE_RPO'
    assert intervention_panel(x,1.2,48,c,p,baseline_certificate=cert)['status']=='BLOCKED_NO_CERTIFIED_BASELINE'


def test_full_state_shooting_ring_and_minimum_period():
    x=ring(); c=contract(x); p=protocol()
    with pytest.raises(ValueError,match='MINIMUM_PERIOD'):
        refine_full_state(x,.1,8,c,p)
    y,t,action,result=refine_full_state(x,1.2,12,c,p)
    assert result['status']=='RPO_RESIDUAL_PASSED'
    assert result['full_state_dimension']==24
    assert t>=1.2


def test_time_grid_convergence_nontrivial_state():
    x=ring(12); x[0,2]=.04; c=contract(x)
    states=[integrate(x,.2,n,c)['final'] for n in [4,8,16]]
    coarse=np.linalg.norm(states[0]-states[1]); fine=np.linalg.norm(states[1]-states[2])
    assert coarse/fine>10


def test_arnoldi_cannot_claim_complete_spectrum():
    x=ring(); c=contract(x); p=protocol()
    p.update(arnoldi_k=2,arnoldi_tol=1e-6)
    result=floquet_certificate(x,1.2,12,c,p,method='arnoldi')
    assert result['status'] in ['PARTIAL_SPECTRUM_NOT_CERTIFIED','FAILED_ARNOLDI_CONVERGENCE']
    assert result['physics_verdict']=='NOT_ESTABLISHED'


def test_ladder_enumerates_every_cell_and_keeps_publication_gate_closed():
    p=protocol(); p.update(resolution_ladder=[8],dt_multipliers=[1.,.5],core_ladder=[.08],mesh_rate_ladder=[4.])
    result=run_ladders(ring(),1.2,{'dt_factor':.2,'max_steps':1000,'require_native':False},p)
    assert len(result['cells'])==2
    assert not result['causal_language_allowed']
    assert result['status']=='CROSS_LADDER_COMPARISON_REQUIRED'


def test_trefoil_diagram_witness_does_not_accept_unknot_or_figure_eight():
    assert trefoil_witness(analytic_trefoil(96))['accepted']
    assert trefoil_witness(analytic_trefoil(96)*[-1,1,1])['accepted']
    assert not trefoil_witness(ring(64),projections=12)['accepted']
    t=np.arange(96)*2*np.pi/96
    figure8=np.c_[(2+np.cos(2*t))*np.cos(3*t),(2+np.cos(2*t))*np.sin(3*t),np.sin(4*t)]
    assert not trefoil_witness(figure8,projections=12)['accepted']
