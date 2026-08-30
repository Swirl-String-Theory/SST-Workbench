from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","refine","mode","centre","fitto","collision","energy","safe","dowker",
         "lnknum","length","distance","angle","acn","save","coords","ago","stop"}
bad=[]
for folder,ext in [("kpc_standard",False),("kpc_extended",True)]:
    files=sorted((ROOT/folder).glob("*.kpc"))
    if len(files)!=20:bad.append((folder,0,f"expected 20 scripts, got {len(files)}"))
    for p in files:
        t=p.read_text()
        if "torus " in t:bad.append((p.name,0,"torus forbidden"))
        if ext and "_i30000.k" not in t:bad.append((p.name,0,"missing continuation load"))
        if not ext and t.count("load 3.1")!=1:bad.append((p.name,0,"expected load 3.1"))
        cnt={"charge":0,"hooke":0,"power":0}
        for ln,raw in enumerate(t.splitlines(),1):
            s=raw.strip()
            if not s or s.startswith("%"):continue
            m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
            if m:
                name=m.group(1).strip()
                if name not in runtime:bad.append((p.name,ln,f"unknown assignment {name}"))
                if name in cnt:cnt[name]+=1
                continue
            head=s.split()[0]
            if head not in actions:bad.append((p.name,ln,f"unknown action {head}"))
            if head in {"charge","hooke","power","timeincr","nbeads","alex"}:
                bad.append((p.name,ln,f"forbidden command parameter {head}"))
        for k,n in cnt.items():
            if n!=1:bad.append((p.name,0,f"{k} count={n}"))
if bad:
    print("KPC AUDIT FAIL")
    for x in bad[:100]:print(x)
    raise SystemExit(3)
print("STANDARD KPC AUDIT PASS: 20/20")
print("EXTENDED KPC AUDIT PASS: 20/20")
print("GEOMETRY LOCK PASS: K31 only")
