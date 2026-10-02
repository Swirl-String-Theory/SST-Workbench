from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"PREREGISTRATION_LOCK.json").read_text())
bad=[]
for rel,h in D["files"].items():
    p=ROOT/rel
    a=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<missing>"
    if a!=h:bad.append((rel,h,a))
if bad:
    print("PREREGISTRATION LOCK FAIL")
    for x in bad:print(x)
    raise SystemExit(2)
print("PREREGISTRATION LOCK PASS")
