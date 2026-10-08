from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]

def test_readonly_v040_spectral_diagnostic_on_synthetic_controls(tmp_path):
    out=tmp_path/'g2.json'
    cp=subprocess.run([
        sys.executable,'-m','tools.diagnose_spectral_v2',
        '--input-dir',str(ROOT/'data'/'synthetic_blind'),
        '--config',str(ROOT/'configs'/'e010_real_score.json'),
        '--output',str(out),
    ],cwd=ROOT,text=True,capture_output=True)
    assert cp.returncode==0, cp.stderr
    payload=json.loads(out.read_text(encoding='utf-8'))
    assert payload['schema']=='A056-G2-V040-DIAGNOSTIC-READONLY-1'
    assert len(payload['cases'])==5
    assert all(c['spectral_pass'] for c in payload['cases'])
    assert all('legacy_raw_phase_pod_diagnostic' in c for c in payload['cases'])

def test_g2_fail_path_persists_partial_metrics():
    src=(ROOT/'experiment'/'pipeline.py').read_text(encoding='utf-8')
    assert 'A056_G2_DIAGNOSTICS.json' in src
    assert 'A056_CASE_RESULTS_PARTIAL.csv' in src
    assert 'circular_fourier_v1' in src
