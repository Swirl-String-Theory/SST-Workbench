from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
L=json.loads((ROOT/"PREREGISTRATION_LOCK.json").read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
bad=[]
if sha("balance_design.json")!=L["balance_design_sha256"]:bad.append("balance_design.json")
if sha("PREREGISTRATION.md")!=L["preregistration_sha256"]:bad.append("PREREGISTRATION.md")
D=json.loads((ROOT/"balance_design.json").read_text())
s=hashlib.sha256(json.dumps(D["settings"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
if s!=L["settings_sha256"]:bad.append("settings")
if bad:
    print("PREREGISTRATION LOCK FAIL:",bad);raise SystemExit(3)
print("PREREGISTRATION LOCK PASS")
