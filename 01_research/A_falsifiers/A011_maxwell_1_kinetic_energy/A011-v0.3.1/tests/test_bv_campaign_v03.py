from pathlib import Path
from maxwell_sst_falsifier.campaign import run_campaign

ROOT=Path(__file__).resolve().parents[1]

def test_bv_synthetic_pass_has_no_closure_failures():
    r=run_campaign(ROOT/'examples'/'bv_synthetic_pass'/'config.json')
    assert r['dataset_kind']=='synthetic'
    assert not r['research_closure_failures']
    assert r['boltzmann']['occupation_fit'][0]['status']=='PASS'


def test_bv_synthetic_fail_triggers_multiple_gates():
    r=run_campaign(ROOT/'examples'/'bv_synthetic_fail'/'config.json')
    gates={x['gate'] for x in r['research_closure_failures']}
    assert 'BOLTZMANN_EQUILIBRIUM' in gates
    assert 'ENTROPIC_PRESSURE_FORCE' in gates
    assert 'VERLINDE_SCREEN' in gates
