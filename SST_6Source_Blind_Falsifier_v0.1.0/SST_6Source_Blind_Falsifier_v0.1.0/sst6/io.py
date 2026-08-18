from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class CurveDataset:
    item_id: str
    path: Path
    components: list[np.ndarray]
    metrics: dict
    sha256: str


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_curve_txt(path: Path) -> list[np.ndarray]:
    comps=[]; cur=[]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s=raw.strip()
        if not s:
            if cur:
                comps.append(np.asarray(cur,dtype=float)); cur=[]
            continue
        if s.startswith("#") or s.startswith("//"):
            continue
        parts=s.replace(","," ").split()
        if len(parts)<3:
            continue
        try:
            cur.append([float(parts[0]),float(parts[1]),float(parts[2])])
        except ValueError:
            continue
    if cur: comps.append(np.asarray(cur,dtype=float))
    if not comps:
        raise ValueError(f"No XYZ components parsed from {path}")
    for c in comps:
        if len(c)<8:
            raise ValueError(f"Component too short ({len(c)} points) in {path}")
    return comps


def load_metrics(txt_path: Path) -> dict:
    p=txt_path.with_suffix(".metrics.json")
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: return {}
    return {}


def load_dataset(path: Path) -> CurveDataset:
    return CurveDataset(
        item_id=path.stem,
        path=path.resolve(),
        components=parse_curve_txt(path),
        metrics=load_metrics(path),
        sha256=sha256_file(path),
    )


def discover_datasets(dataset_dir: Path, pattern: str="*_final.txt") -> list[CurveDataset]:
    files=sorted(dataset_dir.glob(pattern))
    if not files:
        files=sorted(dataset_dir.glob("*.txt"))
    return [load_dataset(p) for p in files]


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    fields=[]
    for r in rows:
        for k in r.keys():
            if k not in fields: fields.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(rows)
