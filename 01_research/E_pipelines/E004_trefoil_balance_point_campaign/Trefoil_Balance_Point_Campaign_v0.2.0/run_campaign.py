from pathlib import Path
import subprocess,os,re,json,argparse,hashlib
ROOT=Path(__file__).resolve().parent
SHORTCUT=ROOT.parent/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
HARD=("can't open file","cannot open file","failed to open","freeglut error")

def resolve():
    sc=Path(os.environ.get("KNOTPLOT_LNK","").strip() or SHORTCUT)
    if not sc.is_file(): raise FileNotFoundError(f"Missing {sc}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    ls=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
    if not ls: raise RuntimeError("Could not resolve KnotPlot shortcut")
    return Path(ls[0]),Path(ls[1]) if len(ls)>1 and ls[1] else ROOT.parent

def render(src,cwd):
    text=src.read_text(encoding="utf-8")
    rel=os.path.relpath(ROOT,cwd).replace("\\","/")
    if " " in rel: raise RuntimeError("Relative campaign path contains spaces")
    dd=ROOT/"runtime_kpc";dd.mkdir(exist_ok=True)
    p=dd/src.name;p.write_text(text.replace("__BUNDLE_ROOT__",rel),encoding="utf-8",newline="\n")
    return p

def expected(rt,cwd):
    x=re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",rt.read_text())
    return [(cwd/Path(q)).resolve() for q in x]

def one(exe,cwd,src):
    rt=render(src,cwd); exp=expected(rt,cwd)
    for p in exp:
        p.parent.mkdir(parents=True,exist_ok=True)
        try:p.unlink()
        except FileNotFoundError:pass
    lp=ROOT/"logs"/f"{src.stem}.log";lp.parent.mkdir(exist_ok=True)
    with rt.open("rb") as fin,lp.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    text=lp.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in HARD)]
    miss=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    status="PASS" if cp.returncode==0 and not rej and not hard and not miss else "FAIL"
    audit={"run_id":src.stem,"status":status,"process_exit":cp.returncode,
           "rejections":rej[:50],"hard_errors":hard[:50],"missing_outputs":miss,
           "kpc_sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
    (ROOT/"logs"/f"{src.stem}_audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    return audit

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args()
    exe,cwd=resolve(); scripts=sorted((ROOT/"kpc").glob("*.kpc"))
    if a.smoke: scripts=[scripts[0],scripts[-1]]
    print("Executable:",exe);print("CWD:",cwd);print("Scripts:",len(scripts))
    bad=0
    for i,p in enumerate(scripts,1):
        r=one(exe,cwd,p);print(f"[{i:02d}/{len(scripts):02d}] {p.stem:12s} {r['status']}")
        if r["status"]!="PASS":
            bad+=1
            for x in r["rejections"][:3]+r["hard_errors"][:3]:print("   ",x)
            for x in r["missing_outputs"][:3]:print("    missing:",x)
    print(f"ZERO-BRACKET RUN: PASS={len(scripts)-bad} FAIL={bad}")
    return 1 if bad else 0
if __name__=="__main__":raise SystemExit(main())
