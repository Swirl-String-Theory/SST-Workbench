from pathlib import Path
import json
import numpy as np
from a054_ntaf.prepare import prepare
from a054_ntaf.blind import run_blind, _polarity_group, _dt_steps


def test_partial_prepare_without_workbench(tmp_path):
    s=prepare(tmp_path,None,n=72)
    assert s['status']=='PREPARED_PARTIAL_FAIL_CLOSED'
    m=json.loads((tmp_path/'BLIND_MANIFEST.json').read_text())
    assert m['scientific_ready'] is False
    assert m['candidate_count']==3
    text=(tmp_path/'BLIND_MANIFEST.json').read_text()
    for forbidden in ['5_2','6_1','uud','udd','borromean','triple_gear']:
        assert forbidden.lower() not in text.lower()


def test_blind_does_not_need_private_mapping(tmp_path):
    prepare(tmp_path,None,n=48)
    cfg=tmp_path/'cfg.json'; cfg.write_text(json.dumps({
      'resolutions':[36,48],'core_ratios':[0.02],'dynamic_t_final':0.0,
      'dt_reference':1e-5,'dt_reference_resolution':36,
      'convergence_rel_tol':2.0,'convergence_abs_tol':{'default':2.0},
      'objectivity_abs_tol':1e-6,'max_shape_drift':0.3,'max_linking_drift':0.3,
      'backend_policy':'allow_numpy','separation_epsilon':0.035,
      'circulation_sectors':['Q0','Q1','Q2','Q3','Q4','Q5','Q6','Q7']}))
    (tmp_path/'_private').rename(tmp_path/'_private_hidden')
    a=run_blind(tmp_path,cfg)
    assert a['private_manifest_read'] is False
    assert a['semantic_identity_read'] is False


def test_constant_final_time_dt_scaling():
    cfg={'resolutions':[72,108],'dynamic_t_final':3.2e-4,'dt_reference':4e-5,'dt_reference_resolution':72}
    dt72,n72=_dt_steps(cfg,72); dt108,n108=_dt_steps(cfg,108)
    assert abs(dt72*n72-cfg['dynamic_t_final'])<1e-15
    assert abs(dt108*n108-cfg['dynamic_t_final'])<1e-15
    assert dt108 < dt72 and n108 > n72


def test_preregistered_polarity_gate():
    sectors=['Q0','Q1','Q2','Q3']
    cross={'Q0':-0.2,'Q1':0.3,'Q2':0.25,'Q3':0.28}
    rel={'Q0':0.9,'Q1':0.5,'Q2':0.55,'Q3':0.52}
    fine=[{'sector':s,'cross_stabilization':cross[s],'rel_eq_residual':rel[s]} for s in sectors]
    stat={s:{'status':'QUALIFIED_SHORT_HORIZON'} for s in sectors}
    p=_polarity_group(fine,'Q0',['Q1','Q2','Q3'],stat)
    assert p['selection_gate'] is True
    assert p['qualified_sign_reversal_count']==3
    assert p['delta_cross_median']>0
