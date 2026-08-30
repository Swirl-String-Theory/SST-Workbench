from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","mode","collision","energy","coords","stop","ago","centre","safe","dowker","lnknum","length","distance","angle","acn","save"}
bad=[]
for folder in ["kpc_probe","kpc_continuation"]:
    fs=list((ROOT/folder).glob("*.kpc"))
    if len(fs)!=20:bad.append((folder,0,f"expected20 got{len(fs)}"))
    for p in fs:
        txt=p.read_text()
        if folder=="kpc_continuation":
            pre=txt.split("ago ",1)[0]
            for x in ["fitto ","refine ","\ncentre\n"]:
                if x in pre:bad.append((p.name,0,"forbidden pre-ago "+x.strip()))
            if "_i100000.k" not in pre:bad.append((p.name,0,"missing 100k source"))
        for n,line in enumerate(txt.splitlines(),1):
            s=line.strip()
            if not s or s.startswith("%"):continue
            m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
            if m:
                if m.group(1).strip() not in runtime:bad.append((p.name,n,"bad var "+m.group(1)))
            elif s.split()[0] not in actions:bad.append((p.name,n,"bad cmd "+s.split()[0]))
if bad:
    print("KPC VALIDATION FAIL")
    for x in bad[:50]:print(x)
    raise SystemExit(3)
print("KPC VALIDATION PASS: 20+20; metric-neutral 100k prefix")
