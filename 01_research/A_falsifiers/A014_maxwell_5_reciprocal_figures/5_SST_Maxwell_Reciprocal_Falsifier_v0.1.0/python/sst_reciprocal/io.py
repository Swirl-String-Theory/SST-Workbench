from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.io import mmread


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path: str | Path, obj) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_xyz(path: str | Path):
    comps, cur = [], []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            if cur:
                comps.append(np.asarray(cur, dtype=float)); cur=[]
            continue
        if line.startswith("#"):
            continue
        vals = line.replace(",", " ").split()
        if len(vals) < 3:
            raise ValueError(f"Bad XYZ line in {path}: {raw}")
        cur.append([float(vals[0]), float(vals[1]), float(vals[2])])
    if cur: comps.append(np.asarray(cur, dtype=float))
    if not comps: raise ValueError(f"No vertices in {path}")
    return comps


def flatten_components(comps):
    return np.vstack(comps)


def load_native_matrix(native_dir: str | Path):
    native_dir = Path(native_dir)
    A = mmread(native_dir / "A.mtx").tocsr().astype(float)
    b = []
    with open(native_dir / "b_length_gradient.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            b.extend([float(r["x"]), float(r["y"]), float(r["z"])])
    return A, np.asarray(b, dtype=float)


def read_csv_records(path: str | Path):
    p=Path(path)
    if not p.exists(): return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
