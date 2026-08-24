from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
SRC=(ROOT/"reference/parameters_full_source.txt").read_text(encoding="utf-8",errors="replace")
runtime=set()
for raw in SRC.splitlines():
    m=re.match(r"^\s*([^=\s][^=]*?)\s*=\s*.*$",raw)
    if m: runtime.add(m.group(1).strip())

required={"close","max-dr","mechforce","elecforce","bendforce","charge","hooke",
          "power","tinc","bencon","stusplit","dstep","bradius","cradius"}
missing=sorted(required-runtime)
if missing:
    print("RUNTIME PARAMETER SOURCE FAIL:",missing); raise SystemExit(2)

actions={"reset","load","refine","mode","centre","fitto","collision","energy","echo",
         "safe","dowker","lnknum","length","distance","angle","acn","save","coords",
         "ago","stop"}
forbidden_action_names={"charge","hooke","power","timeincr","tinc","nbeads","alex"}
problems=[]
files=sorted((ROOT/"kpc").glob("*.kpc"))
for p in files:
    for ln,raw in enumerate(p.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        s=raw.strip()
        if not s or s.startswith("%"): continue
        if "=" in s:
            name=s.split("=",1)[0].strip()
            if name not in runtime:
                problems.append((p,ln,f"unknown runtime assignment `{name}`",raw))
            continue
        head=s.split()[0]
        if head in forbidden_action_names:
            problems.append((p,ln,f"`{head}` illegally emitted as action command",raw))
        elif head not in actions:
            problems.append((p,ln,f"unregistered action `{head}`",raw))
        if head=="refine" and s!="refine nbeads 300":
            problems.append((p,ln,"bad refine nbeads syntax",raw))
if problems:
    print(f"KPC AUDIT FAIL: {len(problems)}")
    for p,ln,msg,raw in problems[:100]:
        print(f"{p.name}:{ln}: {msg}\n  {raw}")
    raise SystemExit(3)
print(f"RUNTIME PARAMETER SOURCE PASS: {len(required)} core parameters confirmed")
print(f"KPC SYNTAX AUDIT PASS: {len(files)} candidate scripts")
print("No `charge X`, `hooke X`, `power X`, `timeincr X`, `nbeads X`, or `alex` action syntax.")
