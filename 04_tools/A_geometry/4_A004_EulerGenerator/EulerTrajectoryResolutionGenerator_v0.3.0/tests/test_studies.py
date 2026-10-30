"""Regression tests for independent Euler study axes and fail-closed semantics."""
import numpy as np
import pytest
from resolver.studies import (target_resolution,plan_runs,_aligned_error,even_up,SCHEMA)
from resolver.run import estimate_gib


def test_qualification_nominal_minimums():
    assert target_resolution('a075')==260
    assert target_resolution('a077')==170
    assert target_resolution('a075',effective=True)==390
    assert target_resolution('a077',effective=True)==254


def test_budget_increases_sharply():
    assert estimate_gib(390)>estimate_gib(260)>estimate_gib(96)
    assert estimate_gib(254)>estimate_gib(170)>estimate_gib(96)


def test_all_five_studies_are_orthogonal():
    studies=['spatial','temporal','core','box','perturb']
    rows=plan_runs('a077','qualification',studies,4,False,.02,.001,8,44)
    groups={g:[x for x in rows if x['study']==g] for g in studies}
    assert {k:len(v) for k,v in groups.items()} == {'spatial':3,'temporal':3,'core':3,'box':3,'perturb':7}
    assert len({r['tag'] for r in rows})==19
    assert all(r['t_final']==.02 for r in rows)
    assert {r['dt_request'] for r in groups['spatial']}=={.001}
    assert all(r['geometric_radius_over_dx']>=4.0 for r in groups['spatial'])
    assert {r['box_length'] for r in groups['temporal']}=={8.}
    assert {r['core_factor'] for r in groups['box']}=={1.}
    assert {r['n'] for r in groups['core']}=={170}
    assert len({r['box_length']/r['n'] for r in groups['box']})<=3
    assert {r['seed'] for r in groups['perturb'] if r['perturb']>.0}=={45,46,47}


def test_a075_changes_spectral_core_but_not_geometric_radius():
    rows=plan_runs('a075','smoke',['core'],4,False,.001,.001,5,7)
    assert {r['n'] for r in rows}=={32}
    assert {r['core_factor'] for r in rows}=={.8,1.,1.2}
    assert {r['geometric_radius_over_dx'] for r in rows}=={round(.154*32/10,5)}


def test_smoke_not_qualified():
    for provider in ['a075','a077']:
        p=plan_runs(provider,'smoke',['spatial'],4,False,.002,.001,8,22)
        assert len(p)==3
        assert p[-1]['spectral_effective_radius_cells'] < 4.


def test_alignment_interpolates_time_not_frame():
    t=np.array([0.,.5,1.])
    reference={'time':t,'x':np.tile(t[:,None,None],(1,2,3)),'v':np.ones((3,2,3))}
    t2=np.array([0.,.25,.5,.75,1.])
    other={'time':t2,'x':np.tile(t2[:,None,None],(1,2,3)),'v':np.ones((5,2,3))}
    assert _aligned_error(reference,other,.1)['max_trajectory_position_to_smallest_radius']<1e-12


def test_different_physical_final_time_refused():
    ref={'time':np.array([0.,1.]),'x':np.zeros((2,1,3))}
    other={'time':np.array([0.,2.]),'x':np.zeros((2,1,3))}
    with pytest.raises(ValueError,match='DIFFERENT_FINAL_TIME'):
        _aligned_error(ref,other,.2)


def test_invalid_resolution_refused():
    for x in (0,-1):
        with pytest.raises(ValueError):target_resolution('a077',x)
    with pytest.raises(ValueError):target_resolution('bad')


def test_schema_and_grid_even():
    assert SCHEMA.endswith('-2')
    assert even_up(169.3)==170
    assert even_up(16)==16
