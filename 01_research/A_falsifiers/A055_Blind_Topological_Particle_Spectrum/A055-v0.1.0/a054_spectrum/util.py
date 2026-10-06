from __future__ import annotations
from pathlib import Path
import json, hashlib, hmac, math, os, csv

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def case_id(secret: bytes, topology_id: str) -> str:
    return "CASE_" + hmac.new(secret, topology_id.encode(), hashlib.sha256).hexdigest()[:16].upper()

def mean(xs):
    return sum(xs)/len(xs) if xs else float("nan")

def stdev(xs):
    if len(xs)<2: return 0.0
    m=mean(xs)
    return math.sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))

def cv(xs):
    m=abs(mean(xs))
    return stdev(xs)/(m+1e-15)

def zscores(values):
    m=mean(values); s=stdev(values)
    if s < 1e-15: return [0.0]*len(values)
    return [(x-m)/s for x in values]
