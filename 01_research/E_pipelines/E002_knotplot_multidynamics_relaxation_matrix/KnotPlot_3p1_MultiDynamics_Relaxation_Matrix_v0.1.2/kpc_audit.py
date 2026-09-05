from __future__ import annotations
import re, json, sys
from pathlib import Path

RELAX_COMMANDS=("charge","hooke","power","timeincr")
FATAL_LOG_MARKERS=("unknown command","this command is obsolete","can't open file","nothing to save","nothing to output")

def script_issues(path: Path)->list[str]:
    t=path.read_text(encoding="utf-8",errors="replace")
    issues=[]
    for cmd in RELAX_COMMANDS:
        if re.search(rf"(?mi)^\s*{re.escape(cmd)}\s*=",t):
            issues.append(f"legacy invalid syntax: {cmd} = value")
    if re.search(r"(?mi)^\s*nbeads\s+\d+\s*$",t):
        issues.append("target runtime marks nbeads obsolete; use refine nbeads N")
    if re.search(r"(?mi)^\s*alex\s+-1\s*$",t):
        issues.append("alex -1 requires missing KP-alex.exe on target runtime")
    saves=re.findall(r"(?mi)^\s*save\s+(\S+)",t)
    coords=re.findall(r"(?mi)^\s*coords\s+(\S+)",t)
    if len(saves)!=len(coords): issues.append(f"save/coords count mismatch: {len(saves)} vs {len(coords)}")
    return issues

def log_issues(text: str)->list[str]:
    lo=text.lower(); issues=[]
    for m in FATAL_LOG_MARKERS:
        if m in lo:
            if m=="nothing to save" and ("knot saved" in lo or "data output to file" in lo):
                continue
            issues.append(m)
    if "nothing loaded" in lo and not ("knot loaded" in lo or "knot saved" in lo): issues.append("nothing loaded")
    return sorted(set(issues))

def expected_outputs(script: Path, workdir: Path)->list[Path]:
    t=script.read_text(encoding="utf-8",errors="replace")
    toks=[]
    toks += re.findall(r"(?mi)^\s*save\s+(\S+)",t)
    toks += re.findall(r"(?mi)^\s*coords\s+(\S+)",t)
    return [(workdir/Path(tok)).resolve() for tok in toks]

def main()->int:
    root=Path(__file__).resolve().parent
    bad={}
    for p in sorted(root.glob("[0-9][0-9]_*.kpc")):
        if p.name.startswith(("97_","98_","99_")): continue
        q=script_issues(p)
        if q: bad[p.name]=q
    if bad:
        print(json.dumps(bad,indent=2)); return 2
    print("KPC STATIC AUDIT PASS")
    return 0
if __name__=="__main__": raise SystemExit(main())
