import json,re
from pathlib import Path
import numpy as np
from sst_modal_clock.geometry import synthetic_trefoil,resample_closed,canonical_arclength_align,tangential_redistribution_velocity,tangents
from sst_modal_clock.analyze import _coverage_gate
ROOT=Path(__file__).resolve().parents[1]

def cfg(name): return json.loads((ROOT/'config'/name).read_text())

def test_parameterization_invariant_alignment_handles_cyclic_phase_and_rigid_motion():
    x=resample_closed(synthetic_trefoil(97),64)
    a=.73; R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
    y=np.roll(x,13,axis=0)@R.T+np.array([2.1,-3.2,.7])
    z=canonical_arclength_align(y,x)
    assert np.sqrt(np.mean(np.sum((z-x)**2,axis=1)))<0.01

def test_segment_feedback_mesh_controller_reduces_ds_cv_and_is_tangent_only():
    th=np.linspace(0,2*np.pi,64,endpoint=False); ph=th+.35*np.sin(th)
    x=np.c_[np.cos(ph),np.sin(ph),np.zeros_like(ph)]
    def cv(q):
        ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1); return float(ds.std()/ds.mean())
    c0=cv(x)
    for _ in range(800): x=x+.001*tangential_redistribution_velocity(x,4.0,'segment_feedback')
    assert cv(x)<.1*c0
    u=tangential_redistribution_velocity(x,4.0,'segment_feedback'); t=tangents(x)
    leak=np.linalg.norm(u-(u*t).sum(1)[:,None]*t)/max(np.linalg.norm(u),1e-30)
    assert leak<1e-12

def test_global_negative_verdict_requires_coverage_and_priority():
    c={'gate_min_valid_carrier_fraction_for_global_fail':.8,'gate_min_valid_carriers_for_global_fail':20,'gate_require_all_priority_carriers':True}
    assert not _coverage_gate(49,3,3,0,c)['coverage_ok_for_global_fail']
    assert not _coverage_gate(49,40,3,2,c)['coverage_ok_for_global_fail']
    assert _coverage_gate(49,40,3,3,c)['coverage_ok_for_global_fail']

def test_basic_priority_carriers_and_mesh_gauge_are_predeclared():
    c=cfg('basic.json')
    pats=' '.join(c['priority_source_patterns'])
    assert 'knot_6' in pats and 'link_4' in pats and 'link_9' in pats
    assert c['gate_require_all_priority_carriers'] is True
    assert c['mesh_gauge_low_factor']<1<c['mesh_gauge_high_factor']
    assert c['mesh_redistribution_method']=='segment_feedback'
    assert c['gate_max_stage_a_ds_cv']==.2

def test_focus_and_resolution_coverage_semantics():
    for n in ('focus_6p3.json','focus_link_4p2p1.json','focus_link_9p2p20.json'):
        c=cfg(n); assert c['gate_min_valid_carriers_for_global_fail']==1 and c['gate_min_valid_carrier_fraction_for_global_fail']==1.0
    for n in (64,96,128):
        c=cfg(f'resolution_N{n}.json'); assert c['gate_min_valid_carriers_for_global_fail']==3 and c['gate_min_valid_carrier_fraction_for_global_fail']==1.0

def test_run_chain_contains_mesh_gauge_certification():
    s=(ROOT/'run_basic.cmd').read_text(errors='ignore')
    assert 'stage_a_gauge_low' in s and 'stage_a_gauge_high' in s and 'analyze-stage-a-gauge' in s
    w=(ROOT/'src/sst_modal_clock/workflow.py').read_text()
    assert 'flush=True' in w and 'carrier=' in w

def test_version_is_021():
    assert '0.2.1' in (ROOT/'pyproject.toml').read_text()
    assert '0.2.1' in (ROOT/'src/sst_modal_clock/__init__.py').read_text()
