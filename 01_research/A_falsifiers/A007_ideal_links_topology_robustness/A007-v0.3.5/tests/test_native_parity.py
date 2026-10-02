from pathlib import Path
import pytest

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.biot_savart import sign_matrix
from sst_link_suite.native_ext import BackendOptions
from sst_link_suite.native_ext.audit import run_native_parity_audit
from sst_link_suite.native_ext.build_ext_if_needed import build_if_needed

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def _require_build():
    if not build_if_needed(force=False, verbose=False):
        pytest.skip("pybind11 headers/compiler unavailable")


def test_native_python_parity_two_component():
    _require_build()
    link = parse_ideal_links(DATA)["L2a1"]
    curves = [sample_component(component, 96).r for component in link.components]
    report = run_native_parity_audit(
        curves,
        sign_matrix(len(curves)),
        [0.05, 0.1],
        BackendOptions(require_native=True),
        abs_tolerance=2e-11,
        relative_tolerance=2e-11,
    )
    assert report["ok"], report
    assert report["backend_status"]["backend"] == "cpp"


def test_native_python_parity_three_component():
    _require_build()
    link = parse_ideal_links(DATA)["L6a4"]
    curves = [sample_component(component, 64).r for component in link.components]
    report = run_native_parity_audit(
        curves,
        sign_matrix(len(curves)),
        [0.1],
        BackendOptions(require_native=True),
        abs_tolerance=2e-11,
        relative_tolerance=2e-11,
    )
    assert report["ok"], report
