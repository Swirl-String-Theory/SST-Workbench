from pathlib import Path
from sst_modal_clock.progress import BranchProgress,_fmt_seconds


def test_progress_time_formatter():
    assert _fmt_seconds(0)=='00:00:00'
    assert _fmt_seconds(3661)=='01:01:01'
    assert _fmt_seconds(None)=='--:--:--'


def test_progress_log_is_append_only_and_blind(tmp_path,capsys):
    p=BranchProgress('stage_a',2,tmp_path/'progress.log')
    st=p.start_candidate(1,'anon_candidate','anon_carrier',0,2,100,'anon_candidate.npz')
    p.heartbeat(1,'anon_candidate',st,50,100,12.0,24.0)
    p.done_candidate(1,'anon_candidate',st,100,'t=24/24 ds_cv=0.1 stop=COMPLETED')
    txt=(tmp_path/'progress.log').read_text()
    assert 'anon_candidate.npz' in txt and 'carrier=anon_carrier' in txt
    assert 'ETA~' in txt and 'branch_elapsed=' in txt
    assert 'Gilbert' not in txt and 'Katlas' not in txt and 'Fremlin' not in txt
