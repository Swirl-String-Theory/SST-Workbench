from __future__ import annotations
from pathlib import Path
import hashlib, json, math
from dataclasses import is_dataclass, asdict
from typing import Any

def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()

def json_safe(x: Any) -> Any:
    if is_dataclass(x): return json_safe(asdict(x))
    if isinstance(x, dict): return {str(k):json_safe(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [json_safe(v) for v in x]
    try:
        import numpy as np
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,np.generic): return x.item()
    except Exception: pass
    if isinstance(x,float) and not math.isfinite(x): return None
    return x

def write_json(path: str | Path, obj: Any) -> None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(json_safe(obj),indent=2,sort_keys=True),encoding='utf-8')
