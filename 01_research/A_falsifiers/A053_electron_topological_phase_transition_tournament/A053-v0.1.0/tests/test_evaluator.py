import json
from a053_etptf.selftest_data import instrument_manifest
from a053_etptf.evaluator import evaluate_manifest

def test_selftest_all_survive():
    cfg=json.load(open('configs/basic.json','r',encoding='utf-8'))
    out=evaluate_manifest(instrument_manifest(),cfg)
    assert set(out['survivors'])=={'H0','H1','H2','H3'}
    assert out['verdict']=='NON_UNIQUE_SURVIVORS_TESTED_DOMAIN'


def test_ideal_euler_cannot_support_topology_change():
    cfg=json.load(open('configs/basic.json','r',encoding='utf-8'))
    m=instrument_manifest()
    m['producer']['physics_class']='ideal_euler_no_reconnection'
    out=evaluate_manifest(m,cfg)
    assert out['hypotheses']['H2']['status']!='PASS'
    assert out['hypotheses']['H3']['status']!='PASS'
