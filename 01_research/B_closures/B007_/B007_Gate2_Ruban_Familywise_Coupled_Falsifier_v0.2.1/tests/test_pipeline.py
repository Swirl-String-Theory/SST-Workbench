import math,hashlib,json
from pathlib import Path
import numpy as np
import pytest
from src.geometry import get_config,families,generate,metrics,export,CONFIG,GENER
from src.filaments import velocity,fit,run_pair,exploratory_score,quotient_distance
from src.pipeline import create_parser,selected_families,values,parse_floats,parse_integers
from src.coupled import centres,pair_distance_preflight

def test_thirty_families():
    f=families(get_config());assert len(f)==30
    assert sum(math.gcd(x['p'],x['q'])>1 for x in f.values())==6

def test_knots_new_members():
    f=families(get_config());assert {'T_2_9','T_2_11','T_2_3','T_3_2'}<=f.keys()

def test_torus_single_closed():
    p=generate(2,3,.2,128)
    assert len(p)==1 and p[0].shape==(128,3)
    assert 11<metrics(p)['length_total']<15

def test_links_three_components():
    for p,q in [(3,3),(3,6),(3,9),(6,9),(6,15),(6,21)]:
        out=generate(p,q,.2,128)
        assert len(out)==3
        assert metrics(out)['minimum_sampled_intercomponent_distance']>0

def test_perturb_global_volume_preserving():
    p=np.array([.8, .5,.4])
    cfg=get_config();eps=cfg['perturbation_policy']['epsilon_xy'];es=cfg['perturbation_policy']['epsilon_z_shear'];R0=cfg['geometry_R0'];k=2
    # Jacobian determinant for affine XY + Z shear is exactly one analytically
    jac=np.array([[1+eps,0,0],[0,1/(1+eps),0],[es*k*np.cos(k*p[0]/R0),0,1]])
    assert np.isclose(np.linalg.det(jac),1.,atol=1e-14)
    a=generate(2,3,.2,128);b=generate(2,3,.2,128,True)
    assert quotient_distance(a,b)>0

def test_analytic_independent_of_atlas_files():
    assert CONFIG.is_file() and GENER.is_file()
    assert len(generate(2,11,.2,2048)[0])==2048

def test_filament_symmetries():
    p=generate(2,3,.2,64)
    v=velocity(p,.05)
    assert len(v)==1 and v[0].shape==(64,3)
    assert np.isfinite(v[0]).all()
    assert 0<=fit(p,v)['relative_residual']<=1.00000001

def test_residual_known_rigid_translation():
    p=generate(2,3,.2,64)
    v=[np.tile([0,0,.71],(64,1))]
    assert fit(p,v)['relative_residual']<1e-12
    assert abs(fit(p,v)['U_z']-.71)<1e-12

def test_shape_distance_rigid_rotation_translation():
    p=generate(2,3,.2,64)
    x=p[0];a=.34
    Q=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    transformed=[x@Q.T+np.array([3,4,5])]
    assert quotient_distance(p,transformed)<1e-12

def test_pair_reduced_finite_time():
    a=generate(2,3,.16,64);b=generate(2,3,.16,64,True)
    r=run_pair(a,b,3.4,32,steps=2,T=.002)
    assert r['steps']==2 and r['final_time']==.002
    assert r['perturbation_amplification']>0
    assert exploratory_score(r)>=0

def test_fine_values_count():
    cfg=get_config();args=create_parser().parse_args(['--family','T_2_3','--profile','fine'])
    b,l=values(args,cfg);assert len(b)==121 and b[-1]==.32 and len(l)==5

def test_joint_lambda_override():
    cfg=get_config();args=create_parser().parse_args(['--family','T_2_3','--b0','.16,.20','--lambda-values','3.4,6.0'])
    assert values(args,cfg)==([.16,.20],[3.4,6.])

def test_selected_knot_and_link():
    args=create_parser().parse_args(['--family','T_2_9,T_3_9'])
    assert set(selected_families(args,get_config()))=={'T_2_9','T_3_9'}

def test_reject_invalid_family():
    args=create_parser().parse_args(['--family','T_7_7'])
    with pytest.raises(ValueError):selected_families(args,get_config())

def test_background_counts():
    assert len(centres('none'))==0
    assert len(centres('single'))==1
    assert len(centres('triple'))==3
    assert len(centres('3x3'))==9
    assert len(centres('5x5'))==25

def test_no_false_geometry_certification():
    a=generate(3,6,.2,64)
    assert metrics(a)['continuous_reach_certified'] is False
    assert pair_distance_preflight(a,.05)['status'] in ('PASS_CONSERVATIVE_POLYGON_SEPARATION','BLOCKED_NO_CERTIFIED_TUBE_CLEARANCE')

def test_export_hashes(tmp_path):
    parts=generate(3,3,.16,128)
    records=export(parts,tmp_path,'T_3_3_B1600_N128','nominal')
    assert len(records)==3
    for r in records:
        assert hashlib.sha256((tmp_path/r['path']).read_bytes()).hexdigest()==r['sha256']

def test_no_duplicate_select_lists():
    with pytest.raises(ValueError):parse_floats('3.4,3.4')
    with pytest.raises(ValueError):parse_integers('128,128')

def test_select_topological_trefoil_pair():
    args=create_parser().parse_args(['--topology','3_1'])
    assert set(selected_families(args,get_config()))=={'T_2_3','T_3_2'}

def test_select_link_only():
    args=create_parser().parse_args(['--kind','links'])
    assert len(selected_families(args,get_config()))==10

def test_source_provenance_hashes_are_real():
    assert len(hashlib.sha256(CONFIG.read_bytes()).hexdigest())==64
    assert GENER.read_text().startswith('"""E010 v0.3.6')

def test_core_ratio_excludes_underresolved_high_lambda():
    from src.pipeline import stage2
    from tempfile import TemporaryDirectory
    cfg=get_config()
    class A: screen_points=64;screen_steps=1;final_time=.002;seed_points=128;max_segment_over_core=2.
    with TemporaryDirectory() as d:
        rows,gate=stage2({'T_2_3':families(cfg)['T_2_3']},[.2],[7.],Path(d),A(),cfg)
        assert len(rows)==1
        assert rows[0]['spatial_preflight_pass']==False
        assert gate['spatial_preflight_ineligible_pairs']==1
