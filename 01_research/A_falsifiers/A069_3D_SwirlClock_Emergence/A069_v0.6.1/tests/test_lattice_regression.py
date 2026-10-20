import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from a069_v061.lattice_graph_legacy import windings,component_diagnostics,compare_snapshots

def coords(n=24):
    a=2*np.pi*np.arange(n)/n
    return np.meshgrid(a,a,a,indexing='ij')

def straight(n=24):
    x,y,z=coords(n)
    return (np.sin(x+.13)+1j*np.sin(y+.27)).astype(complex)

def rings(n=24):
    x,y,z=coords(n)
    return np.cos(x)+np.cos(y)-1.36 + 1j*np.sin(z+.18)

def test_no_vortex():
    result=component_diagnostics(np.ones((24,)*3,complex));assert result['total_edges']==0 and result['graph_consistent']
def test_four_periodic_lines():
    r=component_diagnostics(straight())
    assert r['graph_consistent'] and r['component_count']==4
    assert all(abs(c['periodic_homology'][2])==1 for c in r['components'])
    assert all(c['simple_oriented_cycle'] for c in r['components'])
def test_two_closed_rings():
    r=component_diagnostics(rings())
    assert r['graph_consistent'] and r['component_count']==2
    assert all(c['periodic_homology']==[0,0,0] for c in r['components'])
def test_phase_gauge_invariant():
    p=straight();ref=component_diagnostics(p)
    for phase in (0.25,2.3,-2.1):
        other=component_diagnostics(p*np.exp(1j*phase))
        assert other['face_counts']==ref['face_counts']
        assert other['component_count']==ref['component_count']
def test_conjugation_reverses_flux():
    a=windings(straight());b=windings(np.conj(straight()))
    assert all(np.array_equal(v,-b[k]) for k,v in a.items())
def test_integer_translation_invariant():
    r=component_diagnostics(straight());q=component_diagnostics(np.roll(straight(),[2,3,1],axis=[0,1,2]))
    assert r['component_count']==q['component_count']
    assert sorted(c['edges'] for c in r['components'])==sorted(c['edges'] for c in q['components'])
def test_no_knot_automatic_promotion():
    r=component_diagnostics(rings()); assert r['knot_type_certified'] is False
    assert r['physical_clock_frequency'] is None
def test_no_reconnection_automatic_promotion():
    r=compare_snapshots(straight(),rings());assert r['status']=='UNRESOLVED_TOPOLOGY'
    assert len(r['requires'])>=4
def test_field_reject_invalid():
    with pytest.raises(ValueError):component_diagnostics(np.zeros((12,)*3,complex))
    with pytest.raises(ValueError):component_diagnostics(np.ones((12,10,12),complex))
