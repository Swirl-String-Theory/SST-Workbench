import json
from sst_phase_delay_falsifier.analysis import evaluate

def test_evaluate_single_candidate_is_json_safe_inconclusive(tmp_path):
    cfg={
      'packet':{'min_valid_modes_per_candidate':1,'min_valid_candidate_fraction':0.8},
      'gates':{'min_candidates':8,'spearman_rho_max':-0.5,'spearman_p_max':0.05,'holdout_rmse_improvement_min':0.1,'holdout_min_train':3,'holdout_min_test':3}
    }
    pred={'config':cfg,'candidates':[{'blind_id':'B0001','delay_score':1.2,'packet_valid_modes':1,'median_packet_r2':0.9}]}
    meas={'candidates':[{'blind_id':'B0001','observed_growth_dimensionless':0.08}]}
    man={'items':[{'blind_id':'B0001','canonical_sha256':'a'*64}]}
    audit={'mode':'legacy_audit','confirmatory_eligible':False}
    paths=[]
    for name,obj in [('pred.json',pred),('measure.json',meas),('manifest.json',man),('audit.json',audit)]:
        p=tmp_path/name; p.write_text(json.dumps(obj)); paths.append(p)
    op=tmp_path/'eval.json'
    out=evaluate(*paths,op)
    assert out['status']=='INCONCLUSIVE'
    assert out['claim_status']=='RETROSPECTIVE_ONLY'
    assert out['n_valid']==1
    assert out['primary_rank_gate']['spearman_rho'] is None
    raw=op.read_text(); assert 'NaN' not in raw and 'Infinity' not in raw
    json.loads(raw)
