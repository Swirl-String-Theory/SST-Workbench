from dataclasses import replace
from a069_v061.campaign_v062 import CASES,allowed_core_window,screening,resource_forecast
import pytest

def test_registered_both_160():
    assert CASES['A160'].n==160 and CASES['B160'].n==160

def test_fourier_a_160_no_xi_can_pass():
    w=allowed_core_window('A',160)
    assert not w['feasible']
    assert w['xi_min_resolution']>.25-1e-10
    assert .084<w['xi_max_geometry']<.086

def test_b_160_window_and_xi():
    assert screening('B',160,.28)['all_preconditions_met']

def test_a512_window_and_xi():
    assert screening('A',512,.08)['all_preconditions_met']

def test_a320_is_diagnostic_only():
    assert not screening('A',320,.08)['all_preconditions_met']

def test_high_b_256():
    assert screening('B',256,.28)['all_preconditions_met']

def test_b_too_large_core_rejected():
    assert not screening('B',160,.42)['all_preconditions_met']

def test_b_too_small_core_rejected():
    assert not screening('B',160,.08)['all_preconditions_met']

def test_forecast_increases():
    assert resource_forecast(512)['conservative_peak_gib']>resource_forecast(160)['conservative_peak_gib']

def test_resource_guard_fail():
    assert resource_forecast(160,2*2**30)['fits_budget'] is False

def test_rejects_bad_kind():
    with pytest.raises(KeyError): screening('C',160,.28)

def test_no_physical_claims_from_core_screen():
    assert screening('B',160,.28)['status']=='PASS_GEOMETRY_SCREEN_ONLY'

@pytest.mark.parametrize('case_id', ['B192_CORE024','B256_CORE024'])
def test_b_core_refinement_cases_screen(case_id):
    c=CASES[case_id]
    assert screening(c.kind,c.n,c.xi,c.box)['all_preconditions_met']
