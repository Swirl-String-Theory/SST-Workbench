from __future__ import annotations
from pathlib import Path
import hashlib, importlib, json, os, sys

ROOT = Path(__file__).resolve().parent
FRAMEWORK = ROOT / "framework" / "SST_Falsifier_Framework_v1.0.6"
EXPECTED_PACKAGE_MANIFEST_SHA256 = "233730abad5ef26f851db0ae75c691fd17daa75e99beb8419d6934ccf85c15be"
EXPECTED_CANONICAL_FREEZE_SHA256 = "03813843a3c00907ed12def0decf3572a57b7f40e5671276bd14b9189ac31759"

class FrameworkBootstrapError(RuntimeError):
    pass

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def verify_bundled_framework() -> dict:
    manifest=FRAMEWORK/'PACKAGE_MANIFEST.json'; freeze=FRAMEWORK/'CANONICAL_FREEZE.json'
    if not (FRAMEWORK/'sst_falsifier'/'__init__.py').is_file():
        raise FrameworkBootstrapError(f"Bundled framework missing: {FRAMEWORK}")
    if _sha256(manifest)!=EXPECTED_PACKAGE_MANIFEST_SHA256:
        raise FrameworkBootstrapError('Bundled framework PACKAGE_MANIFEST.json hash mismatch')
    if _sha256(freeze)!=EXPECTED_CANONICAL_FREEZE_SHA256:
        raise FrameworkBootstrapError('Bundled framework CANONICAL_FREEZE.json hash mismatch')
    payload=json.loads(manifest.read_text(encoding='utf-8'))
    bad=[]
    for row in payload.get('files',[]):
        p=FRAMEWORK/row['path']; actual=_sha256(p) if p.is_file() else None
        size=p.stat().st_size if p.is_file() else None
        if actual!=row['sha256'] or size!=row['size']:
            bad.append({'path':row['path'],'expected_sha256':row['sha256'],'actual_sha256':actual,'expected_size':row['size'],'actual_size':size})
    if bad:
        raise FrameworkBootstrapError(f"Bundled framework file verification failed: {bad[:5]}")
    return {'pass':True,'root':str(FRAMEWORK),'file_count':len(payload.get('files',[])),'package_manifest_sha256':EXPECTED_PACKAGE_MANIFEST_SHA256,'canonical_freeze_sha256':EXPECTED_CANONICAL_FREEZE_SHA256}

def resolve_framework_root() -> Path:
    verify_bundled_framework()
    return FRAMEWORK.resolve()

def load_framework() -> Path:
    framework=resolve_framework_root(); fs=str(framework)
    sys.path[:]=[p for p in sys.path if os.path.normcase(os.path.abspath(p or '.'))!=os.path.normcase(fs)]
    sys.path.insert(0,fs)
    for name in list(sys.modules):
        if name=='sst_falsifier' or name.startswith('sst_falsifier.'):
            del sys.modules[name]
    importlib.invalidate_caches()
    module=importlib.import_module('sst_falsifier')
    actual=Path(module.__file__).resolve().parent.parent
    if actual!=framework:
        raise FrameworkBootstrapError(f"Bundled framework import mismatch: expected {framework}, imported {actual}")
    return framework
