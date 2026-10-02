from pathlib import Path
import argparse
import hashlib
import importlib
import json
import platform
import sys
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["python", "native"], required=True)
args = parser.parse_args()

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs" / "BLIND"
OUT.mkdir(parents=True, exist_ok=True)

record = {
    "mode": args.mode,
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "machine": platform.machine(),
    "numpy": np.__version__,
}
try:
    import pybind11
    record["pybind11"] = pybind11.__version__
except Exception:
    record["pybind11"] = None

if args.mode == "native":
    mod = importlib.import_module("triadic_native")
    p = Path(mod.__file__).resolve()
    record["native_module_path"] = str(p)
    record["native_module_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    record["native_module_size_bytes"] = p.stat().st_size

path = OUT / f"runtime_{args.mode}.json"
path.write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record, indent=2))
