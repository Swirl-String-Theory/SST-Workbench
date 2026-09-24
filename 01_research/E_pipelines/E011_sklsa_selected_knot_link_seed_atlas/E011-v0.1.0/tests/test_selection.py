from pathlib import Path
import sys
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from sklsa.selection import canonical_topology_from_text,load_selection

def test_ids():
    assert canonical_topology_from_text('knots/8_5/final.xyz')=='8_5'
    assert canonical_topology_from_text('knot.3.1.fseries')=='3_1'
    assert canonical_topology_from_text('links/L6a4/final.vect')=='L6a4'

def test_low_crossing_selection_complete():
    cfg=load_selection(HERE/'configs'/'selected_topologies.json')
    assert len(cfg['core_knots'])==35
    assert cfg['core_knots'][0]=='3_1'
    assert cfg['core_knots'][-1]=='8_21'
    assert all(not x.startswith(('9_','10_','11_')) for x in cfg['core_knots'])

def test_poc_contains_borromean():
    cfg=load_selection(HERE/'configs'/'selected_topologies.json')
    assert 'L6a4' in cfg['poc']
