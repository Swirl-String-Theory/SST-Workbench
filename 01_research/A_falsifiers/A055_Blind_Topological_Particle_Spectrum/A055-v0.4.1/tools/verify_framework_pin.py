from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
pin=json.loads((ROOT/'FRAMEWORK_PIN.json').read_text(encoding='utf-8'))
loc=(ROOT/(ROOT/'.sst_framework_root').read_text(encoding='utf-8').strip()).resolve()
manifest=loc/'PACKAGE_MANIFEST.json'; freeze=loc/'CANONICAL_FREEZE.json'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
problems=[]
if not manifest.is_file(): problems.append(f'missing {manifest}')
elif h(manifest)!=pin['framework_package_manifest_sha256']: problems.append('framework PACKAGE_MANIFEST.json hash mismatch')
if not freeze.is_file(): problems.append(f'missing {freeze}')
elif h(freeze)!=pin['framework_canonical_freeze_sha256']: problems.append('framework CANONICAL_FREEZE.json hash mismatch')
print(json.dumps({'framework_root':str(loc),'status':'PASS' if not problems else 'FAIL','problems':problems},indent=2))
raise SystemExit(0 if not problems else 1)
