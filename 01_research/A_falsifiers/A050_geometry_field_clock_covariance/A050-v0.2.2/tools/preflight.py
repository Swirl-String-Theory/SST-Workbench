import json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
seal=json.loads((ROOT/'config/SEAL_v0.2.2.json').read_text(encoding='utf-8'))
fail=[]
for rel,expected in seal['sha256'].items():
    p=ROOT/rel
    got=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if got!=expected: fail.append((rel,expected,got))
manifest=json.loads((ROOT/'data/HOLDOUT_MANIFEST.json').read_text(encoding='utf-8'))
for e in manifest['entries']:
    p=ROOT/'data'/e['file']
    got=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if got!=e['sha256']: fail.append((str(p.relative_to(ROOT)),e['sha256'],got))
if fail:
    print('PREFLIGHT FAILED')
    for x in fail: print(x)
    raise SystemExit(1)
print(f"PREFLIGHT PASS: {len(seal['sha256'])} sealed files + {len(manifest['entries'])} holdout hashes")
