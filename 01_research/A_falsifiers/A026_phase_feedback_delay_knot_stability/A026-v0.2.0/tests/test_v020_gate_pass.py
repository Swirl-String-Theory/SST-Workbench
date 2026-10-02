import json
from sst_phase_delay_falsifier.analysis import evaluate

def test_synthetic_strict_negative_signal_passes_both_gates(tmp_path):
    cfg={'packet':{'min_valid_modes_per_candidate':1,'min_valid_candidate_fraction':0.8},
         'gates':{'min_candidates':8,'spearman_rho_max':-0.5,'spearman_p_max':0.05,'holdout_rmse_improvement_min':0.1,'holdout_min_train':3,'holdout_min_test':3}}
    pred={'config':cfg,'candidates':[]}; meas={'candidates':[]}; man={'items':[]}
    for i in range(10):
        bid=f'B{i+1:04d}'; h=f'{i+100:064x}'; D=float(i); Y=20.0-2.0*D
        pred['candidates'].append({'blind_id':bid,'delay_score':D,'packet_valid_modes':2,'median_packet_r2':0.99})
        meas['candidates'].append({'blind_id':bid,'observed_growth_dimensionless':Y})
        man['items'].append({'blind_id':bid,'canonical_sha256':h})
    audit={'mode':'legacy_audit','confirmatory_eligible':False}
    paths=[]
    for n,d in [('p.json',pred),('m.json',meas),('man.json',man),('a.json',audit)]:
        q=tmp_path/n; q.write_text(json.dumps(d)); paths.append(q)
    r=evaluate(*paths,tmp_path/'out.json')
    assert r['status']=='PASS'
    assert r['claim_status']=='RETROSPECTIVE_ONLY'
    assert r['primary_rank_gate']['pass'] and r['negative_slope_holdout_gate']['pass']
