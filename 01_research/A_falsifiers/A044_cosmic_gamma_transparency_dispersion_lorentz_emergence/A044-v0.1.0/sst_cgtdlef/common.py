\
from __future__ import annotations
from pathlib import Path
import hashlib, json, math

PROJECT = "SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier"
VERSION = "v0.1.0"
OUTPUT_DIR = f"{PROJECT}_{VERSION}-outputs"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def sci(x: float) -> str:
    if math.isinf(x): return "inf"
    return f"{x:.8e}"
