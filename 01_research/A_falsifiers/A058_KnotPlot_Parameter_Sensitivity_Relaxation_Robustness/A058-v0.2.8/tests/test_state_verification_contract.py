from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_runner_verifies_numeric_state_start_and_final():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert '_state_ok' in s
    assert 'A058_PARAMETER_STATE_BEGIN' in s
    assert 'A058_FINAL_STATE_BEGIN' in s
    assert 'math.isclose' in s

def test_runner_materializes_complete_sector_defaults():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert "for aid in sm['axes']" in s
    assert "lines.append(f'{p} = {val:.17g}')" in s
    assert 'accepted_unreported' in s


def test_activation_control_switches_off_only_after_numeric_baseline_materialized():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert "if c['role']=='activation_control'" in s
    assert "lines.append(f'{sector_switch} = off')" in s
    assert s.index("lines.append(f'{p} = {val:.17g}')") < s.index("lines.append(f'{sector_switch} = off')")
    assert "expected_switch=not off_control" in s


def test_public_state_never_serializes_raw_parameter_names():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert "'parameters_seen':sorted(params)" not in s
    assert "'accepted_unreported':unreported" not in s
    assert "'reported_axis_ids':reported" in s
    assert "'switch_reported':sw in params" in s
