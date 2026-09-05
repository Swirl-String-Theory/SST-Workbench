from pathlib import Path
import re,sys,json
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","mode","collision","energy","coords","stop","ago","centre","safe","dowker","lnknum","length","distance","angle","acn","save"}
bad=[]
for folder in ["kpc_probe","kpc_continuation"]:
    fs=sorted((ROOT/folder).glob("*.kpc"))
    if len(fs)!=20:bad.append((folder,0,f"expected 20 scripts, got {len(fs)}"))
    for p in fs:
        txt=p.read_text()
        if folder=="kpc_continuation":
            prefix=txt.split("ago ",1)[0]
            for forbidden in ["fitto ","refine ","\ncentre\n"]:
                if forbidden in prefix:bad.append((p.name,0,f"forbidden pre-resume geometry transform: {forbidden.strip()}"))
            if "_i60000.k" not in prefix:bad.append((p.name,0,"missing i60000 source"))
        for ln,raw in enumerate(txt.splitlines(),1):
            s=raw.strip()
            if not s or s.startswith("%"):continue
            m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
            if m:
                if m.group(1).strip() not in runtime:bad.append((p.name,ln,f"unknown runtime var {m.group(1).strip()}"))
                continue
            head=s.split()[0]
            if head not in actions:bad.append((p.name,ln,f"unknown command {head}"))
if bad:
    print("KPC VALIDATION FAIL")
    for x in bad[:100]:print(x)
    raise SystemExit(3)
print("KPC VALIDATION PASS: 20 probes + 20 continuations; metric-neutral prefix confirmed")
