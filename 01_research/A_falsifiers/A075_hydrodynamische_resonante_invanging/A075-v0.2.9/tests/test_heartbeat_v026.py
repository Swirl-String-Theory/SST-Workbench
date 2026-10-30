"""Non-science heartbeat tests: no Euler or gate changes."""
from pathlib import Path
import json, time
from experiment import heartbeat as h

def test_heartbeat_file_progress_completion(tmp_path):
    h.start(tmp_path,'BASIC',interval=.01)
    try:
        h.phase('suite_base',backend='py',knot='0_1',grid=16,physical_end_time=1,phase_index=1,phase_total=6)
        for n in range(1,11):h.advance(n,n/10,1,.1,rejected=1 if n==5 else 0)
        time.sleep(.05)
        state=h.status(tmp_path)
        assert state['state']=='RUNNING'
        assert state['step']==10
        assert state['phase_progress_pct']==100.
        assert state['phase_index']==1 and state['phase_total']==6
        assert state['rejected_steps_total']==1
        assert state['backend']=='py'
    finally:h.finish(0)
    assert h.status(tmp_path)['state']=='COMPLETED'

def test_heartbeat_no_file(tmp_path):
    assert h.status(tmp_path)['state']=='NO_HEARTBEAT'

def test_heartbeat_failure_completion(tmp_path):
    h.start(tmp_path,'BASIC',interval=.1)
    h.finish(3,'framework backend qualification blocked')
    assert h.status(tmp_path)['state']=='BLOCKED_OR_FAILED'
    assert h.status(tmp_path)['exit_code']==3
