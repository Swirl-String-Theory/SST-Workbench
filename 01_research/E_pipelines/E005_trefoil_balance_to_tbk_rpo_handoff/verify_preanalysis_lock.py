from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"PREANALYSIS_LOCK.json").read_text())
bad=[]
for rel,h in D["files"].items():
    p=ROOT/rel
    a=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<missing>"
    if a!=h: bad.append((rel,h,a))
if bad:
    print("PREANALYSIS LOCK FAIL")
    for x in bad: print(x)
    raise SystemExit(2)
print("PREANALYSIS LOCK PASS")
