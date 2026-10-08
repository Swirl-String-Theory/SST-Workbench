import json
from pathlib import Path
from a055_science import legacy


def _write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj),encoding='utf-8')


def test_provider_duplicate_failure_list_is_not_double_counted(tmp_path,monkeypatch):
    out=tmp_path/'old'; (out/'BLIND'/'dynamics').mkdir(parents=True)
    monkeypatch.setattr(legacy,'verify_a055_v030_output',lambda p:{'status':'PASS'})
    obj={
      'case':{'case_id':'C1'},
      'dynamic':{'particle_promotion_qualified':False,'providers':[{
        'provider_group':'P','rpo_accepted':False,
        'mode_reports':[{'mode_m':1,'qualified':False,
          'levels':[{'N':40,'status':'OSCILLATORY_PAIR_AVAILABLE'}],
          'failures':[{'N':56,'mode_m':1,'status':'NO_OSCILLATORY_PAIR'}]}],
        # Historical v0.3.0 provider-level duplicate must be ignored.
        'mode_cell_failures':[{'N':56,'mode_m':1,'status':'NO_OSCILLATORY_PAIR'}]
      }]}}
    _write(out/'BLIND'/'dynamics'/'C1.json',obj)
    r=legacy.summarize_legacy_controls(out)
    assert r['unique_mode_resolution_cells']==2
    assert r['available_legacy_oscillatory_cells']==1
    assert r['unavailable_cells']==1
