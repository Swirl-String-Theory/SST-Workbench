from pathlib import Path
import json,re,sys

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"parameter_manifest.json").read_text(encoding="utf-8"))
SRC=(ROOT/"parameters_full_source.txt").read_text(encoding="utf-8",errors="replace")

runtime_names=set()
for raw in SRC.splitlines():
    m=re.match(r"^\s*([^=\s][^=]*?)\s*=\s*.*$",raw)
    if m:
        runtime_names.add(m.group(1).strip())

manifest_names=set(D["baseline"])
for fam in D["families"]:
    manifest_names.add(fam["name"])
    manifest_names.update(fam.get("context",{}))

missing=sorted(manifest_names-runtime_names)
if missing:
    print("PARAMETER MANIFEST FAIL: names absent from parameters_full_source.txt")
    for x in missing: print(" ",x)
    raise SystemExit(2)

allowed_actions={"reset","load","refine","mode","centre","fitto","collision",
                 "energy","save","coords","ago","stop"}
problems=[]
files=sorted((ROOT/"kpc"/"probe").glob("*.kpc"))+sorted((ROOT/"kpc"/"extended").glob("*.kpc"))
for p in files:
    for ln,raw in enumerate(p.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        s=raw.strip()
        if not s or s.startswith("%"): continue
        if "=" in s:
            name=s.split("=",1)[0].strip()
            if name not in runtime_names:
                problems.append((p,ln,f"assignment to unknown runtime variable `{name}`",raw))
            continue
        head=s.split()[0]
        if head not in allowed_actions:
            problems.append((p,ln,f"non-assignment command not in action whitelist `{head}`",raw))
        if head=="refine" and s!="refine nbeads 300":
            problems.append((p,ln,"bead syntax must be exactly `refine nbeads 300`",raw))

if problems:
    print(f"KPC STATIC AUDIT FAIL: {len(problems)} problem(s)")
    for p,ln,msg,raw in problems[:80]:
        print(f" {p.relative_to(ROOT)}:{ln}: {msg}")
        print("   ",raw)
    raise SystemExit(3)

print(f"PARAMETER MANIFEST PASS: {len(manifest_names)} used variables exist in runtime dump")
print(f"KPC STATIC AUDIT PASS: {len(files)} generated scripts")
print("Important: `charge`, `hooke`, `power`, `tinc`, etc. are emitted as `name = value`, not action commands.")
