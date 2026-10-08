from pathlib import Path
import hashlib,json
import pytest
from a055_science.upstream import import_a054_runner,prepare_a054_runner

def _h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def test_missing_runner_fails_closed(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="isolated blind runner absent"):
        import_a054_runner(tmp_path)

def test_manifest_allowlist_excludes_unlisted_abi_native(tmp_path: Path):
    runner=tmp_path/'blind_runner'; pkg=runner/'a054_blind'; pkg.mkdir(parents=True)
    files={
      'a054_blind\\__init__.py':b'',
      'a054_blind\\certify_v020.py':b'# sealed\n',
      'a054_blind\\blind_geometry.py':b'# sealed\n',
      'a054_blind\\physics.py':b'# sealed\n',
      'a054_blind\\modes_v020.py':b'# sealed\n',
      'a054_blind\\_native.pyd':b'SEALED-NATIVE',
    }
    manifest={'schema':'TEST','files':{}}
    for rel,data in files.items():
        p=runner/Path(*rel.replace('\\','/').split('/')); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); manifest['files'][rel]=_h(p)
    (pkg/'_native.cp314-win_amd64.pyd').write_bytes(b'UNLISTED-ROGUE')
    (runner/'RUNNER_MANIFEST.json').write_text(json.dumps(manifest),encoding='utf-8')
    stage,prov=prepare_a054_runner(tmp_path)
    assert (stage/'a054_blind'/'_native.pyd').read_bytes()==b'SEALED-NATIVE'
    assert not (stage/'a054_blind'/'_native.cp314-win_amd64.pyd').exists()
    assert prov['excluded_unlisted_executables']

def test_manifest_mismatch_fails_closed(tmp_path: Path):
    runner=tmp_path/'blind_runner'; pkg=runner/'a054_blind'; pkg.mkdir(parents=True)
    (pkg/'certify_v020.py').write_text('# x',encoding='utf-8')
    (runner/'RUNNER_MANIFEST.json').write_text(json.dumps({'files':{'a054_blind\\certify_v020.py':'0'*64}}),encoding='utf-8')
    with pytest.raises(RuntimeError, match='runner manifest mismatch'):
        prepare_a054_runner(tmp_path)
