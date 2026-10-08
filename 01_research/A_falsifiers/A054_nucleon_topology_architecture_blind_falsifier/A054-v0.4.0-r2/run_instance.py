from pathlib import Path
import json, os, sys, re
ROOT=Path(__file__).resolve().parent
PIN=json.loads((ROOT/'FRAMEWORK_PIN.json').read_text())
def framework_root():
    env=os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT')
    p=Path(env) if env else (ROOT/(ROOT/'.sst_framework_root').read_text().strip())
    p=p.resolve()
    if p.name!='SST_Falsifier_Framework_v1.0.4': raise RuntimeError(f'v1.0.4 CANONICAL_FROZEN required, got {p}')
    manifest=p/'PACKAGE_MANIFEST.json'
    if not manifest.is_file(): raise RuntimeError(f'framework PACKAGE_MANIFEST.json missing: {manifest}')
    import hashlib
    h=hashlib.sha256(manifest.read_bytes()).hexdigest()
    if h!=PIN['framework_package_manifest_sha256']: raise RuntimeError(f'framework package-manifest SHA mismatch: {h}')
    return p
FW=framework_root(); sys.path.insert(0,str(FW))
from sst_falsifier.runner import run_mode
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'BASIC'; raise SystemExit(run_mode(ROOT,mode))
