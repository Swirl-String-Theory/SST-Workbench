"""Fail-closed local-runtime bootstrap. No Workbench, pip, or env fallback."""
from pathlib import Path
import hashlib, importlib, json, sys
ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/'_sst_runtime'
class FrameworkBootstrapError(RuntimeError): pass

def resolve_framework_root() -> Path:
    marker=RUNTIME/'sst_falsifier'/'__init__.py'
    mf=RUNTIME/'RUNTIME_SNAPSHOT_MANIFEST.json'
    if not marker.is_file() or not mf.is_file():
        raise FrameworkBootstrapError('Missing self-contained runtime or snapshot manifest; no fallback permitted')
    info=json.loads(mf.read_text(encoding='utf-8'))
    if info.get('version')!='1.1.1':raise FrameworkBootstrapError('Unexpected runtime version')
    for item in info['files']:
        rel=Path(item['path'])
        if rel.is_absolute() or '..' in rel.parts:raise FrameworkBootstrapError('Invalid runtime inventory path')
        src=RUNTIME/rel
        if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=item['sha256']:
            raise FrameworkBootstrapError('Framework runtime integrity failure: '+str(rel))
    return RUNTIME.resolve()

def load_framework() -> Path:
    root=resolve_framework_root()
    sys.path[:]=[v for v in sys.path if Path(v or '.').resolve()!=root]
    sys.path.insert(0,str(root))
    for name in list(sys.modules):
        if name=='sst_falsifier' or name.startswith('sst_falsifier.'):del sys.modules[name]
    importlib.invalidate_caches()
    mod=importlib.import_module('sst_falsifier')
    if Path(mod.__file__).resolve().parent.parent!=root:raise FrameworkBootstrapError('Runtime import mismatch')
    return root
