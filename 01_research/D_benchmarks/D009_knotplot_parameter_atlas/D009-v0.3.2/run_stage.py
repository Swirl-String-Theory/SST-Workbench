from __future__ import annotations
import argparse,subprocess,sys,json,re,os,shutil,hashlib
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent
SHORTCUT=WORKSPACE/"KnotPlot.lnk"
D=json.loads((ROOT/"parameter_manifest.json").read_text())
HARD=("nothing to save","nothing to output","can't open file")
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
MAX_NONFATAL_RUN_FAILED_FRACTION=0.10


def ensure_runtime_dirs(stage):
    """Create directories that ZIP extraction may omit when they are empty."""
    required = [
        ROOT/"out"/stage,
        ROOT/"logs"/stage,
        ROOT/"runtime_kpc"/stage,
        ROOT/"analysis",
        ROOT/"archive",
    ]
    for p in required:
        p.mkdir(parents=True, exist_ok=True)
    return required

def resolve_shortcut():
    if not SHORTCUT.is_file():
        raise FileNotFoundError(f"Missing {SHORTCUT}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(SHORTCUT).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError("Could not resolve KnotPlot.lnk")
    exe=Path(lines[0]); cwd=Path(lines[1]) if len(lines)>1 and lines[1] else WORKSPACE
    return exe,cwd

def rel_bundle(cwd):
    return os.path.relpath(ROOT,cwd).replace("\\","/")

def classify(text,family):
    lines=text.splitlines(); loaded=None
    for i,l in enumerate(lines,1):
        if "knot loaded" in l.lower():
            loaded=i; break
    rej=[]; hard=[]
    for i,l in enumerate(lines,1):
        lo=l.lower()
        if family.lower() in lo and any(x in lo for x in REJECT):
            rej.append({"line":i,"text":l.strip()})
        if any(x in lo for x in HARD):
            if loaded is None or i>=loaded:
                hard.append({"line":i,"text":l.strip()})
    return rej,hard,loaded

def render(src,cwd,stage):
    txt=src.read_text(encoding="utf-8",errors="replace")
    txt=txt.replace("__BUNDLE_ROOT__",rel_bundle(cwd))
    dd=ROOT/"runtime_kpc"/stage; dd.mkdir(parents=True,exist_ok=True)
    out=dd/src.name; out.write_text(txt,encoding="utf-8",newline="\n")
    return out

def expected_files(runtime,cwd):
    t=runtime.read_text(encoding="utf-8")
    toks=re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",t)
    return [(cwd/Path(x)).resolve() for x in toks]

def run_script(exe,cwd,src,stage):
    runtime=render(src,cwd,stage)
    family=src.stem.split("__",1)[0]
    expected=expected_files(runtime,cwd)
    # KnotPlot does not create parent directories for save/coords targets.
    for p in expected:
        p.parent.mkdir(parents=True,exist_ok=True)
        try: p.unlink()
        except FileNotFoundError: pass
    log=ROOT/"logs"/stage/f"{src.stem}.log"; log.parent.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc)
    with runtime.open("rb") as fin, log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    ended=datetime.now(timezone.utc)
    text=log.read_text(encoding="utf-8",errors="replace")
    rej,hard,loaded=classify(text,family)
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]
    status="PASS"
    if rej: status="REJECTED"
    elif cp.returncode!=0 or hard or missing or loaded is None: status="RUN_FAILED"
    audit={
        "candidate":src.stem,"family":family,"stage":stage,"status":status,
        "process_exit":cp.returncode,"loaded_line":loaded,
        "rejections":rej,"hard_errors":hard,"missing_outputs":missing,
        "started_utc":started.isoformat(),"ended_utc":ended.isoformat(),
        "log":str(log)
    }
    ap=ROOT/"logs"/stage/f"{src.stem}_audit.json"
    ap.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    return audit

def families_for_extended():
    p=ROOT/"analysis"/"PROBE.json"
    if not p.is_file():
        return None
    d=json.loads(p.read_text())
    # Run all accepted families at 1000, including early nulls, to catch delayed effects.
    return set(d.get("accepted_families",[]))

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",choices=["probe","extended"],required=True)
    a=ap.parse_args(argv)
    created=ensure_runtime_dirs(a.stage)
    print("Runtime directories:")
    for p in created:
        print("  ",p)
    exe,cwd=resolve_shortcut()
    selected=None if a.stage=="probe" else families_for_extended()
    if a.stage=="extended" and selected is None:
        print("ERROR: analysis/PROBE.json missing"); return 2
    if a.stage=="extended" and not selected:
        print("No accepted parameter families; extended stage skipped.")
        (ROOT/"analysis"/"EXTENDED_SKIPPED.flag").write_text("No accepted parameter families.\n")
        return 0
    scripts=sorted((ROOT/"kpc"/a.stage).glob("*.kpc"))
    scripts=[p for p in scripts if p.name!="index.json"]
    if selected is not None:
        scripts=[p for p in scripts if p.stem.split("__",1)[0] in selected]
    print("="*72)
    print(f"KnotPlot Parameter Atlas {a.stage.upper()} stage")
    print("Executable:",exe); print("CWD       :",cwd); print("Scripts   :",len(scripts))
    print("="*72)
    nfail=nrej=0
    for i,p in enumerate(scripts,1):
        audit=run_script(exe,cwd,p,a.stage)
        print(f"[{i:03d}/{len(scripts):03d}] {p.stem:40s} {audit['status']}")
        if audit["status"]=="REJECTED":
            nrej+=1
            for x in audit["rejections"][:2]: print("   ",x["text"])
        elif audit["status"]!="PASS":
            nfail+=1
            for x in audit["hard_errors"][:2]: print("   ",x["text"])
    npass=len(scripts)-nfail-nrej
    frac=(nfail/len(scripts)) if scripts else 0.0
    summary={
        "format":"KNOTPLOT-ATLAS-STAGE-SUMMARY-0.3.2",
        "stage":a.stage,
        "n_scripts":len(scripts),
        "pass":npass,
        "rejected":nrej,
        "run_failed":nfail,
        "run_failed_fraction":frac,
        "max_nonfatal_run_failed_fraction":MAX_NONFATAL_RUN_FAILED_FRACTION,
        "continuation_allowed": frac <= MAX_NONFATAL_RUN_FAILED_FRACTION,
    }
    (ROOT/"analysis"/f"{a.stage.upper()}_STAGE_SUMMARY.json").write_text(
        json.dumps(summary,indent=2)+"\n",encoding="utf-8"
    )
    print(f"Stage complete: PASS={npass} REJECTED={nrej} RUN_FAILED={nfail}")
    if nfail:
        print(f"RUN_FAILED fraction: {frac:.3%}")
        if frac <= MAX_NONFATAL_RUN_FAILED_FRACTION:
            print("Atlas continuation: ALLOWED; failed candidates remain explicit measured outcomes.")
        else:
            print("Atlas continuation: ABORT; failure fraction exceeds runtime-safety threshold.")
            return 4
    # REJECTED and isolated RUN_FAILED candidates are discovery measurements.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
