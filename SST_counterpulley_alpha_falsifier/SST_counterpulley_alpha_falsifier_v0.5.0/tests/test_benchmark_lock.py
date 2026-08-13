from sst_counterpulley.benchmark import benchmark_blind_summary


def test_benchmark_stays_closed_without_H18():
    r=benchmark_blind_summary({'ready_for_alpha_unblinding':False,'verdict':'NO_RPO'})
    assert r['alpha_value_opened'] is False
    assert r['benchmark_phase'].startswith('BLOCKED')
