import json
from pathlib import Path
from a055_science.upstream import _runner_manifest_native_expectation

def test_runner_manifest_native_expectation_normalizes_windows_paths(tmp_path):
    r=tmp_path/'blind_runner'; r.mkdir()
    (r/'RUNNER_MANIFEST.json').write_text(json.dumps({
      'require_native':True,'require_openmp':True,
      'files':{'a054_blind\\\\_native.pyd':'abc123'},
      'native_import_verified':True,'native_openmp_verified':True}),encoding='utf-8')
    got=_runner_manifest_native_expectation(r)
    assert got['require_native'] is True
    assert got['require_openmp'] is True
    assert got['native_expected_sha256']=='abc123'
