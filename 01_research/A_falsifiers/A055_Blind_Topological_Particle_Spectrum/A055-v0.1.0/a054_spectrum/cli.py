from __future__ import annotations
from pathlib import Path
import argparse, json, math, shutil
from .atlas import load_atlas, validate_pd, component_cycles
from .geometry import build_embedding
from .backend import measure, native_available, backend_name
from .blind import run_blind, seal_blind, verify_seal
from .reveal import run_reveal
from .packaging import package_outputs
from .util import load_json, sha256_file

ROOT=Path(__file__).resolve().parents[1]

def selftest(force_python=False, require_native=False):
    atlas=load_atlas(ROOT)
    assert len(atlas)==82
    assert sum(r["kind"]=="knot" for r in atlas)==35
    assert sum(r["kind"]=="link" for r in atlas)==47
    for r in atlas: validate_pd(r)
    by={r["id"]:r for r in atlas}
    assert len(component_cycles(by["3_1"]))==1
    assert len(component_cycles(by["L2a1"]))==2
    assert len(component_cycles(by["L6a4"]))==3
    assert len(component_cycles(by["L8n8"]))==4

    g=build_embedding(by["5_2"],32,"selftest",0)
    py=measure(g,0.03,force_python=True)
    if require_native and not native_available():
        raise RuntimeError("Native backend required but a054_native is not importable")
    if native_available() and not force_python:
        na=measure(g,0.03,force_python=False)
        keys=["total_length","bend_energy","min_distance","contact_ratio","neumann_energy","writhe","linking_strength"]
        for k in keys:
            den=max(1.0,abs(py[k]),abs(na[k]))
            if abs(py[k]-na[k])/den > 5e-10:
                raise AssertionError(f"native/python parity failed {k}: {py[k]} vs {na[k]}")
    print(json.dumps({"selftest":"PASS","atlas":82,"backend":backend_name(force_python),"native_available":native_available()}))

def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("selftest"); p.add_argument("--force-python",action="store_true"); p.add_argument("--require-native",action="store_true")
    p=sp.add_parser("blind"); p.add_argument("--config",default="configs/basic.json"); p.add_argument("--force-python",action="store_true"); p.add_argument("--overwrite",action="store_true")
    p=sp.add_parser("seal"); p.add_argument("--config",default="configs/basic.json")
    p=sp.add_parser("reveal"); p.add_argument("--config",default="configs/basic.json")
    p=sp.add_parser("package"); p.add_argument("--config",default="configs/basic.json")
    args=ap.parse_args()
    if args.cmd=="selftest":
        selftest(args.force_python,args.require_native); return
    cfg=load_json(ROOT/args.config); out=ROOT/cfg["output_dir"]
    if args.cmd=="blind":
        if cfg.get("strict_native") and not args.force_python and not native_available():
            raise RuntimeError("Config is strict_native but native backend is unavailable. Build C++ first or pass --force-python explicitly.")
        run_blind(ROOT,ROOT/args.config,args.force_python,args.overwrite)
    elif args.cmd=="seal":
        print(json.dumps(seal_blind(out),indent=2))
    elif args.cmd=="reveal":
        run_reveal(ROOT,out); print("reveal complete")
    elif args.cmd=="package":
        print([str(p) for p in package_outputs(out)])

if __name__=="__main__": main()
