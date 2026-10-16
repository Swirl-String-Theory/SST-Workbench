from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_framework_pin_relative():
    assert (ROOT/'.sst_framework_root').read_text().strip().endswith('SST_Falsifier_Framework_v1.0.6')
