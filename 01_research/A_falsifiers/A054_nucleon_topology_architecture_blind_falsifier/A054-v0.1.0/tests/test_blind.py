from pathlib import Path
import json
from a054_ntaf.prepare import prepare
from a054_ntaf.blind import run_blind

def test_partial_prepare_without_workbench(tmp_path):
    s=prepare(tmp_path,None,n=72)
    assert s['status']=='PREPARED_PARTIAL_FAIL_CLOSED'
    m=json.loads((tmp_path/'BLIND_MANIFEST.json').read_text())
    assert m['scientific_ready'] is False
    assert m['candidate_count']==3
    text=(tmp_path/'BLIND_MANIFEST.json').read_text()
    for forbidden in ['P_B','N_B','5_2','6_1']:
        assert forbidden not in text

def test_blind_does_not_need_private_mapping(tmp_path):
    prepare(tmp_path,None,n=48)
    cfg=tmp_path/'cfg.json'; cfg.write_text(json.dumps({
      'resolutions':[36,48],'core_ratios':[0.02],'dynamic_steps':0,'dt':1e-5,
      'convergence_rel_tol':2.0,'objectivity_abs_tol':1e-7,'max_shape_drift':None,'max_linking_drift':0.3}))
    # Rename private directory to prove blind execution does not read it.
    (tmp_path/'_private').rename(tmp_path/'_private_hidden')
    a=run_blind(tmp_path,cfg)
    assert a['private_manifest_read'] is False
    assert a['semantic_identity_read'] is False
