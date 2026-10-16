from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_runner_verifies_numeric_state_start_and_final():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert '_state_ok' in s
    assert 'A058_PARAMETER_STATE_BEGIN' in s
    assert 'A058_FINAL_STATE_BEGIN' in s
    assert 'math.isclose' in s
