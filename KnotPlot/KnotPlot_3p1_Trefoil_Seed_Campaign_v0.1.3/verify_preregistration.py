from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent
lock=json.loads((ROOT/"PREREGISTRATION_LOCK.json").read_text())
bad=[]
for rel,expected in lock["files"].items():
    p=ROOT/rel
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<missing>"
    if actual!=expected: bad.append((rel,expected,actual))
if bad:
    print("PREREGISTRATION LOCK FAIL")
    for x in bad: print(" ",x[0],"expected",x[1],"actual",x[2])
    raise SystemExit(2)
print("PREREGISTRATION LOCK PASS")
