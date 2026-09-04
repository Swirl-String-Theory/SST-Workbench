from __future__ import annotations
from pathlib import Path
import json, hashlib, csv, math, statistics, os, time
import numpy as np

def dump_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding='utf-8')

def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(path): return sha256_bytes(Path(path).read_bytes())
def geometry_sha256(points, offsets):
    p=np.ascontiguousarray(points,dtype='<f8'); o=np.ascontiguousarray(offsets,dtype='<i8')
    return hashlib.sha256(p.tobytes()+o.tobytes()).hexdigest()
def cv(x):
    x=np.asarray(x,float); m=float(np.mean(x)); return float(np.std(x)/abs(m)) if m else float('inf')
def relerr(a,b): return abs(float(a)-float(b))/abs(float(b)) if b else float('inf')
def linfit(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float); A=np.column_stack([x,np.ones_like(x)]); m,b=np.linalg.lstsq(A,y,rcond=None)[0]; yh=m*x+b
    ssr=float(np.sum((y-yh)**2)); sst=float(np.sum((y-np.mean(y))**2)); r2=1-ssr/sst if sst>0 else 1.0
    return float(m),float(b),float(r2)
def logfit(x,y): return linfit(np.log(np.asarray(x,float)),np.log(np.asarray(y,float)))
def write_csv(path,rows,fields=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if not rows: return
    fields=fields or list(rows[0].keys())
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def read_csv(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def nowstamp(): return time.strftime('%Y%m%d_%H%M%S')
