from pathlib import Path
import json
from sst_modal_clock.sources import _ideal_records_xml, canonical_ideal_id, parse_fseries_file


def test_official_tl_link_container_parses_multiple_components(tmp_path):
    txt='''<DATA Title="x"><TL Id="L2a1"><STRING I="1"><Coeff I="0" A="-1,0,0" B="0,0,0"/><Coeff I="1" A="1,0,0" B="0,1,0"/></STRING><STRING I="2"><Coeff I="0" A="1,0,0" B="0,0,0"/><Coeff I="1" A="1,0,0" B="0,1,0"/></STRING></TL>'''
    p=tmp_path/'IdealLinks.txt'; p.write_text(txt)
    rows=_ideal_records_xml(txt,'ideal_links',p,32)
    assert len(rows)==1
    assert rows[0].topology_id=='L2.2.1'
    assert len(rows[0].components)==2
    assert rows[0].metadata['tag']=='TL'


def test_official_k11_ids_do_not_get_double_k_prefix():
    assert canonical_ideal_id('K11a247',False)=='K11A247'
    assert canonical_ideal_id('K11n17',False)=='K11N17'


def test_fremlin_suffix_is_retained_as_shape_variant(tmp_path):
    p=tmp_path/'knot.3_1p.fseries'
    p.write_text('1 0 0 1 0 0\n0.1 0 0 0.1 0.2 0\n')
    rows=parse_fseries_file(p,64)
    assert len(rows)==1
    assert rows[0].topology_id=='K3.1'
    assert rows[0].metadata['variant_label']=='p'


def test_fremlin_base_variant_label(tmp_path):
    p=tmp_path/'knot.6_1.fseries'
    p.write_text('1 0 0 1 0 0\n0.1 0 0 0.1 0.2 0\n')
    rows=parse_fseries_file(p,64)
    assert rows[0].metadata['variant_label']=='base'

def test_official_ht_style_fremlin_name_is_preserved(tmp_path):
    p=tmp_path/'knot.12a_1202z6.fseries'
    p.write_text('1 0 0 1 0 0\n0.1 0 0 0.1 0.2 0\n')
    rows=parse_fseries_file(p,64)
    assert rows[0].topology_id=='K12A1202'
    assert rows[0].metadata['variant_label']=='z6'


def test_compact_fremlin_catalogue_name_is_not_guessed(tmp_path):
    p=tmp_path/'knot.15331.fseries'
    p.write_text('1 0 0 1 0 0\n0.1 0 0 0.1 0.2 0\n')
    rows=parse_fseries_file(p,64)
    assert rows[0].topology_id=='FREMLIN15331'

def test_multiple_fremlin_variants_count_as_one_provenance_family(tmp_path):
    import csv, json
    from sst_modal_clock.analyze import analyze_provenance
    work=tmp_path; (work/'analysis').mkdir()
    # Three variants from one opaque source family + one relaxed + one ideal.
    specs=[('f1','famF'),('f2','famF'),('f3','famF'),('r1','famR'),('i1','famI')]
    rows=[]
    for j,(cid,fam) in enumerate(specs):
        for arm in (-1,0,1):
            rows.append({'candidate_id':f'{cid}_{arm}','pair_id':f'P{j}','carrier_id':cid,'topology_group_id':'opaqueK','provenance_group_id':fam,'probe_arm':arm,'data':'x','n_components':1,'certification_priority':False})
    (work/'blind_catalog.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with open(work/'analysis/blind_stage_a_carrier_summary.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['carrier_id','geometry_ok']);w.writeheader()
        for cid,_ in specs: w.writerow({'carrier_id':cid,'geometry_ok':'True'})
    with open(work/'analysis/blind_stage_a_modal_results.csv','w',newline='') as f:
        fields=['carrier_id','material_multi_return_closure_median','material_cycles','material_harmonic_r2','material_spectral_power_fraction'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for cid,_ in specs: w.writerow({'carrier_id':cid,'material_multi_return_closure_median':.2,'material_cycles':6,'material_harmonic_r2':.9,'material_spectral_power_fraction':.8})
    # Only two Fremlin variants pass: this is ONE source-family vote, not two.
    (work/'analysis/stage_a_candidates.json').write_text(json.dumps({'candidates':[{'carrier_id':'f1','topology_group_id':'opaqueK','period':1.0,'closure_median':.2,'channel':'natural'},{'carrier_id':'f2','topology_group_id':'opaqueK','period':1.02,'closure_median':.2,'channel':'natural'}]}))
    (work/'analysis/blind_stage_a_gauge_summary.json').write_text(json.dumps({'primary_gate':'X'}))
    cfg={'gate_min_provenance_source_families_for_robustness':2,'gate_min_provenance_candidate_fraction':2/3,'gate_max_provenance_period_spread':.3,'gate_require_provenance_geometry_valid':True,'gate_require_provenance_channel_match':True}
    out=analyze_provenance(work,cfg)
    assert out['n_groups_with_provenance_robust_clock']==0
    assert out['n_groups_with_single_source_family_clock_only']==1
