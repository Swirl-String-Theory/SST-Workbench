from pathlib import Path
import pytest
pytest.importorskip('pybind11', reason='pybind11 is installed by run_install.cmd before production selftest')
from a055_science.native_metric import certify


def test_native_signed_metric_parity():
    root=Path(__file__).resolve().parents[1]
    cfg={'seed':5504000,'native_metric_relative_l2_max':1e-10}
    r=certify(root,cfg)
    assert r['status']=='PASS', r
    assert r['parity']['relative_l2'] <= 1e-10
