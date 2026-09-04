import json
from pathlib import Path
from sst_blind.ladder import analyze_ladder


def _r(g,boundary=0.01,epsdrift=0.0):
    return {'status':'LINEAR_PASS' if g<=0.12 else 'LINEAR_FAIL','metrics':{'normalized_growth':g,'dominant_kmax_boundary_weight':boundary,'jacobian_robustness_relative_drift_max':epsdrift,'rpo_found':False,'floquet_valid':False},'dominant_mode_diagnostics':{'kmax_boundary_weight':boundary,'kmax_basis_present':True}}


def test_good_ladder_converged_pass():
    plan=json.loads(Path('configs/hr_ladder/ladder_plan.json').read_text())
    gs=[0.0800,0.0790,0.0785,0.0783,0.0782,0.0782]
    payload={}
    for rd,g in zip(plan['rungs'],gs):
        payload[rd['name']]={'results':{'B01':_r(g,0.01,0.10 if rd['index']==5 else 0.0)},'mapping':{'B01':{'source':'synthetic:test','topology_class':'knot','canonical_id':'x'}}}
    rec=analyze_ladder(payload,plan)[0]
    assert rec['classification']=='CONVERGED_PASS'
    assert rec['spatial_tail']['converged']
    assert rec['spectral_tail']['converged']
    assert rec['kmax_boundary_ok']


def test_kmax_boundary_forces_unresolved():
    plan=json.loads(Path('configs/hr_ladder/ladder_plan.json').read_text())
    gs=[0.20,0.19,0.185,0.182,0.181,0.181]
    payload={}
    for rd,g in zip(plan['rungs'],gs):
        payload[rd['name']]={'results':{'B01':_r(g,0.40)},'mapping':{'B01':{'source':'synthetic:test','topology_class':'knot','canonical_id':'x'}}}
    rec=analyze_ladder(payload,plan)[0]
    assert rec['classification']=='UNRESOLVED'
    assert 'dominant_mode_hits_kmax_boundary' in rec['cpu_fp64_reasons']
