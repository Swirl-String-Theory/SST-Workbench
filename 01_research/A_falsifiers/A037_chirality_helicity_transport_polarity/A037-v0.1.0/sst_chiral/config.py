from __future__ import annotations
from pathlib import Path
from .util import read_json

def load_config(path):
    cfg=read_json(path)
    cfg["_config_path"] = str(Path(path).resolve())
    return cfg
