from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.backend_selftest import run_backend_selftest
from sst_falsifier_framework.provenance import compiler_probe


def test_backend_selftest_can_audit_without_optional_native():
    r=run_backend_selftest(ROOT,require_native=False)
    assert r['status']=='PASS'
    assert {x['case'] for x in r['native_cases']}=={'circle','trefoil'}
    assert all(x['status'] in {'PASS','SKIP'} for x in r['native_cases'])


def test_compiler_probe_schema_is_explicit():
    r=compiler_probe('host')
    assert r['kind']=='host'
    assert 'available' in r and 'fingerprint' in r
