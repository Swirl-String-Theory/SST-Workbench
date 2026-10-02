import numpy as np
import pytest
from sst_torsion.observations import spectrum, leakage_diagnostic, branch_admission, REQUIRED_QUALIFICATION


def test_spectrum_reports_resolution_without_inventing_eigenfrequency():
    t = np.arange(2048)/128
    result = spectrum(t, np.sin(2*np.pi*8*t))
    peak = np.argmax(result['power'])
    assert abs(result['frequency'][peak]-8) < 0.51
    assert result['measured_eigenfrequency'] is None
    assert result['status'] == 'INDETERMINATE'


def test_coherence_exposes_shared_signal_and_rejects_single_window():
    rng = np.random.default_rng(70)
    t = np.arange(4096)/128
    x = rng.normal(size=len(t))
    shared = leakage_diagnostic(t, x, 3*x)
    independent = leakage_diagnostic(t, x, rng.normal(size=len(t)))
    assert np.median(shared['coherence']) > .9999
    assert np.median(independent['coherence']) < .1
    assert shared['independent_nonoverlapping_segments'] >= 4
    assert leakage_diagnostic(t[:32], x[:32], x[:32])['status'] == 'INDETERMINATE'


def test_no_phase_or_qualification_never_becomes_negative_physics_result():
    r = branch_admission({'evidence_kind':'INDEPENDENT_DYNAMICS',
                          'candidate_equation_drives_data':False,
                          'qualification':{'independent_core_state':'PASS'}})
    assert r['decision'] == 'AMBIGUOUS'
    assert r['physical_hypothesis'] == 'NOT_YET_TESTED'
    assert not r['promotion_allowed'] and not r['model_competition_executed']
    assert 'material_observable' in r['missing_prerequisites']


def test_even_qualified_input_does_not_masquerade_as_implemented_model_competition():
    r = branch_admission({'evidence_kind':'INDEPENDENT_DYNAMICS',
        'candidate_equation_drives_data':False,
        'qualification':dict.fromkeys(REQUIRED_QUALIFICATION,'PASS')})
    assert r['status'] == 'NOT-IMPLEMENTED' and not r['promotion_allowed']


@pytest.mark.parametrize('bad', [np.arange(8)[::-1], [0,1,2,3,4,5,6,8], [0,1,2,3,4,5,6,np.nan]])
def test_invalid_timing_rejected(bad):
    with pytest.raises(ValueError):
        spectrum(bad, np.ones(8))
