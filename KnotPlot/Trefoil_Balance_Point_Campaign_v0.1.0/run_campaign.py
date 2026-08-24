from pathlib import Path
import subprocess,os,re,json,argparse,hashlib
ROOT=Path(__file__).resolve().parent
SHORTCUT=ROOT.parent/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter",
        "not a parameter","obsolete","this command is obsolete")
HARD=("can't open file","cannot open file","failed to open")

def resolve():
    sc=Path(os.environ.get("KNOTPLOT_LNK","").strip() or SHORTCUT)
    if not sc.is_file(): raise FileNotFoundError(f"Missing {sc}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    ls=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    if not ls: raise RuntimeError("Could not resolve KnotPlot.lnk")
    return Path(ls[0]),Path(ls[1]) if len(ls)>1 and ls[1] else ROOT.parent

def render(src,cwd):
    txt=src.read_text()
    rel=os.path.relpath(ROOT,cwd).replace("\\","/")
    txt=txt.replace("__BUNDLE_ROOT__",rel)
    dd=ROOT/"runtime_kpc";dd.mkdir(exist_ok=True)
    p=dd/src.name;p.write_text(txt,encoding="utf-8",newline="\n")
    return p

def outputs(runtime,cwd):
    toks=re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",runtime.read_text())
    return [(cwd/Path(x)).resolve() for x in toks]

def one(exe,cwd,src):
    rt=render(src,cwd); exp=outputs(rt,cwd)
    for p in exp:
        p.parent.mkdir(parents=True,exist_ok=True)
        try:p.unlink()
        except FileNotFoundError:pass
    log=ROOT/"logs"/f"{src.stem}.log";log.parent.mkdir(exist_ok=True)
    with rt.open("rb") as fin,log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    text=log.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in HARD)]
    miss=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    status="PASS" if cp.returncode==0 and not rej and not hard and not miss else "FAIL"
    a={"run_id":src.stem,"status":status,"exit":cp.returncode,
       "rejections":rej[:50],"hard_errors":hard[:50],"missing":miss,
       "kpc_sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
    (ROOT/"logs"/f"{src.stem}_audit.json").write_text(json.dumps(a,indent=2)+"\n")
    return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--smoke-two-variants",action="store_true")
    a=ap.parse_args()
    exe,cwd=resolve()
    scripts=sorted((ROOT/"kpc").glob("*.kpc"))
    if a.smoke_two_variants:
        scripts=[p for p in scripts if p.stem in {"K31__B00","T23__B00"}]
    print("Executable:",exe);print("CWD:",cwd);print("Scripts:",len(scripts))
    bad=0
    for i,p in enumerate(scripts,1):
        q=one(exe,cwd,p)
        print(f"[{i:02d}/{len(scripts):02d}] {p.stem:16s} {q['status']}")
        if q["status"]!="PASS":
            bad+=1
            for x in q["rejections"][:3]+q["hard_errors"][:3]:print("   ",x)
            for x in q["missing"][:3]:print("    missing:",x)
    print(f"BALANCE CAMPAIGN RUN: PASS={len(scripts)-bad} FAIL={bad}")
    return 1 if bad else 0
if __name__=="__main__": raise SystemExit(main())
