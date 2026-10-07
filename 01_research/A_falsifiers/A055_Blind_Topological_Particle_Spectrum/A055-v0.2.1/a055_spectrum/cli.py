from __future__ import annotations
from pathlib import Path
import argparse,json
from .atlas import load_atlas,validate_pd,component_cycles
from .blind import run_blind,seal_blind,verify_seal
from .reveal import run_reveal
from .packaging import package_outputs
from .util import load_json
from .workbench import detect_workbench_root, find_c006_version
from .c006_bridge import native_preflight
ROOT=Path(__file__).resolve().parents[1]

def selftest():
    a=load_atlas(ROOT); assert len(a)==82
    for x in a: validate_pd(x)
    by={x["id"]:x for x in a}
    assert len(component_cycles(by["3_1"]))==1
    assert len(component_cycles(by["L2a1"]))==2
    assert len(component_cycles(by["L6a4"]))==3
    print(json.dumps({"selftest":"PASS","version":"0.2.1","atlas":82}))

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    sp.add_parser("selftest")
    p=sp.add_parser("preflight"); p.add_argument("--config",default="configs/quick.json"); p.add_argument("--workbench-root")
    p=sp.add_parser("blind"); p.add_argument("--config",default="configs/ci.json"); p.add_argument("--workbench-root"); p.add_argument("--force-python",action="store_true"); p.add_argument("--overwrite",action="store_true")
    p=sp.add_parser("seal"); p.add_argument("--config",default="configs/ci.json")
    p=sp.add_parser("reveal"); p.add_argument("--config",default="configs/ci.json")
    p=sp.add_parser("package"); p.add_argument("--config",default="configs/ci.json")
    a=ap.parse_args()
    if a.cmd=="selftest": selftest(); return
    cfg=load_json(ROOT/a.config); out=ROOT/cfg["output_dir"]
    if a.cmd=="preflight":
        wb=detect_workbench_root(a.workbench_root)
        print(json.dumps(native_preflight(find_c006_version(wb),cfg["c006_native"]),indent=2)); return
    if a.cmd=="blind": run_blind(ROOT,ROOT/a.config,a.workbench_root,a.force_python,a.overwrite)
    elif a.cmd=="seal": print(json.dumps(seal_blind(out),indent=2))
    elif a.cmd=="reveal": run_reveal(ROOT,out); print("reveal complete")
    elif a.cmd=="package": print([str(x) for x in package_outputs(out)])
if __name__=="__main__":main()
