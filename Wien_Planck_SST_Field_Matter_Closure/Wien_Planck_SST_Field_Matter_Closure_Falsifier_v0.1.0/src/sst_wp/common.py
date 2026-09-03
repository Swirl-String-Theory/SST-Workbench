
from __future__ import annotations
import csv, json, math, statistics, hashlib, random
from pathlib import Path

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No rows to write")
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def dump_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)

def ffloat(x):
    return float(x)

def mean(xs):
    return statistics.fmean(xs)

def cv(xs):
    m = mean(xs)
    return float("inf") if m == 0 else statistics.pstdev(xs)/abs(m)

def relerr(a,b):
    return abs(a-b)/abs(b) if b != 0 else float("inf")

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def linreg_log(x, y):
    lx=[math.log(v) for v in x]
    ly=[math.log(v) for v in y]
    xm=mean(lx); ym=mean(ly)
    den=sum((a-xm)**2 for a in lx)
    if den == 0:
        return float("nan"), float("nan")
    slope=sum((a-xm)*(b-ym) for a,b in zip(lx,ly))/den
    intercept=ym-slope*xm
    return slope, intercept
