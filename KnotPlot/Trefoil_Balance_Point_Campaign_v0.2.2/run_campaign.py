from pathlib import Path
import argparse,subprocess,os,re,json,hashlib,time
from datetime import datetime
ROOT=Path(__file__).resolve().parent
SHORTCUT=ROOT.parent/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
HARD=("can't open file","cannot open file","failed to open","freeglut error")

def resolve():
    sc=Path(os.environ.get("KNOTPLOT_LNK","").strip() or SHORTCUT)
    if not sc.is_file():raise FileNotFoundError(sc)
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    a=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
    return Path(a[0]),Path(a[1]) if len(a)>1 and a[1] else ROOT.parent

def render(src,cwd,stage):
    rel=os.path.relpath(ROOT,cwd).replace("\\","/")
    dd=ROOT/"runtime_kpc"/stage;dd.mkdir(parents=True,exist_ok=True)
    p=dd/src.name;p.write_text(src.read_text().replace("__BUNDLE_ROOT__",rel),encoding="utf-8",newline="\n")
    return p

def expected(rt,cwd):
    return [(cwd/Path(x)).resolve() for x in re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",rt.read_text())]

def fmt(sec):
    sec=int(sec);h,r=divmod(sec,3600);m,s=divmod(r,60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def one(exe,cwd,src,stage,i,n,avg):
    rt=render(src,cwd,stage)
    m=re.search(r"(?mi)^\s*load\s+(\S+_i60000\.k)",rt.read_text())
    q=(cwd/Path(m.group(1))).resolve() if m else None
    if q is None or not q.is_file():
        return {"run_id":src.stem,"status":"FAIL","elapsed_seconds":0.0,"hard_errors":[f"missing prerequisite {q}"],"rejections":[]}
    exp=expected(rt,cwd)
    for p in exp:
        p.parent.mkdir(parents=True,exist_ok=True)
        try:p.unlink()
        except FileNotFoundError:pass
    log=ROOT/"logs"/f"{stage}__{src.stem}.log";log.parent.mkdir(exist_ok=True)
    start=time.monotonic()
    print(f"[{i:02d}/{n:02d}] START {src.stem} stage={stage}",flush=True)
    with rt.open("rb") as fin,log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    elapsed=time.monotonic()-start
    txt=log.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in HARD)]
    miss=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    st="PASS" if cp.returncode==0 and not rej and not hard and not miss else "FAIL"
    eta=(avg if avg else elapsed)*(n-i)
    print(f"[{i:02d}/{n:02d}] DONE {src.stem} {st} elapsed={fmt(elapsed)} remainingETA={fmt(eta)}",flush=True)
    a={"run_id":src.stem,"stage":stage,"status":st,"process_exit":cp.returncode,
       "elapsed_seconds":elapsed,"rejections":rej[:50],"hard_errors":hard[:50],"missing_outputs":miss,
       "kpc_sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
    (ROOT/"logs"/f"{stage}__{src.stem}_audit.json").write_text(json.dumps(a,indent=2)+"\n")
    return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--stage",choices=["probe","continuation"],required=True)
    a=ap.parse_args();exe,cwd=resolve()
    folder=ROOT/("kpc_probe" if a.stage=="probe" else "kpc_continuation")
    scripts=sorted(folder.glob("*.kpc"))
    bad=0;times=[]
    print("Executable:",exe);print("CWD:",cwd);print("Stage:",a.stage);print("Scripts:",len(scripts))
    for i,p in enumerate(scripts,1):
        avg=sum(times)/len(times) if times else None
        r=one(exe,cwd,p,a.stage,i,len(scripts),avg)
        if r["status"]=="PASS":times.append(float(r.get("elapsed_seconds",0.0)))
        else:
            bad+=1
            for x in r.get("hard_errors",[])[:3]+r.get("rejections",[])[:3]:print("   ",x)
    print(f"{a.stage.upper()} PASS={len(scripts)-bad} FAIL={bad}")
    return 1 if bad else 0
if __name__=="__main__":raise SystemExit(main())
