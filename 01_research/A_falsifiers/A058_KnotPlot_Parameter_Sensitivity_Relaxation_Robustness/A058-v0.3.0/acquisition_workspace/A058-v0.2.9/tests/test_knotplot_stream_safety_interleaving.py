from pathlib import Path
from tools.run_knotplot_campaign import _safe_diagnostic,_safe_response,_segment

EXACT_USER_SEGMENT = "\nKnotPlot> Current position is  *** khat_mag is zero! the knot embedding may be bad or the projection is not well defined!\nsafe.\nKnotPlot> "


def test_exact_uploaded_user_safe_log_segment():
    log = ("A058_STREAM_START_BEGIN" + EXACT_USER_SEGMENT + "A058_STREAM_START_END")
    d=_safe_diagnostic(_segment(log,"A058_STREAM_START_BEGIN","A058_STREAM_START_END"))
    assert d['status']=='SAFE_WITH_WARNING'
    assert d['safe'] is True
    assert d['warning_count']==1
    assert 'khat_mag is zero' in d['warnings'][0]


def test_explicit_unsafe_remains_fail_closed():
    for msg in ("Current position is not safe.", "Current position is  *** diagnostic!\nnot safe.",
                "Current position is unsafe.", "Current position is  *** diagnostic!\nNOT safe."):
        d=_safe_diagnostic(msg)
        assert not d['safe'],msg
        assert d['status']=='UNSAFE'


def test_missing_or_ambiguous_responses_not_safe():
    for msg in ('','KnotPlot> ','*** khat_mag is zero!','safe.',
                'Current position is','nothing loaded\nCurrent position is safe.',
                'Current position is safe.\n*** nothing to save'):
        assert not _safe_response(msg),repr(msg)


def test_normal_response_still_accepted():
    assert _safe_diagnostic('KnotPlot> Current position is safe.\nKnotPlot>')['status']=='SAFE'


def test_all_runtime_safety_sites_use_common_parser():
    root=Path(__file__).resolve().parents[1]
    runner=(root/'tools/run_knotplot_campaign.py').read_text(encoding='utf-8')
    install=(root/'tools/install_test_export.py').read_text(encoding='utf-8')
    assert runner.count('_safe_diagnostic(')>=5
    assert "'current position is safe' in" not in runner
    assert 'from tools.run_knotplot_campaign import resolve_exe,resolve_workdir,_safe_response' in install
    assert "'current position is safe' in" not in install


def test_complete_uploaded_log_marked_safe_with_warning():
    fixture=Path(__file__).resolve().parent/'fixtures/knotplot_build5125w_warning_interleaved.log'
    text=fixture.read_text(encoding='utf-8')
    seg=_segment(text,'A058_STREAM_START_BEGIN','A058_STREAM_START_END')
    assert _safe_diagnostic(seg)['status']=='SAFE_WITH_WARNING'
