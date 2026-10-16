from pathlib import Path
import json,hashlib
from tools.parameter_readback import qualify_numeric
from tools.run_knotplot_campaign import _state_ok
ROOT=Path(__file__).resolve().parents[1]

def test_six_decimal_getter_round_trip_precision():
    q=qualify_numeric(1.114881670315,1.114882)
    assert q['pass'] and q['evidence']=='ROUNDED_GETTER'
    assert q['abs_error']<5e-7
    assert not qualify_numeric(1.114881670315,1.114884)['pass']
    assert not qualify_numeric(1.0,None)['pass']
    assert not qualify_numeric(float('nan'),0.0)['pass']

def test_tiny_expected_numeric_state_is_flagged_quantization_limited():
    q=qualify_numeric(2e-7,0.0)
    assert q['pass'] and q['evidence']=='ROUNDED_GETTER_QUANTIZATION_LIMITED'

def test_alias_axis_getter_and_switch_checked_on_and_off():
    priv=json.loads((ROOT/'private/axis_map.json').read_text())
    sid='R2';switch=priv['sectors'][sid].get('getter_switch')
    axis=priv['axes']['S3'];name=axis.get('getter_parameter');other=priv['axes']['S4']['parameter']
    defaults={axis['parameter']:1.4,other:2.0}
    cal={'defaults':defaults,'resolved_sectors':{sid:priv['sectors'][sid]['switch_parameter']}}
    c={'role':'reference','sector_id':sid,'axis_id':None,'multiplier':1.0}
    txt=f'BEGIN\n{switch} = on\n{name} = 1.400000\n{other} = 2.000000\nEND'
    ok,d=_state_ok(txt,c,priv,cal,'BEGIN','END')
    assert ok and d['checks']['S3'] and d['switch_reported']
    bad=txt.replace('= on','= off')
    assert not _state_ok(bad,c,priv,cal,'BEGIN','END')[0]
    off=dict(c,role='activation_control')
    assert _state_ok(bad,off,priv,cal,'BEGIN','END')[0]
    assert not _state_ok(txt.replace(f'{name} = 1.400000',''),c,priv,cal,'BEGIN','END')[0]

def test_legacy_import_is_separate_provenance_bound_overlay():
    s=(ROOT/'tools/import_prior_basic.py').read_text()
    assert 'qualification_overlay.json' in s
    assert 'original_runlog_sha256' in s and 'private_log_sha256' in s
    assert "shutil.copytree(src,dest)" in s
    driver=(ROOT/'tools/run_budget.py').read_text()
    assert 'source_qualification_overlay_sha256' in driver
    assert 'original_manifest_sha256' in driver
