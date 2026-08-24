import json
from pathlib import Path
from sst_phase_delay_falsifier.analysis import evaluate

def test_evaluate_rejects_pseudorep_manifest(tmp_path):
 cfg={'packet':{'min_valid_modes_per_candidate':1,'min_valid_candidate_fraction':0.8},'gates':{'min_candidates':2,'spearman_rho_max':-0.5,'spearman_p_max':0.05,'holdout_rmse_improvement_min':0.1,'holdout_min_train':1,'holdout_min_test':1}}
 pred={'config':cfg,'candidates':[{'blind_id':'B0001','delay_score':1.0,'packet_valid_modes':1,'median_packet_r2':1.0},{'blind_id':'B0002','delay_score':0.0,'packet_valid_modes':1,'median_packet_r2':1.0}]}
 meas={'candidates':[{'blind_id':'B0001','observed_growth_dimensionless':0.0},{'blind_id':'B0002','observed_growth_dimensionless':1.0}]}
 man={'items':[{'blind_id':'B0001','canonical_sha256':'x'},{'blind_id':'B0002','canonical_sha256':'x'}]}
 audit={'mode':'legacy_audit','confirmatory_eligible':False}
 for n,d in [('p.json',pred),('m.json',meas),('man.json',man),('a.json',audit)]: (tmp_path/n).write_text(json.dumps(d))
 r=evaluate(tmp_path/'p.json',tmp_path/'m.json',tmp_path/'man.json',tmp_path/'a.json',tmp_path/'o.json')
 assert r['status']=='INCONCLUSIVE' and not r['dataset_gate']['pseudoreplication_free']
