from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
L=json.loads((ROOT/"PREREGISTRATION_LOCK.json").read_text(encoding="utf-8"))
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
bad=[]
if sha("balance_design.json")!=L["balance_design_sha256"]:bad.append("design")
if sha("PREREGISTRATION.md")!=L["preregistration_sha256"]:bad.append("prereg")
p=hashlib.sha256(json.dumps(D["panel"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
if p!=L["panel_sha256"]:bad.append("panel")
if bad:
    print("PREREGISTRATION LOCK FAIL",bad);raise SystemExit(3)
print("PREREGISTRATION LOCK PASS")
