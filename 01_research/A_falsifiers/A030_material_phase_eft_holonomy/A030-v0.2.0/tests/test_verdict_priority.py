"""Physical G4 FAIL must not be erased by T/S_CONV noise."""

from sst_eft_falsifier.campaign import exit_code_for_overall


def _overall_from_counts(counts, *, t_enabled=True, s_enabled=True):
    cert_fail = (t_enabled and counts['T_CONV']['FAIL'] > 0) or (
        s_enabled and counts['S_CONV']['FAIL'] > 0
    )
    physical_fail = counts['G4_DISPERSION']['FAIL'] > 0
    physical_inconclusive = (
        counts['G4_DISPERSION']['SKIP'] > 0
        and counts['G4_DISPERSION']['FAIL'] == 0
        and counts['G4_DISPERSION']['PASS'] == 0
    )
    diagnostic_fail = any(
        counts[g]['FAIL'] > 0 for g in ['G1_REPARAM', 'G2_PHASE', 'G3_REDUNDANCY']
    )
    if physical_fail:
        return 'CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS' if cert_fail else 'CLOSURE_FAIL'
    if cert_fail:
        return 'NUMERICALLY_INCONCLUSIVE'
    if physical_inconclusive:
        return 'INCONCLUSIVE'
    if t_enabled or s_enabled:
        return 'CLOSURE_SURVIVED_WITH_WARNINGS' if diagnostic_fail else 'CLOSURE_SURVIVED'
    return 'PRELIMINARY_SURVIVED_WITH_WARNINGS' if diagnostic_fail else 'PRELIMINARY_SURVIVED'


def test_physical_fail_beats_cert_fail():
    counts = {
        'G1_REPARAM': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G2_PHASE': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G3_REDUNDANCY': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G4_DISPERSION': {'PASS': 0, 'FAIL': 2, 'SKIP': 1},
        'T_CONV': {'PASS': 0, 'FAIL': 1, 'SKIP': 0},
        'S_CONV': {'PASS': 0, 'FAIL': 1, 'SKIP': 0},
    }
    overall = _overall_from_counts(counts)
    assert overall == 'CLOSURE_FAIL_WITH_NUMERICAL_WARNINGS'
    assert exit_code_for_overall(overall) == 0


def test_all_g4_skip_is_inconclusive():
    counts = {
        'G1_REPARAM': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G2_PHASE': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G3_REDUNDANCY': {'PASS': 1, 'FAIL': 0, 'SKIP': 0},
        'G4_DISPERSION': {'PASS': 0, 'FAIL': 0, 'SKIP': 3},
        'T_CONV': {'PASS': 0, 'FAIL': 0, 'SKIP': 3},
        'S_CONV': {'PASS': 0, 'FAIL': 0, 'SKIP': 3},
    }
    overall = _overall_from_counts(counts, t_enabled=False, s_enabled=False)
    assert overall == 'INCONCLUSIVE'
    assert exit_code_for_overall(overall) == 2


def test_exit_codes():
    assert exit_code_for_overall('CLOSURE_FAIL') == 0
    assert exit_code_for_overall('CLOSURE_SURVIVED') == 0
    assert exit_code_for_overall('INCONCLUSIVE') == 2
    assert exit_code_for_overall('NUMERICALLY_INCONCLUSIVE') == 2
