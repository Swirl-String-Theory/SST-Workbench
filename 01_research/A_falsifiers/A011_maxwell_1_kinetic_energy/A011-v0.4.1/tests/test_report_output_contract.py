from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_scientific_report_has_every_framework_section_without_placeholders():
    from maxwell_sst_falsifier.framework_v110 import qualified_framework
    qualified_framework(ROOT)
    from sst_falsifier.report import validate_report, REQUIRED_SECTION_MARKERS
    report = ROOT / 'report/FALSIFIER_REPORT.tex'
    assert validate_report(report, require_complete=True) == []
    assert len(REQUIRED_SECTION_MARKERS) == 16
    text = report.read_text(encoding='utf-8')
    assert r'\input{AUTO_SCIENCE_CONTRACT.tex}' in text
    assert r'\input{AUTO_RESULTS.tex}' in text
    assert r'\input{AUTO_ADAPTER_RESULTS.tex}' in text
    assert 'References and primary reproducibility records' in text


def test_shared_binding_is_pinned_and_reuses_existing_framework_generator():
    pin = json.loads((ROOT/'REPORT_OUTPUT_CONTRACT.json').read_text())
    binding = ROOT.parents[3] / pin['binding']
    assert hashlib.sha256(binding.read_bytes()).hexdigest() == pin['binding_sha256']
    source = binding.read_text(encoding='utf-8')
    assert 'write_auto_science_tex(root' in source
    assert 'write_auto_results_tex(root' in source
    assert 'publish_instance_report(root' in source
    assert 'deterministic_zip(out' in source
    assert 'reportlab' not in source


def test_standalone_entry_point_uses_version_directory_and_refuses_full_campaign():
    text = (ROOT/'run_all.cmd').read_text(encoding='utf-8')
    assert 'cd /d "%~dp0"' in text
    assert 'run_tests.py' in text
    assert 'run_reported.py' in text
    assert 'Only BASIC or SELFTEST is authorized' in text
    assert 'run_00_install.cmd' not in text


def test_underscore_output_prefix_is_catalog_qualified():
    pin = json.loads((ROOT/'REPORT_OUTPUT_CONTRACT.json').read_text())
    assert pin['output_prefix'] == 'A011_Maxwell_SST_Kinetic_Falsifier'
    assert pin['output_pattern'] == '<output_prefix>_<version>_outputs'
