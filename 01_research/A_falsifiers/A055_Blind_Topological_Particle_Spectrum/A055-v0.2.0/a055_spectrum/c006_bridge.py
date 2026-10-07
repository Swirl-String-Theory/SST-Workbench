from __future__ import annotations
import importlib,sys
from pathlib import Path
from .util import sha256_file

def import_c006(c006_root):
    root=Path(c006_root).resolve()
    if not (root/"sst_kelvin_workbench").is_dir():
        raise FileNotFoundError(f"C006 package missing under {root}")
    s=str(root)
    if s not in sys.path: sys.path.insert(0,s)
    return {
      "dynamics":importlib.import_module("sst_kelvin_workbench.dynamics"),
      "spectral":importlib.import_module("sst_kelvin_workbench.spectral_cert"),
      "orbit":importlib.import_module("sst_kelvin_workbench.orbit"),
      "monodromy":importlib.import_module("sst_kelvin_workbench.monodromy"),
    }
def provenance(c006_root):
    root=Path(c006_root).resolve(); files={}
    for rel in ["sst_kelvin_workbench/dynamics.py","sst_kelvin_workbench/backend.py",
                "sst_kelvin_workbench/spectral_cert.py","sst_kelvin_workbench/orbit.py",
                "sst_kelvin_workbench/monodromy.py","SPECTRAL_THRESHOLDS_FROZEN.json","THRESHOLDS_FROZEN.json"]:
        p=root/rel
        if p.exists(): files[rel]={"path":str(p),"sha256":sha256_file(p)}
    return {"c006_root":str(root),"version":"0.3.0","files":files}
