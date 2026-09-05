import json
from pathlib import Path
from sst_phase_delay_falsifier.analysis import evaluate


def test_evaluate_single_candidate_is_json_safe_inconclusive(tmp_path):
    cfg={"gates":{"min_candidates":8,"spearman_rho_max":-0.5,"spearman_p_max":0.05,"holdout_rmse_improvement_min":0.1}}
    pred={"config":cfg,"candidates":[{"blind_id":"B0001","delay_score":1.2,"linear_sigma0":0.1,"delay_feature_z":-0.3}]}
    meas={"candidates":[{"blind_id":"B0001","observed_growth":0.08}]}
    pp=tmp_path/'pred.json'; mp=tmp_path/'measure.json'; op=tmp_path/'eval.json'
    pp.write_text(json.dumps(pred)); mp.write_text(json.dumps(meas))
    out=evaluate(pp,mp,op)
    assert out['status']=='INCONCLUSIVE'
    assert out['status_reason']=='insufficient_candidates: 1 < 8'
    assert out['primary']['spearman_rho'] is None
    assert out['primary']['p'] is None
    assert out['global_gain_holdout']['kappa'] is None
    # Strict parse proves there are no NaN/Infinity tokens in the result file.
    raw=op.read_text()
    assert 'NaN' not in raw and 'Infinity' not in raw
    parsed=json.loads(raw)
    assert parsed['n']==1
