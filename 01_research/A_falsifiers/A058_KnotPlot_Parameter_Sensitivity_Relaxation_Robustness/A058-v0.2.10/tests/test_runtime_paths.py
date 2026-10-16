from pathlib import Path
import tomllib
ROOT=Path(__file__).resolve().parents[1]
def test_framework_pin_relative():
    assert (ROOT/'.sst_framework_root').read_text().strip().endswith('SST_Falsifier_Framework_v1.0.8')
def test_falsifier_declares_v108():
    with (ROOT/'falsifier.toml').open('rb') as f: cfg=tomllib.load(f)
    assert cfg['project']['framework_version']=='1.0.8'
