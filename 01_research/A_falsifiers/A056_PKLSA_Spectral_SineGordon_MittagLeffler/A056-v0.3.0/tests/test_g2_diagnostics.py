from pathlib import Path
import json, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]


def test_readonly_g2_diagnostic_on_synthetic_controls(tmp_path):
    out=tmp_path/'g2.json'
    cp=subprocess.run([
        sys.executable,'-m','tools.diagnose_g2',
        '--input-dir',str(ROOT/'data'/'synthetic_blind'),
        '--config',str(ROOT/'configs'/'e010_real_score.json'),
        '--json-out',str(out),
    ],cwd=ROOT,text=True,capture_output=True)
    assert cp.returncode==0, cp.stderr
    payload=json.loads(out.read_text(encoding='utf-8'))
    assert payload['schema']=='A056-G2-DIAGNOSTIC-READONLY-1'
    assert len(payload['cases'])==5
    assert all(c['spectral_pass'] for c in payload['cases'])


def test_g2_fail_path_persists_partial_metrics():
    src=(ROOT/'experiment'/'pipeline.py').read_text(encoding='utf-8')
    assert "A056_G2_DIAGNOSTICS.json" in src
    assert "A056_CASE_RESULTS_PARTIAL.csv" in src
    assert "decision_unchanged_by_diagnostic_hotfix" in src
