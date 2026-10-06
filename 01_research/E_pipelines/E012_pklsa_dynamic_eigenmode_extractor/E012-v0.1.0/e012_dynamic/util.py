from __future__ import annotations
import hashlib, json, math
from pathlib import Path
from typing import Any

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def jsonable(x: Any):
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return [jsonable(v) for v in x.tolist()]
        if isinstance(x, np.generic):
            return x.item()
    except Exception:
        pass
    if isinstance(x, complex):
        return {"re": float(x.real), "im": float(x.imag)}
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k,v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, Path):
        return str(x)
    return x

def dump_json(path: str | Path, obj: Any):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(jsonable(obj), indent=2, sort_keys=False) + "\n", encoding="utf-8")

def polygon_length(points) -> float:
    import numpy as np
    p = np.asarray(points, dtype=float)
    return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())

def relative_shift(a: float, b: float, floor: float = 1e-30) -> float:
    return abs(float(b)-float(a))/max(abs(float(a)),abs(float(b)),floor)

def centered_slopes(x, y):
    if len(x) != len(y) or len(x) < 3:
        return []
    out=[]
    for i in range(1,len(x)-1):
        dx=float(x[i+1])-float(x[i-1])
        if dx == 0:
            raise ValueError("duplicate x in centered slope")
        out.append({
            "index": i,
            "x": float(x[i]),
            "slope": (float(y[i+1])-float(y[i-1]))/dx,
        })
    return out
