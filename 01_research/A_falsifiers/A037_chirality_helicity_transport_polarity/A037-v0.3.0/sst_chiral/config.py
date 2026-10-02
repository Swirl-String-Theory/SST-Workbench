from __future__ import annotations
import json
from pathlib import Path


def load_config(path: str | Path) -> dict:
    p = Path(path)
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cfg["_config_path"] = str(p.resolve())
    return cfg
