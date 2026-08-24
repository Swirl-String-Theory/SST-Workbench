from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/"handoff_contract.json").read_text(encoding="utf-8"))
WORKSPACE=ROOT.parent

def version(p):
    q=p/"VERSION.json"
    if not q.is_file(): return ""
    d=json.loads(q.read_text(encoding="utf-8"))
    return str(d.get("version") or d.get("package_version") or "")

def detect(prefer):
    env=os.environ.get("SST_TBK_TARGET","").strip()
    if env:
        p=Path(env).resolve()
        return p
    v48=(WORKSPACE/C["workspace_layout"]["target_v048"]).resolve()
    v46=(WORKSPACE/C["workspace_layout"]["target_v046"]).resolve()
    cand=[v48,v46] if prefer!="v046" else [v46,v48]
    for p in cand:
        v=version(p)
        if p.is_dir() and (v=="0.4.8" or v.startswith("0.4.6")):
            return p
    raise SystemExit("No supported target found")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prefer",choices=["v048","v046"],required=True)
    ap.add_argument("bridge_args",nargs=argparse.REMAINDER)
    a=ap.parse_args()
    target=detect(a.prefer)
    py=target/".venv/Scripts/python.exe"
    if not py.is_file():
        print("Target venv missing; running target run_install.cmd...")
        cp=subprocess.run(["cmd.exe","/c","run_install.cmd"],cwd=target)
        if cp.returncode: return cp.returncode
    cmd=[str(py),str(ROOT/"bridge.py"),*a.bridge_args]
    print("[DISPATCH]",target)
    return subprocess.run(cmd,cwd=ROOT).returncode
if __name__=="__main__":
    raise SystemExit(main())
