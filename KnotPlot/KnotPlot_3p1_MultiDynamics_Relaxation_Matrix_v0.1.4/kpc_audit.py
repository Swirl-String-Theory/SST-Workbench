from __future__ import annotations
import re, json
from pathlib import Path

RELAX_COMMANDS=("charge","hooke","power","timeincr")
FATAL_LOG_MARKERS=("unknown command","this command is obsolete","can't open file","nothing to save","nothing to output")

def script_issues(path: Path)->list[str]:
    t=path.read_text(encoding="utf-8",errors="replace")
    issues=[]
    for cmd in RELAX_COMMANDS:
        if re.search(rf"(?mi)^\s*{re.escape(cmd)}\s*=",t):
            issues.append(f"invalid command syntax: {cmd} = value; use `{cmd} value`")
    if re.search(r"(?mi)^\s*alex\s+-1\s*$",t):
        issues.append("alex -1 requires external KP-alex helper and is not allowed in discovery scripts")
    saves=re.findall(r"(?mi)^\s*save\s+(\S+)",t)
    coords=re.findall(r"(?mi)^\s*coords\s+(\S+)",t)
    if len(saves)!=len(coords):
        issues.append(f"save/coords count mismatch: {len(saves)} vs {len(coords)}")
    for tok in saves+coords:
        if "KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1." in tok:
            issues.append(f"hard-coded versioned output root remains: {tok}")
            break
    return issues

def log_issue_details(text: str)->list[dict]:
    out=[]
    for i,line in enumerate(text.splitlines(),1):
        lo=line.lower()
        for marker in FATAL_LOG_MARKERS:
            if marker in lo:
                out.append({"line":i,"marker":marker,"text":line.strip()})
                break
        if "nothing loaded" in lo:
            out.append({"line":i,"marker":"nothing loaded","text":line.strip()})
    # stable de-duplication
    seen=set(); dedup=[]
    for x in out:
        k=(x["line"],x["marker"],x["text"])
        if k not in seen:
            seen.add(k); dedup.append(x)
    return dedup

def log_issues(text: str)->list[str]:
    return sorted({x["marker"] for x in log_issue_details(text)})

def expected_outputs(script: Path, workdir: Path)->list[Path]:
    t=script.read_text(encoding="utf-8",errors="replace")
    toks=re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",t)
    return [(workdir/Path(tok)).resolve() for tok in toks]

def main()->int:
    root=Path(__file__).resolve().parent
    bad={}
    for p in sorted(root.glob("[0-9][0-9]_*.kpc")):
        if p.name.startswith(("97_","98_","99_")):
            continue
        q=script_issues(p)
        if q:
            bad[p.name]=q
    if bad:
        print(json.dumps(bad,indent=2))
        return 2
    print("KPC STATIC AUDIT PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
