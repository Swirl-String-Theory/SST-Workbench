import json
import pytest
from pathlib import Path
import numpy as np
from sst_seed_falsifier.candidates import analytic_trefoil,generate
from sst_seed_falsifier.dynamics import tangential_redistribution
from sst_seed_falsifier.geometry import resample_closed,normalize_length,tangents
from sst_seed_falsifier.metrics import shape_distance
from sst_seed_falsifier.io import load_json,dump_json,discover_sources
from sst_seed_falsifier.blind import sealed_private_dir
from sst_seed_falsifier.workflow import _stratified_ids,_temporal_classification,stage_mechanism,reveal


def test_mesh_velocity_is_tangential():
    x=normalize_length(resample_closed(analytic_trefoil(256),64),2*np.pi); u=tangential_redistribution(x,4.0,'segment_feedback'); t=tangents(x)
    normal=u-np.sum(u*t,axis=1)[:,None]*t
    assert np.max(np.linalg.norm(normal,axis=1))<1e-12


def test_parameterization_invariant_shape_distance():
    x=normalize_length(resample_closed(analytic_trefoil(512),96),2*np.pi)
    # Different cyclic origin and deliberately nonuniform point-density interpolation of the same polyline.
    y=np.roll(x,17,axis=0); y=resample_closed(y,96)
    assert shape_distance(x,y,4)<1e-4


def test_stratified_promotion_preserves_groups():
    rows=[{'candidate_id':'A','score':10},{'candidate_id':'B','score':9},{'candidate_id':'C','score':8},{'candidate_id':'D','score':1}]
    groups={'A':'G1','B':'G1','C':'G1','D':'G2'}
    ids=_stratified_ids(rows,2,groups,1)
    assert 'D' in ids and len(ids)==2


def test_source_generation_round_robin(tmp_path):
    # Three distinct orientations become three opaque source groups; max_candidates=3 must
    # still schedule one candidate from each source rather than spending all budget on source 1.
    data=tmp_path/'data'; data.mkdir()
    x=analytic_trefoil(96)
    shapes=[]
    for zscale in (.75,1.0,1.35):
        y=x.copy(); y[:,2]*=zscale; shapes.append(y)
    for i,y in enumerate(shapes): np.savetxt(data/f'knot_3.1_source{i}.txt',y)
    out=tmp_path/'out'
    cfg={'run_kind':'blind_scientific','min_scientific_source_groups':3,'source_regex':'knot_3[.]1_source[0-9]+','source_name_match_mode':'fullmatch','extensions':['.txt'],'allow_analytic_fallback':False,'candidate_seed':7,'candidate_n':64,'target_length':2*np.pi,'max_sources':3,'variants_per_source':4,'max_candidates':3,'xy_scale_range':[.99,1.01],'z_scale_range':[.99,1.01],'max_deform_mode':2,'normal_amp_range':[-.001,.001],'binormal_amp_range':[-.001,.001],'contact_skip':3,'min_initial_gap_over_ds':.1,'cyclic_stride':4,'source_dedup_rms_tol':1e-12}
    generate(data,out,cfg); m=load_json(out/'public_manifest.json')
    assert len(m['candidates'])==3
    assert len({r['source_group_id'] for r in m['candidates']})==3
    assert not (out/'private').exists()
    assert (sealed_private_dir(out)/'identity_map.json').exists()
    revealed=reveal(out)
    assert revealed['identity_commitment_verified'] is True
    assert len(revealed['revealed_candidates'])==3


def test_link_names_are_rejected_by_source_discovery(tmp_path):
    x=analytic_trefoil(96)
    np.savetxt(tmp_path/'knot_3.1_final.txt',x)
    np.savetxt(tmp_path/'link_6.3.1_final.txt',x)
    found=discover_sources(tmp_path,r'(?:trefoil(?:[_-].*)?|knot[_-]?3[.]1(?:[_-].*)?)',['.txt'],match_mode='fullmatch')
    assert [p.name for p,_ in found]==['knot_3.1_final.txt']


def test_scientific_prepare_fails_with_one_source_group(tmp_path):
    data=tmp_path/'data'; data.mkdir(); np.savetxt(data/'knot_3.1_only.txt',analytic_trefoil(96))
    cfg={'run_kind':'blind_scientific','min_scientific_source_groups':3,'source_regex':'knot_3[.]1_only','source_name_match_mode':'fullmatch','extensions':['.txt'],'allow_analytic_fallback':False,'candidate_seed':7,'candidate_n':64,'target_length':2*np.pi,'max_sources':3,'variants_per_source':3,'max_candidates':3,'xy_scale_range':[.99,1.01],'z_scale_range':[.99,1.01],'max_deform_mode':2,'normal_amp_range':[-.001,.001],'binormal_amp_range':[-.001,.001],'contact_skip':3,'min_initial_gap_over_ds':.1,'cyclic_stride':4,'source_dedup_rms_tol':1e-12}
    out=tmp_path/'out'
    with pytest.raises(RuntimeError,match='INDETERMINATE_INSUFFICIENT_SOURCE_DIVERSITY'): generate(data,out,cfg)
    s=load_json(out/'prepare_summary.json')
    assert s['physics_verdict']=='INDETERMINATE' and s['n_source_groups_with_candidates']==1


def test_temporal_classification_is_explicit():
    cfg={'temporal_error_floor':1e-12,'temporal_min_order':2.8}
    assert _temporal_classification(2e-15,3e-15,True,cfg)[0]=='FLOOR_LIMITED'
    assert _temporal_classification(8e-4,1e-4,True,cfg)[0]=='ORDER_CONFIRMED'
    assert _temporal_classification(2e-4,3e-4,True,cfg)[0]=='FAILED'


def test_chain_does_not_claim_mesh_certification_when_s37_has_zero(tmp_path):
    out=tmp_path
    for rel,obj in {
        'stage30_resolution/summary.json':{'n_qualified':1},
        'stage32_temporal/summary.json':{'n_qualified':1},
        'stage35_core_robustness/summary.json':{'n_qualified':1},
        'stage37_mesh_gauge/summary.json':{'n_qualified':0},
        'stage40_long/summary.json':{'n_near_rpo_candidates':0,'verdict':'INDETERMINATE_RPO_WINDOW_NUMERICAL_COVERAGE'},
        'stage50_rpo_floquet/summary.json':{'n_projected_floquet_pass':0},
    }.items(): dump_json(out/rel,obj)
    dump_json(out/'stage50_rpo_floquet'/'results.json',[])
    dump_json(out/'prepare_summary.json',{'source_diversity_status':'PASS_SOURCE_DIVERSITY'})
    stage_mechanism(out,{'run_kind':'blind_scientific','mechanism_top_k':1})
    s=load_json(out/'BLIND_CHAIN_SUMMARY.json')
    assert s['verdict']=='CHAIN_CORE_ROBUST_SEEDS__MESH_GAUGE_NOT_CERTIFIED'


def test_one_click_profiles_are_explicit():
    root=Path(__file__).resolve().parents[1]
    expected={
        'run_all.cmd':('outputs\\basic','config\\basic.json'),
        'run_all_extended.cmd':('outputs\\extended','config\\extended.json'),
        'run_all_production.cmd':('outputs\\production','config\\production.json'),
    }
    for name,(out,cfg) in expected.items():
        text=(root/name).read_text(encoding='utf-8')
        assert f'set OUT={out}' in text
        assert f'set CFG={cfg}' in text
        assert '$profile' not in text
        assert 'run_32_temporal.cmd' in text and 'run_37_mesh_gauge.cmd' in text
