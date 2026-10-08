import hashlib, json
from pathlib import Path
from a055_science.upstream import _stage_a054_runner


def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_stage_excludes_untracked_abi_suffixed_native_shadow(tmp_path: Path):
    runner=tmp_path/'blind_runner'
    pkg=runner/'a054_blind'
    pkg.mkdir(parents=True)
    (pkg/'__init__.py').write_text('',encoding='utf-8')
    (pkg/'certify_v020.py').write_text('X=1\n',encoding='utf-8')
    canonical=pkg/'_native.pyd'
    canonical.write_bytes(b'canonical-sealed-native')
    stale=pkg/'_native.cp314-win_amd64.pyd'
    stale.write_bytes(b'stale-local-rebuild')
    files={
        'a054_blind\\__init__.py':_sha(pkg/'__init__.py'),
        'a054_blind\\certify_v020.py':_sha(pkg/'certify_v020.py'),
        'a054_blind\\_native.pyd':_sha(canonical),
    }
    (runner/'RUNNER_MANIFEST.json').write_text(json.dumps({'files':files,'require_native':True,'require_openmp':True}),encoding='utf-8')
    stage=_stage_a054_runner(runner)
    out=stage['staged_runner']
    assert (out/'a054_blind'/'_native.pyd').read_bytes()==b'canonical-sealed-native'
    assert not (out/'a054_blind'/'_native.cp314-win_amd64.pyd').exists()
    assert stage['staged_native_artifacts']==['a054_blind/_native.pyd']
    excluded=stage['excluded_untracked_native_artifacts']
    assert len(excluded)==1
    assert excluded[0]['relpath']=='a054_blind/_native.cp314-win_amd64.pyd'
    assert excluded[0]['sha256']==_sha(stale)
