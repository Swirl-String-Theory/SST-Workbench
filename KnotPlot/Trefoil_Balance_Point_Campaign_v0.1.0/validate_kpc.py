from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","torus","refine","mode","centre","fitto","collision","energy",
         "echo","safe","dowker","lnknum","length","distance","angle","acn",
         "save","coords","ago","stop"}
problems=[]
files=sorted((ROOT/"kpc").glob("*.kpc"))
for p in files:
    lines=p.read_text(encoding="utf-8",errors="replace").splitlines()
    assign_counts={"charge":0,"hooke":0,"power":0}
    for ln,raw in enumerate(lines,1):
        s=raw.strip()
        if not s or s.startswith("%"): continue
        m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
        if m:
            name=m.group(1).strip()
            if name not in runtime:
                problems.append((p,ln,f"unknown assignment `{name}`",raw))
            if name in assign_counts:
                assign_counts[name]+=1
            continue
        head=s.split()[0]
        if head not in actions:
            problems.append((p,ln,f"unregistered action `{head}`",raw))
        if head=="refine" and s!="refine nbeads 300":
            problems.append((p,ln,"must use `refine nbeads 300`",raw))
        if head=="torus" and s!="torus 2 3 300":
            problems.append((p,ln,"torus variant must be `torus 2 3 300`",raw))
        if head in {"charge","hooke","power","timeincr","nbeads","alex"}:
            problems.append((p,ln,f"`{head}` must not be emitted as an action command",raw))
    for name,n in assign_counts.items():
        if n!=1:
            problems.append((p,0,f"`{name}` assignment count={n}, expected 1",""))
if problems:
    print(f"KPC SYNTAX AUDIT FAIL: {len(problems)}")
    for p,ln,msg,raw in problems[:100]:
        print(f"{p.name}:{ln}: {msg}")
        if raw: print("  ",raw)
    raise SystemExit(3)
print(f"KPC SYNTAX AUDIT PASS: {len(files)}/{len(files)}")
print("Variants verified: `load 3.1` and `torus 2 3 300`")
print("Only q/h/p vary; all other assignments are frozen.")
