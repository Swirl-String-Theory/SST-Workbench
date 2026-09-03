from sst_seed_falsifier.io import dump_json, load_json
from sst_seed_falsifier.workflow import _rpo_eligibility, stage_rpo
from sst_seed_falsifier.evidence import dynamics_contract


def _cfg():
    return {
        'rpo_loose_return_threshold': 0.14,
        'long_max_mesh_ratio': 1.0,
        'rpo_min_observation_time': 1.2,
        'rpo_max_ds_cv_at_return': 0.32,
        'rpo_min_gap_over_ds_at_return': 1.0,
        'rpo_top_k': 3,
        'rpo_n': 32,
        'rpo_return_threshold': 0.09,
        'floquet_rho_max': 1.08,
        'mechanism_top_k': 2,
        'core_fraction': 0.08,
        'gamma': 1.0,
        'dt_factor': 0.025,
        'mesh_redistribution_method': 'segment_feedback',
        'mesh_rate': 4.0,
        'mesh_max_relative_rms': 1.0,
        'long_hard_ds_cv': 0.45,
        'min_gap_over_ds': 0.85,
        'require_native': False,
    }


def _valid_row(**kw):
    r={
        'candidate_id':'C1','mesh_gauge_certified':True,'observation_window_reached':True,
        'actual_t_final':2.0,'stop_reason':'COMPLETED','best_return':0.12,'best_return_time':1.25,
        'ds_cv_at_best_return':0.10,'gap_over_ds_at_best_return':2.0,'mesh_ratio_at_best_return':0.2,'max_mesh_ratio':0.2,'n_returns':0,
    }
    r.update(kw); return r


def test_nonfinite_roundtrip_becomes_null_and_is_fail_closed(tmp_path):
    p=tmp_path/'x.json'; dump_json(p,{'best_return':float('inf'),'best_return_time':float('nan')}); z=load_json(p)
    ok,reason=_rpo_eligibility(_valid_row(best_return=z['best_return'],best_return_time=z['best_return_time']),_cfg())
    assert not ok and reason=='NO_FINITE_BEST_RETURN'


def test_stage_rpo_skips_null_return_without_crashing(tmp_path):
    out=tmp_path; (out/'stage40_long').mkdir(); dump_json(out/'stage40_long'/'results.json',[_valid_row(candidate_id='CNULL',best_return=None,best_return_time=None)])
    dump_json(out/'stage40_long'/'summary.json',{'verdict':'INDETERMINATE_RPO_LONG_HORIZON_COVERAGE'})
    rows=stage_rpo(out,_cfg()); assert rows==[]
    s=load_json(out/'stage50_rpo_floquet'/'summary.json'); assert s['n_tested']==0 and s['n_rejected_from_stage40']==1
    assert s['rejected'][0]['reason']=='NO_FINITE_BEST_RETURN'; assert s['verdict']=='NOT_RUN_RPO_INDETERMINATE_LONG_NUMERICS'


def test_return_must_be_mesh_clean_locally():
    ok,reason=_rpo_eligibility(_valid_row(mesh_ratio_at_best_return=1.25),_cfg()); assert not ok and reason=='MESH_RATIO_BAD_AT_RETURN'


def test_return_must_be_mesh_clean_at_return():
    ok,reason=_rpo_eligibility(_valid_row(ds_cv_at_best_return=.5),_cfg()); assert not ok and reason=='MESH_QUALITY_BAD_AT_RETURN'


def test_valid_loose_return_can_survive_later_mesh_stop():
    ok,reason=_rpo_eligibility(_valid_row(stop_reason='MESH_QUALITY_STOP',actual_t_final=2.0,max_mesh_ratio=1.25,mesh_ratio_at_best_return=.2),_cfg())
    assert ok and reason=='ELIGIBLE'


def test_return_itself_must_be_after_minimum_observation_time():
    ok,reason=_rpo_eligibility(_valid_row(best_return_time=1.1),_cfg())
    assert not ok and reason=='RETURN_BEFORE_MIN_OBSERVATION_TIME'


def test_stage50_rejects_dynamics_contract_mismatch(tmp_path):
    out=tmp_path; (out/'stage40_long').mkdir()
    row=_valid_row(dynamics_contract_sha256='wrong')
    dump_json(out/'stage40_long'/'results.json',[row])
    dump_json(out/'stage40_long'/'summary.json',{'verdict':'PASS_NEAR_RPO_CANDIDATES'})
    assert stage_rpo(out,_cfg())==[]
    s=load_json(out/'stage50_rpo_floquet'/'summary.json')
    assert s['rejected'][0]['reason']=='DYNAMICS_CONTRACT_MISMATCH'
    assert s['dynamics_contract_sha256']==dynamics_contract(_cfg(),32)[1]
