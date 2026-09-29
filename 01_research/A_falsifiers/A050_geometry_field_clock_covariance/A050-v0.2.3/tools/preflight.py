from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'config/SEAL_v0.2.3.json').read_text())
fail=[]
for rel,expect in s['files'].items():
    p=ROOT/rel
    if not p.exists(): fail.append((rel,'MISSING')); continue
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=expect: fail.append((rel,got))
if fail:
    for x in fail: print('SEAL FAIL',x)
    raise SystemExit(2)
print(f'PREFLIGHT PASS: {len(s["files"])} sealed primary files verified.')
