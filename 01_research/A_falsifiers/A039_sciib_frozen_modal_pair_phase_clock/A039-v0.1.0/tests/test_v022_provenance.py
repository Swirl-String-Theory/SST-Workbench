from pathlib import Path
import json
import numpy as np
from sst_modal_clock.sources import parse_fseries_file,parse_ideal_catalog,canonical_ideal_id
from sst_modal_clock.geometry import component_offsets_from_lengths,next_prev_indices,tangential_redistribution_velocity,tangents
from sst_modal_clock.solver import velocity_py
from sst_modal_clock.analyze import _stage_a_geometry_metrics


def test_fremlin_six_column_parser(tmp_path):
    d=tmp_path/'3_1'; d.mkdir(); p=d/'knot.3_1.fseries'
    p.write_text('% Knot Torus(2,3)\n1 0 0 1 0 0\n0.2 0 0 0.1 0.3 0\n')
    r=parse_fseries_file(p,64)
    assert len(r)==1 and r[0].topology_id=='K3.1' and r[0].provenance=='fseries'
    assert r[0].components[0].shape==(64,3)


def test_gilbert_ideal_ab_parser(tmp_path):
    p=tmp_path/'Ideal.txt'
    p.write_text('''<DATA><AB Id="3:1:1" Conway="3"><Coeff I="1" A="1,0,0" B="0,1,0"/><Coeff I="2" A="0.2,0,0.1" B="0,0.1,0"/></AB></DATA>''')
    r=parse_ideal_catalog(p,'ideal',64)
    assert len(r)==1 and r[0].topology_id=='K3.1' and len(r[0].components)==1


def test_gilbert_ideal_links_keeps_components_separate(tmp_path):
    p=tmp_path/'IdealLinks.txt'
    p.write_text('''<DATA><HL Id="L2a1" Conway="2"><STRING I="1"><Coeff I="0" A="-2,0,0" B="0,0,0"/><Coeff I="1" A="1,0,0" B="0,1,0"/></STRING><STRING I="2"><Coeff I="0" A="2,0,0" B="0,0,0"/><Coeff I="1" A="1,0,0" B="0,1,0"/></STRING></HL></DATA>''')
    r=parse_ideal_catalog(p,'ideal_links',48)
    assert len(r)==1 and r[0].topology_id=='L2.2.1' and r[0].metadata['tag']=='HL'
    assert len(r[0].components)==2 and all(x.shape==(48,3) for x in r[0].components)


def test_indexed_link_connectivity_has_no_spurious_bridge_segment():
    t=np.linspace(0,2*np.pi,16,endpoint=False)
    a=np.c_[np.cos(t)-2,np.sin(t),np.zeros_like(t)]; b=np.c_[np.cos(t)+2,np.sin(t),np.zeros_like(t)]
    x=np.vstack([a,b]); off=component_offsets_from_lengths([16,16]); nxt,_=next_prev_indices(len(x),off)
    assert nxt[15]==0 and nxt[31]==16 and nxt[15]!=16
    cores=np.full(len(x),.1); u=velocity_py(x,1.0,cores,off)
    assert np.isfinite(u).all() and u.shape==x.shape


def test_multicomponent_mesh_velocity_is_tangent_only():
    t=np.linspace(0,2*np.pi,24,endpoint=False); ph=t+.2*np.sin(t)
    a=np.c_[np.cos(ph)-2,np.sin(ph),np.zeros_like(ph)];b=np.c_[np.cos(ph)+2,np.sin(ph),np.zeros_like(ph)]
    x=np.vstack([a,b]);off=component_offsets_from_lengths([24,24]);u=tangential_redistribution_velocity(x,4.0,'segment_feedback',off);tt=tangents(x,off)
    leak=np.linalg.norm(u-(u*tt).sum(1)[:,None]*tt)/max(np.linalg.norm(u),1e-30)
    assert leak<1e-12


def test_mesh_cap_float_tolerance_accepts_capped_roundoff():
    class Z(dict): pass
    z=Z(t=np.array([0.,24.]),ds_cv=np.array([.1,.15]),mesh_speed_rms=np.array([1.5,1.5000000000000004]),physical_speed_rms=np.array([1.,1.]))
    c={'stage_a_t_final':24.,'gate_stage_a_completion_fraction':.995,'gate_max_stage_a_ds_cv':.2,'gate_max_mesh_to_physical_rms_ratio':1.5,'mesh_ratio_absolute_tolerance':1e-12}
    m=_stage_a_geometry_metrics((z,z,z),c)
    assert m['mesh_ratio_ok'] and m['geometry_ok']


def test_v022_paths_and_provenance_gates_predeclared():
    root=Path(__file__).resolve().parents[1]; c=json.loads((root/'config/basic.json').read_text())
    assert c['source_roots']['relaxed'].endswith('KnotPlot/knots/final')
    assert c['source_roots']['fseries'].endswith('Ideal_Fremlin_Fseries/fremlin')
    assert c['source_roots']['ideal'].endswith('Ideal_Sources')
    assert c['gate_min_provenance_variants_for_robustness']==2
    assert c['gate_require_provenance_channel_match'] is True
    s=(root/'run_basic.cmd').read_text(errors='ignore')
    assert 'prepare-provenance' in s and 'analyze-provenance' in s

def test_blind_provenance_robustness_uses_opaque_groups(tmp_path):
    import csv
    from sst_modal_clock.analyze import analyze_provenance
    work=tmp_path; (work/'analysis').mkdir();
    rows=[]
    for i,cid in enumerate(('c1','c2','c3')):
        for arm in (-1,0,1): rows.append({'candidate_id':f'{cid}_{arm}','pair_id':f'P{i}','carrier_id':cid,'topology_group_id':'opaqueG','probe_arm':arm,'data':'x','n_components':1,'certification_priority':False})
    (work/'blind_catalog.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    fields=['carrier_id','geometry_ok']
    with open(work/'analysis/blind_stage_a_carrier_summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();[w.writerow({'carrier_id':c,'geometry_ok':'True'}) for c in ('c1','c2','c3')]
    with open(work/'analysis/blind_stage_a_modal_results.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['carrier_id','material_multi_return_closure_median','material_cycles','material_harmonic_r2','material_spectral_power_fraction']);w.writeheader();[w.writerow({'carrier_id':c,'material_multi_return_closure_median':.2,'material_cycles':6,'material_harmonic_r2':.9,'material_spectral_power_fraction':.8}) for c in ('c1','c2','c3')]
    (work/'analysis/stage_a_candidates.json').write_text(json.dumps({'candidates':[{'carrier_id':'c1','topology_group_id':'opaqueG','period':1.0,'closure_median':.2,'channel':'natural'},{'carrier_id':'c2','topology_group_id':'opaqueG','period':1.1,'closure_median':.2,'channel':'natural'}]}))
    (work/'analysis/blind_stage_a_gauge_summary.json').write_text(json.dumps({'primary_gate':'X'}))
    cfg={'gate_min_provenance_variants_for_robustness':2,'gate_min_provenance_candidate_fraction':2/3,'gate_max_provenance_period_spread':.3,'gate_require_provenance_geometry_valid':True,'gate_require_provenance_channel_match':True}
    out=analyze_provenance(work,cfg)
    assert out['n_groups_with_provenance_robust_clock']==1
    assert out['provenance_identity_read'] is False and out['topology_identity_read'] is False


def test_real_gilbert_hl_aliases_are_not_confused_with_ht_index(tmp_path):
    from sst_modal_clock.sources import canonical_ideal_id
    assert canonical_ideal_id('L6a3',True)=='L6.2.1'
    assert canonical_ideal_id('L6a5',True)=='L6.3.1'
    assert canonical_ideal_id('L6a4',True)=='L6.3.2'
    assert canonical_ideal_id('L6n1',True)=='L6.3.3'
    assert canonical_ideal_id('L7n2',True)=='L7.2.8'
    assert canonical_ideal_id('L8a14',True)=='L8.2.1'
    assert canonical_ideal_id('L9a999',True)=='HTL9A999'
