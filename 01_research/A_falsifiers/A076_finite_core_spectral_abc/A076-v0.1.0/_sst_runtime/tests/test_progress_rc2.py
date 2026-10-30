"""Progress regression tests: no false scientific claims, even if native backend is silent."""
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from sst_falsifier import progress


def test_progress_levels_are_measured_and_auditable(tmp_path):
    buffer=io.StringIO()
    log=tmp_path/'RUN_PROGRESS.jsonl'
    with progress.ProgressSession('FULL',stream=buffer,heartbeat_seconds=0.5) as p:
        p.bind_log(log)
        for index,n in enumerate((128,256,512),1):
            with progress.refinement('spatial',level=index,total=3,resolution=n,final_time=1.0):
                pass
        for index,dt in enumerate((.01,.005,.0025),1):
            with progress.refinement('temporal',level=index,total=3,dt=dt,final_time=1.0):
                pass
        p.freeze_log()
        before=log.read_bytes()
        progress.event('PACKAGE','DONE')
        assert log.read_bytes()==before
    records=[json.loads(line) for line in before.decode().splitlines()]
    assert len(records)==12
    spatial_done=[x for x in records if x['phase']=='SPATIAL_REFINEMENT' and x['state']=='DONE']
    temporal_done=[x for x in records if x['phase']=='TEMPORAL_REFINEMENT' and x['state']=='DONE']
    assert [x['completed'] for x in spatial_done]==[1,2,3]
    assert [x['completed'] for x in temporal_done]==[1,2,3]
    assert all(x['total']==3 for x in records)
    assert 'SPATIAL_REFINEMENT' in buffer.getvalue()
    assert 'TEMPORAL_REFINEMENT' in buffer.getvalue()
    assert 'PACKAGE DONE' in buffer.getvalue()


def test_progress_thread_heartbeat_when_not_supervised(monkeypatch):
    monkeypatch.delenv('SST_PROGRESS_SUPERVISED',raising=False)
    buffer=io.StringIO()
    with progress.ProgressSession('FULL',stream=buffer,heartbeat_seconds=.02):
        with progress.phase('SPATIAL_REFINEMENT',completed=0,total=3,level=1):
            time.sleep(.08)
    assert '[SST][HEARTBEAT] RUNNING' in buffer.getvalue()
    assert 'SPATIAL_REFINEMENT' in buffer.getvalue()


def test_progress_rejects_unmeasured_fake_counters():
    with progress.ProgressSession('FULL',stream=io.StringIO(),heartbeat_seconds=.5):
        with pytest.raises(ValueError,match='provided together'):
            progress.event('BACKEND','START',completed=1)
        with pytest.raises(ValueError,match='Invalid measured'):
            progress.event('BACKEND','START',completed=4,total=3)
        with pytest.raises(ValueError,match='refinement kind'):
            progress.refinement('unknown',level=1,total=2)


def test_external_supervisor_heartbeat_independent_of_worker(tmp_path):
    # The subprocess is completely silent for several heartbeat intervals.
    from importlib.util import module_from_spec,spec_from_file_location
    source=Path(__file__).resolve().parents[1]/'instance_template'/'progress_supervisor.py'
    spec=spec_from_file_location('sst_test_supervisor',source)
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    output=io.StringIO()
    rc=module.run_monitored([sys.executable,'-c','import time;time.sleep(.18)'],
                            stream=output,cadence=.03,cwd=tmp_path)
    assert rc==0
    assert output.getvalue().count('[SST][HEARTBEAT] RUNNING')>=2
    # Exit status is preserved, never replaced with the heartbeat's success.
    bad=module.run_monitored([sys.executable,'-c','import sys;sys.exit(7)'],
                              stream=io.StringIO(),cadence=.03,cwd=tmp_path)
    assert bad==7
