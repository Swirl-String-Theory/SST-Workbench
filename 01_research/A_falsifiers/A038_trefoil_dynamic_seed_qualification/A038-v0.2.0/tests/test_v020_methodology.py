import json
from pathlib import Path
import numpy as np
from sst_seed_falsifier.candidates import analytic_trefoil,generate
from sst_seed_falsifier.dynamics import tangential_redistribution
from sst_seed_falsifier.geometry import resample_closed,normalize_length,tangents
from sst_seed_falsifier.metrics import shape_distance
from sst_seed_falsifier.io import load_json
from sst_seed_falsifier.workflow import _stratified_ids


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
    cfg={'source_regex':'knot_3[.]1','extensions':['.txt'],'allow_analytic_fallback':False,'candidate_seed':7,'candidate_n':64,'target_length':2*np.pi,'max_sources':3,'variants_per_source':4,'max_candidates':3,'xy_scale_range':[.99,1.01],'z_scale_range':[.99,1.01],'max_deform_mode':2,'normal_amp_range':[-.001,.001],'binormal_amp_range':[-.001,.001],'contact_skip':3,'min_initial_gap_over_ds':.1,'cyclic_stride':4,'source_dedup_rms_tol':1e-12}
    generate(data,out,cfg); m=load_json(out/'public_manifest.json')
    assert len(m['candidates'])==3
    assert len({r['source_group_id'] for r in m['candidates']})==3


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
