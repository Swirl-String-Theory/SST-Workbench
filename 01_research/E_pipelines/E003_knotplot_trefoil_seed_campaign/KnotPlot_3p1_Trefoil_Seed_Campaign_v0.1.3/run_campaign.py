from __future__ import annotations
from pathlib import Path
import argparse,subprocess,os,json,re,shutil
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent

HARD=("can't open file","cannot open file","failed to open")
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete","this command is obsolete")

def resolve_shortcut():
    env=os.environ.get("KNOTPLOT_LNK","").strip()
    candidates=[]
    if env: candidates.append(Path(env))
    candidates += [ROOT.parent/"KnotPlot.lnk", ROOT/"KnotPlot.lnk"]
    shortcut=next((p for p in candidates if p.is_file()),None)
    if shortcut is None:
        raise FileNotFoundError(
            "KnotPlot.lnk not found. Expected sibling path "
            f"{ROOT.parent/'KnotPlot.lnk'} or set KNOTPLOT_LNK."
        )
    ps=(
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"
        +str(shortcut).replace("'","''")
        +"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    )
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError("Could not resolve KnotPlot.lnk: "+p.stderr)
    exe=Path(lines[0])
    cwd=Path(lines[1]) if len(lines)>1 and lines[1] else ROOT.parent
    if not exe.is_file(): raise FileNotFoundError(f"KnotPlot executable missing: {exe}")
    return exe,cwd

def rel_root(cwd):
    s=os.path.relpath(ROOT,cwd).replace("\\","/")
    if " " in s:
        raise RuntimeError("KnotPlot campaign relative path contains spaces; place campaign under a no-space workspace path.")
    return s

def render(src,cwd):
    txt=src.read_text(encoding="utf-8",errors="replace")
    txt=txt.replace("__CAMPAIGN_ROOT__",rel_root(cwd))
    dd=ROOT/"runtime_kpc"; dd.mkdir(exist_ok=True)
    out=dd/src.name
    out.write_text(txt,encoding="utf-8",newline="\n")
    return out

def expected_outputs(runtime):
    t=runtime.read_text(encoding="utf-8")
    return re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",t)

def run_one(exe,cwd,src,stage):
    runtime=render(src,cwd)
    expected=[(cwd/Path(x)).resolve() for x in expected_outputs(runtime)]
    # ZIP archives do not reliably preserve empty directories.  KnotPlot does
    # not create parent directories for `save` / `coords`, so create them here
    # before handing the script to KnotPlot.
    for p in expected:
        p.parent.mkdir(parents=True, exist_ok=True)
        try: p.unlink()
        except FileNotFoundError: pass
    logdir=ROOT/"logs"/stage; logdir.mkdir(parents=True,exist_ok=True)
    log=logdir/f"{src.stem}.log"
    started=datetime.now(timezone.utc)
    with runtime.open("rb") as fin, log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    ended=datetime.now(timezone.utc)
    text=log.read_text(encoding="utf-8",errors="replace")
    hard=[l.strip() for l in text.splitlines() if any(k in l.lower() for k in HARD)]
    reject=[l.strip() for l in text.splitlines() if any(k in l.lower() for k in REJECT)]
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]
    status="PASS"
    # KnotPlot prints startup "nothing loaded / nothing to save / nothing to output"
    # noise before reading stdin. Those phrases are NOT failures when all requested
    # outputs exist. Missing outputs and true command/open errors remain fatal.
    if cp.returncode!=0 or hard or missing or reject:
        status="FAIL"
    audit={
        "stage":stage,"script":src.name,"status":status,"process_exit":cp.returncode,
        "hard_errors":hard[:20],"rejections":reject[:20],"missing_outputs":missing,
        "started_utc":started.isoformat(),"ended_utc":ended.isoformat(),
        "log":str(log)
    }
    (logdir/f"{src.stem}_audit.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    return audit

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",choices=["export-base","full"],required=True)
    ap.add_argument("--limit",type=int,default=0,help="debug only; 0 means all scripts")
    a=ap.parse_args(argv)
    exe,cwd=resolve_shortcut()
    print("[KNOTPLOT] executable:",exe)
    print("[KNOTPLOT] working dir:",cwd)
    if a.stage=="export-base":
        scripts=[ROOT/"00_export_base.kpc"]
    else:
        scripts=sorted((ROOT/"kpc/full").glob("S*.kpc"))
        if a.limit>0: scripts=scripts[:a.limit]
    if not scripts:
        print("ERROR: no scripts found"); return 2
    nfail=0
    for i,p in enumerate(scripts,1):
        a1=run_one(exe,cwd,p,a.stage)
        print(f"[{i:02d}/{len(scripts):02d}] {p.stem:32s} {a1['status']}")
        if a1["status"]!="PASS":
            nfail+=1
            for s in a1["rejections"][:3]+a1["hard_errors"][:3]:
                print("   ",s)
            for s in a1["missing_outputs"][:3]:
                print("    missing:",s)
    print(f"[KNOTPLOT] stage={a.stage} pass={len(scripts)-nfail} fail={nfail}")
    return 1 if nfail else 0

if __name__=="__main__":
    raise SystemExit(main())
