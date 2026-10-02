import numpy as np
from sst_bkm.resolution import centerline_geometry_audit, spatial_convergence, temporal_convergence
from sst_bkm.diagnostics import model_competition
from sst_bkm.mechanism import local_mechanism


def test_seed_gate_reports_joint_resolution_requirement():
    t=np.linspace(0,2*np.pi,256,endpoint=False)
    p=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])
    a=centerline_geometry_audit(p,2*np.pi,.22,64,{'cells_per_sigma_min':4,'three_sigma_kappa_max':.5,'periodic_clearance_sigma_min':3})
    assert a['N_required_cells_at_current_sigma']>64
    assert a['three_sigma_kappa_max']>0
    assert isinstance(a['geometry_core_gate_pass'],bool)


def test_spatial_and_temporal_convergence_are_same_geometry_observables():
    rows=[{'N':32,'omega_growth':1.3,'bkm_integral':.2},{'N':48,'omega_growth':1.305,'bkm_integral':.202},{'N':64,'omega_growth':1.306,'bkm_integral':.2025}]
    s=spatial_convergence(rows,{'finest_relative_change_max':.05,'observed_order_min':.1})
    assert s['pass']
    tr=[{'dt':.004,'omega_growth':1.30,'bkm_integral':.20},{'dt':.002,'omega_growth':1.3075,'bkm_integral':.20375},{'dt':.001,'omega_growth':1.30796875,'bkm_integral':.203984375}]
    t=temporal_convergence(tr,{'observed_order_min':2.8})
    assert t['pass']


def test_model_competition_recovers_finite_time_power_signal():
    t=np.linspace(0,.8,100); ts=1.0; gamma=1.1
    m=2.0*(ts-t)**(-gamma)
    q=model_competition(t,m,{'late_fractions':[.35,.45,.55],'delta_aicc_min':5,'gamma_min':.9,'tstar_relative_spread_max':.2,'tstar_max_factor':3})
    assert q['finite_time_model_gate_pass']
    assert q['min_gamma']>.9


def test_relative_vorticity_decomposition_identity():
    G=np.array([[.1,.2,-.3],[-.4,.05,.7],[.6,-.2,-.15]])
    w=np.array([G[2,1]-G[1,2],G[0,2]-G[2,0],G[1,0]-G[0,1]])
    q=local_mechanism(G,w)
    assert q['relative_vorticity_decomposition_error']<1e-14
