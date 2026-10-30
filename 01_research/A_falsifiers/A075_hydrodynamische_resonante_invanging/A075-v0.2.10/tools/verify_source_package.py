from pathlib import Path
import sys,json,hashlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SOURCE_FILE_MANIFEST.json').read_text())
for rel,h in manifest['sha256'].items():
 p=(root/rel).resolve()
 if not p.is_relative_to(root.resolve()) or not p.is_file():raise SystemExit('MISSING_OR_UNSAFE '+rel)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=h:raise SystemExit('SHA_MISMATCH '+rel)
print('SOURCE_PACKAGE_VERIFIED',len(manifest['sha256']),'files')
