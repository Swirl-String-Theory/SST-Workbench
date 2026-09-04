from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix


def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path: str | Path,obj) -> None:
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def load_xyz(path: str | Path, component_counts=None):
    """Read shared-final XYZ/TXT.

    KnotPlot shared-final link files may concatenate components without blank lines.
    When component_counts comes from the paired *.metrics.json it is authoritative for splitting.
    """
    rows=[]; blank_breaks=[]; since=0
    for raw in Path(path).read_text(encoding="utf-8",errors="strict").splitlines():
        line=raw.strip()
        if not line:
            if since: blank_breaks.append(len(rows)); since=0
            continue
        if line.startswith("#"): continue
        vals=line.replace(","," ").split()
        if len(vals)<3: raise ValueError(f"Bad XYZ line in {path}: {raw}")
        rows.append([float(vals[0]),float(vals[1]),float(vals[2])]); since+=1
    P=np.asarray(rows,dtype=float)
    if len(P)==0: raise ValueError(f"No vertices in {path}")
    if component_counts is not None:
        counts=[int(x) for x in component_counts]
        if sum(counts)!=len(P): raise ValueError(f"component_counts sum {sum(counts)} != {len(P)} vertices for {path}")
        comps=[]; k=0
        for n in counts: comps.append(P[k:k+n].copy()); k+=n
        return comps
    cuts=[x for x in blank_breaks if 0<x<len(P)]
    if not cuts: return [P]
    comps=[]; k=0
    for c in cuts+[len(P)]: comps.append(P[k:c]); k=c
    return comps


def flatten_components(comps): return np.vstack(comps)


def native_to_sparse(result):
    shape=tuple(int(x) for x in result["shape"])
    rows=np.asarray(result["rows"],dtype=np.int64); cols=np.asarray(result["cols"],dtype=np.int64); data=np.asarray(result["data"],dtype=float)
    A=coo_matrix((data,(rows,cols)),shape=shape).tocsr()
    A.sum_duplicates(); A.eliminate_zeros()
    return A,np.asarray(result["b"],dtype=float)


def write_records(path: str | Path, rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); rows=list(rows)
    if not rows: p.write_text("",encoding="utf-8"); return
    fields=list(rows[0].keys())
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def read_csv_records(path: str | Path):
    p=Path(path)
    if not p.exists() or p.stat().st_size==0: return []
    with p.open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
