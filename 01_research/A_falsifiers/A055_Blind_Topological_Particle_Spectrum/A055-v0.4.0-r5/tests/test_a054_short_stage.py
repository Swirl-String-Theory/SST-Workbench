import hashlib, json
from pathlib import Path
from a055_science.upstream import _stage_a054_runner


def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_stage_a054_runner_is_manifest_identical_and_short(tmp_path: Path):
    # Deliberately make the source path deep; staging must not inherit it.
    src=tmp_path
    for i in range(12):
        src=src/("very_long_archived_campaign_component_%02d"%i)
    runner=src/'blind_runner'
    pkg=runner/'a054_blind'
    pkg.mkdir(parents=True)
    (pkg/'__init__.py').write_text('',encoding='utf-8')
    (pkg/'certify_v020.py').write_text('X=1\n',encoding='utf-8')
    (pkg/'_native.pyd').write_bytes(b'fake-native-payload')
    files={
        'a054_blind\\__init__.py':_sha(pkg/'__init__.py'),
        'a054_blind\\certify_v020.py':_sha(pkg/'certify_v020.py'),
        'a054_blind\\_native.pyd':_sha(pkg/'_native.pyd'),
    }
    (runner/'RUNNER_MANIFEST.json').write_text(json.dumps({'files':files,'require_native':True,'require_openmp':True}),encoding='utf-8')
    staged=_stage_a054_runner(runner)
    out=staged['staged_runner']
    assert out.is_dir()
    assert len(str(out)) < len(str(runner))
    assert (out/'a054_blind'/'_native.pyd').read_bytes()==b'fake-native-payload'
    assert staged['source_verification']['status']=='PASS'
    assert staged['staged_verification']['status']=='PASS'
