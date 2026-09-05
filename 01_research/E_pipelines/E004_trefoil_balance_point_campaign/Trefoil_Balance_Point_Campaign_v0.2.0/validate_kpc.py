from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","refine","mode","centre","fitto","collision","energy","echo","safe",
         "dowker","lnknum","length","distance","angle","acn","save","coords","ago","stop"}
bad=[]
files=sorted((ROOT/"kpc").glob("*.kpc"))
for p in files:
    t=p.read_text(encoding="utf-8")
    if "torus " in t:
        bad.append((p.name,0,"v0.2.0 must run only `load 3.1`"))
    if t.count("load 3.1")!=1:
        bad.append((p.name,0,"expected exactly one `load 3.1`"))
    counts={"charge":0,"hooke":0,"power":0}
    for ln,raw in enumerate(t.splitlines(),1):
        s=raw.strip()
        if not s or s.startswith("%"): continue
        m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
        if m:
            name=m.group(1).strip()
            if name not in runtime: bad.append((p.name,ln,f"unknown runtime variable {name}"))
            if name in counts: counts[name]+=1
            continue
        h=s.split()[0]
        if h not in actions: bad.append((p.name,ln,f"unknown action {h}"))
        if h=="refine" and s!="refine nbeads 300":
            bad.append((p.name,ln,"use `refine nbeads 300`"))
        if h in {"charge","hooke","power","timeincr","nbeads","alex"}:
            bad.append((p.name,ln,f"forbidden command-style parameter {h}"))
    for k,n in counts.items():
        if n!=1: bad.append((p.name,0,f"{k} assignment count={n}, expected 1"))
    for it in D["checkpoints"]:
        if f"_i{it:05d}.txt" not in t:
            bad.append((p.name,0,f"missing checkpoint i{it:05d}"))
if bad:
    print("KPC SYNTAX AUDIT FAIL")
    for x in bad[:100]: print(x)
    raise SystemExit(3)
print(f"KPC SYNTAX AUDIT PASS: {len(files)}/{len(files)}")
print("Geometry lock PASS: all scripts use only `load 3.1`")
