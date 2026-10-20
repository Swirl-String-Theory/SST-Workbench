from pathlib import Path
import json
import numpy as np
import pytest
from src.library_census import ROOT,fremlin_coeff,fremlin_short,ideal_strings,resample
from src.topology3d import knot_signature,gauss_link
from src.long_euler import selected_cases,normalize_curves,ring_local,topology_checkpoint
from src.qualification import build
import xml.etree.ElementTree as ET

DATA=ROOT/'external_pklsa/source_libraries'

def test_fremlin_harmonic_offset_trifoil():
    p=fremlin_coeff((DATA/'fremlin/3_1/knot.3_1.fseries').read_bytes())
    assert knot_signature(p)['alexander_det_at_minus_one']==3

def test_fremlin_figure8():
    p=fremlin_coeff((DATA/'fremlin/4_1/knot.4_1.fseries').read_bytes())
    assert knot_signature(p)['alexander_det_at_minus_one']==5

def test_fremlin_7_1():
    p=fremlin_coeff((DATA/'fremlin/7_1/knot.7_1.fseries').read_bytes())
    assert knot_signature(p)['alexander_det_at_minus_one']==7

def test_short_not_independent():
    q=fremlin_short((DATA/'fremlin/3_1/knot.3_1.short').read_bytes())
    assert knot_signature(q)['alexander_det_at_minus_one']==3

def test_invalid_fremlin_empty_fails_closed():
    with pytest.raises(ValueError):fremlin_coeff((DATA/'fremlin/8_5/knot.8_5.fseries').read_bytes())

def test_ideal_link_l4a1():
    text=(DATA/'idealLinks.txt').read_text()
    el=ET.fromstring('<R>'+text+'</R>').find(".//TL[@Id='L4a1']")
    curves=ideal_strings(el)
    assert len(curves)==2
    assert abs(abs(gauss_link(curves[0],curves[1],5))-2)<.075

def test_n300_preserved_for_long_euler():
    x=selected_cases()['KP_3_1_N300']
    assert len(x['curves'][0])==300

def test_all_three_source_providers():
    x=selected_cases()
    assert {x[k]['provider'] for k in x}=={'knotplot_N300','fremlin_fseries','ideal_links'}

def test_3d_knot_topology_reference():
    c,_=normalize_curves(selected_cases()['KP_3_1_N300']['curves'])
    assert topology_checkpoint(c)['components'][0]['alexander_det_m1']==3

def test_2d_mesh_excluded():
    import numpy as np
    with np.load(ROOT/'external_pklsa/reference/PKLSA_3_1_CANDIDATE_SURFACE.npz',allow_pickle=False) as z:
        assert 'vertices_m' in z.files and 'triangles' in z.files and 'points' not in z.files

def test_fixed_final_time_for_comparison():
    r=json.loads((ROOT/'results/CONVERGENCE_ASSESSMENT.json').read_text())
    assert len(r['cases'])==5
    for v in r['cases'].values():
        assert all(q['duration_model']==2.4 and q['sigma_model']==.5 for q in v['grid_evolutions'])

def test_temporal_refinement_stays_independent_of_spatial():
    r=json.loads((ROOT/'results/CONVERGENCE_ASSESSMENT.json').read_text())
    v=r['cases']['KP_3_1_N300']
    assert v['temporal_refinement_same_time_marker_rms']<v['same_time_marker_differences'][1]['rms_box_length']
