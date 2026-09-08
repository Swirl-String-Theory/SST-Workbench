import numpy as np
from sst_threaded_hole_falsifier.pressure import fit_free_power_exponent
from sst_threaded_hole_falsifier.stats import carrier_cluster, polynomial_pressure_law, symmetric_even_odd
from sst_threaded_hole_falsifier.workflow import decision
from sst_threaded_hole_falsifier.phase import best_small_rational_lock
from sst_threaded_hole_falsifier.model import CurveSet
from sst_threaded_hole_falsifier.geometry import min_nonlocal_segment_distance_exact


def test_free_exponent_recovers_one_over_r_without_target():
    r=np.linspace(.7,3.0,30);p=2.3-0.7/r
    f=fit_free_power_exponent(r,p,.4,2.8,241)
    assert abs(f['nu_best']-1.0)<0.03
    assert f['r2_best']>0.99999


def test_free_exponent_recovers_one_over_r2_without_target():
    r=np.linspace(.7,3.0,30);p=-.4+1.2/r**2
    f=fit_free_power_exponent(r,p,.4,2.8,241)
    assert abs(f['nu_best']-2.0)<0.03


def test_carrier_cluster_does_not_count_repeated_beta_as_independent():
    vals=[-1,-2,-3,+1,+2,+3];ids=['K1']*3+['K2']*3
    x=carrier_cluster(vals,ids,True)
    assert x['n_carriers']==2
    assert x['n_nonzero_carriers']==2
    assert x['favorable_carriers']==1


def test_pressure_law_even_quadratic_recovery():
    b=np.array([-2,-1,-.5,.5,1,2.]);A=.3;B=-.12;y=A*b+B*b*b
    q=polynomial_pressure_law(b,y,4)
    assert abs(q['coefficients'][0]-A)<1e-10
    assert abs(q['coefficients'][1]-B)<1e-10
    s=symmetric_even_odd(b,y)
    assert abs(s['median_even_quadratic_B']-B)<1e-10
    assert abs(s['median_odd_linear_A']-A)<1e-10


def test_contact_gate_blocks_truncated_auc_scoring():
    cfg={'tau_end':1.0,'contact_survival_tie_fraction':.03}
    a={'dynamic_status':'FAIL_CONTACT','actual_tau_end':.2,'shape_auc':1e-9,'initial_relative_equilibrium_residual':1e-9,'rpo_residual':1e-9,'max_real_growth_positive':0}
    b={'dynamic_status':'PASS_FULL_HORIZON','actual_tau_end':1.0,'shape_auc':100,'initial_relative_equilibrium_residual':100,'rpo_residual':100,'max_real_growth_positive':100}
    d=decision(a,b,cfg)
    assert d['winner_anonymous']=='B'
    assert d['decision_basis']=='CONTACT_GATE'
    assert d['metric_log_ratios_A_over_B']=={}


def test_best_small_rational_lock_discovers_ratio_not_targeted():
    # wt/wc=5/2; p*wc ~= q*wt therefore p/q=5/2.
    x=best_small_rational_lock(2.0,5.0,8)
    assert x['p']==5 and x['q']==2
    assert x['residual']<1e-12


def test_exact_segment_clearance_detects_crossing():
    # Two closed 4-segment loops with one transverse segment crossing.
    a=np.array([[-1,0,0],[1,0,0],[1,1,0],[-1,1,0]],float)
    b=np.array([[0,-1,0],[0,.5,0],[.5,.5,0],[.5,-1,0]],float)
    cs=CurveSet.from_components([a,b])
    assert min_nonlocal_segment_distance_exact(cs,1)<1e-12


def test_anonymous_delta_exponent_is_sign_invariant():
    from sst_threaded_hole_falsifier.workflow import anonymous_delta_pressure_fit
    r=np.linspace(.7,3.0,30);base=1.3+.05*r
    a={'radial_r':r.tolist(),'radial_p':(base-.4/r**1.5).tolist()}
    b={'radial_r':r.tolist(),'radial_p':base.tolist()}
    cfg={'pressure_fit':{'nu_min':.1,'nu_max':4.0,'nu_steps':391}}
    ab=anonymous_delta_pressure_fit(a,b,cfg);ba=anonymous_delta_pressure_fit(b,a,cfg)
    assert abs(ab['delta_far_profile_nu_blind']-1.5)<0.03
    assert abs(ab['delta_far_profile_nu_blind']-ba['delta_far_profile_nu_blind'])<1e-12
    assert np.sign(ab['delta_far_profile_coeff_A_minus_B_blind'])==-np.sign(ba['delta_far_profile_coeff_A_minus_B_blind'])


def test_seal_detects_result_tamper(tmp_path):
    import json
    from pathlib import Path
    from sst_threaded_hole_falsifier.seal import seal,verify
    project=tmp_path/'project';project.mkdir();(project/'code.py').write_text('x=1\n',encoding='utf-8')
    blind=tmp_path/'blind';blind.mkdir();(blind/'blind_summary.json').write_text(json.dumps({'carrier_identity_read':False,'condition_identity_read':False,'gravity_target_used':False}),encoding='utf-8');(blind/'result.txt').write_text('sealed data\n',encoding='utf-8')
    catalog=tmp_path/'catalog';catalog.mkdir();(catalog/'pairs_public.csv').write_text('pair_id\nP1\n',encoding='utf-8')
    import hashlib
    psha=hashlib.sha256((catalog/'pairs_public.csv').read_bytes()).hexdigest()
    private=tmp_path/'private';private.mkdir()
    for name in ('candidate_key.csv','pair_key.csv','qualification.csv'):(private/name).write_text(name+'\n',encoding='utf-8')
    h=hashlib.sha256()
    for p in sorted([private/'candidate_key.csv',private/'pair_key.csv',private/'qualification.csv'],key=lambda x:x.name):h.update(p.name.encode());h.update(b'\0');h.update(p.read_bytes());h.update(b'\0')
    (catalog/'manifest_public.json').write_text(json.dumps({'public_pair_sha256':psha,'private_key_commitment_sha256':h.hexdigest()}),encoding='utf-8')
    cfg=tmp_path/'cfg.json';cfg.write_text('{}',encoding='utf-8')
    seal(project,blind,catalog,cfg);verify(project,blind,catalog,cfg,private)
    (blind/'result.txt').write_text('tampered\n',encoding='utf-8')
    import pytest
    with pytest.raises(RuntimeError,match='blind result tree changed'):verify(project,blind,catalog,cfg,private)
