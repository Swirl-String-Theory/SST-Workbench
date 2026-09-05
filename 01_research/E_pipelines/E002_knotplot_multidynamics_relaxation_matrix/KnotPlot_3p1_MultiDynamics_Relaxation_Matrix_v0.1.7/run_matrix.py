from __future__ import annotations
from pathlib import Path
import subprocess,os,re,json,argparse,hashlib
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent
SHORTCUT=WORKSPACE/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter",
        "not a parameter","obsolete","this command is obsolete")
HARD=("can't open file","cannot open file","failed to open")

def resolve_shortcut():
    env=os.environ.get("KNOTPLOT_LNK","").strip()
    sc=Path(env) if env else SHORTCUT
    if not sc.is_file(): raise FileNotFoundError(f"Missing KnotPlot shortcut: {sc}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError("Could not resolve KnotPlot.lnk")
    exe=Path(lines[0]); cwd=Path(lines[1]) if len(lines)>1 and lines[1] else WORKSPACE
    return exe,cwd

def render(src,cwd):
    txt=src.read_text(encoding="utf-8",errors="replace")
    root=os.path.relpath(ROOT,cwd).replace("\\","/")
    txt=txt.replace("__BUNDLE_ROOT__",root)
    dd=ROOT/"runtime_kpc"; dd.mkdir(parents=True,exist_ok=True)
    out=dd/src.name; out.write_text(txt,encoding="utf-8",newline="\n")
    return out

def expected(runtime,cwd):
    toks=re.findall(r"(?mi)^\s*(?:save|coords)\s+(\S+)",runtime.read_text(encoding="utf-8"))
    return [(cwd/Path(x)).resolve() for x in toks]

def run_one(exe,cwd,src):
    runtime=render(src,cwd)
    exp=expected(runtime,cwd)
    for p in exp:
        p.parent.mkdir(parents=True,exist_ok=True)
        try:p.unlink()
        except FileNotFoundError:pass
    log=ROOT/"logs"/f"{src.stem}.log"; log.parent.mkdir(parents=True,exist_ok=True)
    with runtime.open("rb") as fin, log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    text=log.read_text(encoding="utf-8",errors="replace")
    loaded=any("knot loaded" in x.lower() for x in text.splitlines())
    rej=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in HARD)]
    miss=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    status="PASS" if cp.returncode==0 and loaded and not rej and not hard and not miss else "FAIL"
    audit={"candidate":src.stem,"status":status,"exit":cp.returncode,"loaded":loaded,
           "rejections":rej[:50],"hard_errors":hard[:50],"missing":miss,
           "kpc_sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
    (ROOT/"logs"/f"{src.stem}_audit.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    return audit

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--limit",type=int,default=0)
    a=ap.parse_args()
    exe,cwd=resolve_shortcut()
    scripts=sorted((ROOT/"kpc").glob("*.kpc"))
    if a.limit>0:scripts=scripts[:a.limit]
    nbad=0
    print("Executable:",exe);print("CWD:",cwd);print("Scripts:",len(scripts))
    for i,p in enumerate(scripts,1):
        q=run_one(exe,cwd,p)
        print(f"[{i:02d}/{len(scripts):02d}] {p.stem:35s} {q['status']}")
        if q["status"]!="PASS":
            nbad+=1
            for x in q["rejections"][:3]+q["hard_errors"][:3]: print("   ",x)
            for x in q["missing"][:3]: print("    missing:",x)
    print(f"MATRIX RUN: PASS={len(scripts)-nbad} FAIL={nbad}")
    return 1 if nbad else 0
if __name__=="__main__":
    raise SystemExit(main())
