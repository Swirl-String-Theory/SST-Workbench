"""Fail-closed source SHA-256 verifier; no write operations."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SOURCE_FILE_MANIFEST.json').read_text(encoding='utf-8'))
fail=[]
for rel,expected in manifest['entries'].items():
    f=root/rel
    if not f.is_file():fail.append(f'MISSING: {rel}');continue
    actual=hashlib.sha256(f.read_bytes()).hexdigest()
    if actual!=expected:fail.append(f'INVALID: {rel} sha256={actual}')
if fail:
    for item in fail:print('[FAIL]',item)
    sys.exit(2)
print('[PASS] Verified',len(manifest['entries']),'source files with SHA-256')
