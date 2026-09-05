from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def robust_cv(values):
    a = np.asarray(values, float)
    a = a[np.isfinite(a)]
    if len(a) < 2:
        return None
    med = float(np.median(a))
    if med == 0:
        return None
    mad = float(np.median(np.abs(a - med)))
    return 1.4826 * mad / abs(med)
