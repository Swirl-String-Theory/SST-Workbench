import json
from pathlib import Path

from sst_seed_falsifier.io import dump_json, load_json
from sst_seed_falsifier.workflow import _rpo_eligibility, stage_rpo


def _cfg():
    return {
        'rpo_loose_return_threshold': 0.14,
        'long_max_mesh_ratio': 0.50,
        'rpo_top_k': 3,
        'rpo_n': 32,
        'rpo_return_threshold': 0.09,
        'floquet_rho_max': 1.08,
        'mechanism_top_k': 2,
    }


def test_nonfinite_roundtrip_becomes_null_and_is_fail_closed(tmp_path):
    p = tmp_path / 'x.json'
    dump_json(p, {'best_return': float('inf'), 'best_return_time': float('nan')})
    row = load_json(p)
    assert row['best_return'] is None
    assert row['best_return_time'] is None
    ok, reason = _rpo_eligibility(
        {
            'completed': True,
            'best_return': row['best_return'],
            'best_return_time': row['best_return_time'],
            'max_mesh_ratio': 0.1,
        },
        _cfg(),
    )
    assert not ok
    assert reason == 'NO_FINITE_BEST_RETURN'


def test_stage_rpo_skips_null_return_without_crashing(tmp_path):
    out = tmp_path
    (out / 'stage40_long').mkdir()
    dump_json(out / 'stage40_long' / 'results.json', [
        {
            'candidate_id': 'CNULL',
            'completed': True,
            'best_return': None,
            'best_return_time': None,
            'max_mesh_ratio': 0.1,
        }
    ])
    rows = stage_rpo(out, _cfg())
    assert rows == []
    summary = load_json(out / 'stage50_rpo_floquet' / 'summary.json')
    assert summary['n_tested'] == 0
    assert summary['n_rejected_from_stage40'] == 1
    assert summary['rejected'][0]['reason'] == 'NO_FINITE_BEST_RETURN'
    assert summary['verdict'] == 'FAIL_NO_PROJECTED_STABLE_RPO'


def test_stage50_inherits_stage40_mesh_gate():
    ok, reason = _rpo_eligibility(
        {
            'completed': True,
            'best_return': 0.08,
            'best_return_time': 1.25,
            'max_mesh_ratio': 0.75,
        },
        _cfg(),
    )
    assert not ok
    assert reason == 'MESH_RATIO_GATE_FAIL'


def test_valid_loose_return_is_eligible_even_without_strict_return_count():
    # S40's loose RPO gate is intentionally broader than the strict return threshold.
    ok, reason = _rpo_eligibility(
        {
            'completed': True,
            'best_return': 0.12,
            'best_return_time': 1.25,
            'max_mesh_ratio': 0.2,
            'n_returns': 0,
        },
        _cfg(),
    )
    assert ok
    assert reason == 'ELIGIBLE'
