from pathlib import Path
import argparse
import json
import os
import platform
import sys
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["python", "native"], required=True)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parent
BLIND = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs" / "BLIND"
data = {
    "mode": args.mode,
    "python": sys.version,
    "python_executable": sys.executable,
    "platform": platform.platform(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "numpy": np.__version__,
    "SST_BACKEND": os.environ.get("SST_BACKEND"),
}
(BLIND / f"runtime_{args.mode}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps(data, indent=2))
