from __future__ import annotations
from pathlib import Path
import json, os, subprocess, sys

ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/"handoff_contract.json").read_text(encoding="utf-8"))
WORKSPACE=ROOT.parent

def target():
    env=os.environ.get("SST_TBK_TARGET","").strip()
    if env:
        return Path(env).resolve()
    return (WORKSPACE/C["workspace_layout"]["target_v048"]).resolve()

def main():
    t=target()
    py=t/".venv/Scripts/python.exe"
    if not py.is_file():
        print("DD32 PROBE: target venv missing:",py)
        return 11

    code=r"""
import json
from native_ext.core import load_native,native_info
mod=load_native(skip_build=True)
d=native_info(mod,probe_sycl_worker=True)
print(json.dumps(d,indent=2,default=str))
ok=bool(d.get("sycl_worker_available") and d.get("sycl_dd32_available") and d.get("has_gpu"))
raise SystemExit(0 if ok else 10)
"""
    cp=subprocess.run([str(py),"-c",code],cwd=t,text=True,capture_output=True)
    if cp.stdout:
        print(cp.stdout,end="")
    if cp.stderr:
        print(cp.stderr,end="",file=sys.stderr)

    # 0xC0000135 = STATUS_DLL_NOT_FOUND. This was observed on the target run.
    joined=(cp.stdout or "")+(cp.stderr or "")
    if "3221225781" in joined or "0xc0000135" in joined.lower():
        print("DD32 PROBE: external worker could not start (0xC0000135 / STATUS_DLL_NOT_FOUND).")
        print("DD32 PROBE: CPU/OpenMP spectral fallback is required unless the worker runtime is repaired.")

    if cp.returncode==0:
        print("DD32 PROBE PASS: GPU DD32 worker available.")
        return 0

    print("DD32 PROBE UNAVAILABLE: using CPU/OpenMP spectral fallback.")
    return 10

if __name__=="__main__":
    raise SystemExit(main())
