from pathlib import Path
import argparse,subprocess,os,re,json,hashlib,time
ROOT=Path(__file__).resolve().parent
SHORTCUT=ROOT.parent/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
HARD=("can't open file","cannot open file","failed to open","freeglut error")

def resolve():
    sc=Path(os.environ.get("KNOTPLOT_LNK","").strip() or SHORTCUT)
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    a=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
    if not a:raise RuntimeError("Cannot resolve KnotPlot.lnk")
    return Path(a[0]),Path(a[1]) if len(a)>1 and a[1] else ROOT.parent

def render(src,cwd,stage):
    rel=os.path.relpath(ROOT,cwd).replace("\\","/")
    d=ROOT/"runtime_kpc"/stage;d.mkdir(parents=True,exist_ok=True)
    p=d/src.name;p.write_text(src.read_text().replace("__BUNDLE_ROOT__",rel),encoding="utf-8",newline="\n");return p

def fmt(s):
    s=int(s);h,r=divmod(s,3600);m,s=divmod(r,60);return f"{h:02d}:{m:02d}:{s:02d}"

def declared_outputs(rt,cwd):
    """Return save/coords destinations declared by the rendered KPC."""
    paths=[]
    for line in rt.read_text(encoding="utf-8",errors="replace").splitlines():
        s=line.strip()
        m=re.match(r"^(?:save|coords)\s+(\S+)",s,re.I)
        if m:
            paths.append((cwd/Path(m.group(1))).resolve())
    return paths

def prepare_output_paths(rt,cwd):
    paths=declared_outputs(rt,cwd)
    for p in paths:
        p.parent.mkdir(parents=True,exist_ok=True)
    return paths

def one(exe,cwd,src,stage,i,n,avg):
    rt=render(src,cwd,stage)
    log=ROOT/"logs"/f"{stage}__{src.stem}.log"
    log.parent.mkdir(parents=True,exist_ok=True)

    # v0.2.3.1: KnotPlot does not create missing directories for coords/save.
    expected=prepare_output_paths(rt,cwd)
    for p in expected:
        try:
            if p.is_file():p.unlink()
        except OSError:
            pass

    start=time.monotonic()
    print(f"[{i:02d}/{n:02d}] START {src.stem} {stage}",flush=True)
    with rt.open("rb") as fin,log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)

    elapsed=time.monotonic()-start
    txt=log.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in HARD)]
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]
    status="PASS" if cp.returncode==0 and not rej and not hard and not missing else "FAIL"
    eta=(avg if avg else elapsed)*(n-i)

    print(f"[{i:02d}/{n:02d}] DONE {src.stem} {status} elapsed={fmt(elapsed)} remainingETA={fmt(eta)}",flush=True)
    if status!="PASS":
        for x in (hard+rej)[:5]:
            print("   ERROR:",x,flush=True)
        for x in missing[:5]:
            print("   MISSING:",x,flush=True)

    r={"run_id":src.stem,"stage":stage,"status":status,"elapsed_seconds":elapsed,
       "process_exit":cp.returncode,"rejections":rej[:30],"hard_errors":hard[:30],
       "missing_outputs":missing,"expected_outputs":[str(p) for p in expected]}
    (ROOT/"logs"/f"{stage}__{src.stem}_audit.json").write_text(json.dumps(r,indent=2)+"\n")
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--stage",choices=["probe","continuation"],required=True);a=ap.parse_args()
    exe,cwd=resolve();folder=ROOT/("kpc_probe" if a.stage=="probe" else "kpc_continuation")
    scripts=sorted(folder.glob("*.kpc"));times=[];bad=0
    print("Executable:",exe);print("CWD:",cwd);print("Stage:",a.stage);print("Scripts:",len(scripts))
    for i,p in enumerate(scripts,1):
        avg=sum(times)/len(times) if times else None;r=one(exe,cwd,p,a.stage,i,len(scripts),avg)
        if r["status"]=="PASS":times.append(float(r.get("elapsed_seconds",0.0)))
        else:bad+=1
    print(f"{a.stage.upper()} PASS={len(scripts)-bad} FAIL={bad}")
    return 1 if bad else 0
if __name__=="__main__":raise SystemExit(main())
