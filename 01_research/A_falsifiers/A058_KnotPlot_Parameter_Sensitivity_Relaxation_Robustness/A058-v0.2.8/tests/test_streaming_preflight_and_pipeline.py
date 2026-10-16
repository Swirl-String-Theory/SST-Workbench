from pathlib import Path
import json, math


def _points():
    return ''.join(f'{(2+math.cos(3*t))*math.cos(2*t):.17g} {(2+math.cos(3*t))*math.sin(2*t):.17g} {math.sin(3*t):.17g}\n' for t in (2*math.pi*i/300 for i in range(300)))


def _run_mock(tmp_path,monkeypatch,is_safe, warning_interleaved=False):
    from tools import run_knotplot_campaign as runner
    root=tmp_path/'instance'; (root/'private').mkdir(parents=True)
    data=_points();seed=root/'private/seed.txt';seed.write_text(data,encoding='utf-8')
    original=root/'private/map.json'
    fullroot=Path(__file__).resolve().parents[1]
    priv=json.loads((fullroot/'private/axis_map.json').read_text())
    calibration={'resolved_sectors':{'R1':priv['sectors']['R1']['switch_parameter']},
                  'defaults':{priv['axes']['S2']['parameter']:1.0}}
    class FakeKP:
        def __init__(self,exe,wd,log):self.log=log;self.iter=0;self.messages=[]
        def send(self,*lines):
            for line in lines:
                if line.startswith('echo '):self.messages.append(line[5:])
                elif line=='safe':
                    if warning_interleaved and is_safe:self.messages.append('Current position is  *** khat_mag is zero! the knot embedding may be bad or the projection is not well defined!\nsafe.')
                    else:self.messages.append('Current position is safe' if is_safe else 'Current position is not safe')
                elif line=='parameters':self.messages.append(f'iteration = {self.iter}')
                elif line.startswith('go '):self.iter+=int(line[3:])
                elif line.startswith('save '):
                    name=line.removeprefix('save ').removesuffix(' ascii');Path(name).write_text(data,encoding='utf-8')
                else:pass
            self.log.write_text('\n'.join(self.messages)+'\n',encoding='utf-8')
        def close(self):return 0
        def kill(self):pass
    monkeypatch.setattr(runner,'ROOT',root)
    monkeypatch.setattr(runner,'KP',FakeKP)
    result=runner._streaming_preflight(tmp_path,tmp_path,seed,priv,calibration,{'quantum_iterations':32,'per_block_timeout_seconds':1})
    assert (root/'private/stream_preflight/result.json').is_file()
    return result


def test_stream_probe_checks_real_go_and_both_exports(tmp_path,monkeypatch):
    r=_run_mock(tmp_path,monkeypatch,True)
    assert r['status']=='PASS'
    assert r['observed_iteration']==32
    assert r['safe_verified'] and r['before_export_ok'] and r['after_export_ok']


def test_stream_probe_rejects_unsafe_without_go(tmp_path,monkeypatch):
    r=_run_mock(tmp_path,monkeypatch,False)
    assert r['status']=='FAIL'
    assert not r['safe_verified']
    assert r['before_export_ok'] and not r['after_export_ok']


def test_pipeline_reads_instance_thresholds_not_framework_profile(tmp_path,monkeypatch):
    from experiment import pipeline
    root=tmp_path; (root/'configs').mkdir();(root/'campaign/results').mkdir(parents=True)
    cfg=json.loads((Path(__file__).resolve().parents[1]/'configs/default.json').read_text())
    (root/'configs/default.json').write_text(json.dumps(cfg))
    monkeypatch.setattr(pipeline,'analyze',lambda root:{'available':False,'condition_count':0,'runlog_entries':0,'coordinate_complete_fraction':0,'ladder_ok':False,'run_failures':271,'axis_summaries':{}})
    class Gate:
        def __init__(self,enabled=True):self.enabled=enabled
    class Ledger:
        def __init__(self):self.defs={f'G{i}':Gate(i not in (4,6,7)) for i in range(10)};self.statuses={}
        def record(self,gid,status,**kwargs):self.statuses[gid]=status
    ledger=Ledger()
    output=pipeline.run_scientific_pipeline(root,{'project':{'name':'Test','version':'v0.2.8'}},ledger,'FULL')
    assert ledger.statuses['G0']=='PASS'
    assert ledger.statuses['G2']=='FAIL'
    assert ledger.statuses['G8']=='FAIL'
    assert (root/'Test_v0.2.8-outputs/A058_SLIDER_ANALYSIS.json').is_file()


def test_stream_probe_handles_real_warning_interleaving(tmp_path, monkeypatch):
    r=_run_mock(tmp_path,monkeypatch,True,warning_interleaved=True)
    assert r['status']=='PASS'
    assert r['observed_iteration']==32
    assert r['safe_verified']
    assert r['safety_diagnostic']['status']=='SAFE_WITH_WARNING'
    assert r['safety_diagnostic']['warning_count']==1
    assert r['before_export_ok'] and r['after_export_ok']
