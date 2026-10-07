from __future__ import annotations
from pathlib import Path
import json, hashlib, csv

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def write_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding='utf-8')

def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def write_csv(path, rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    rows=list(rows)
    if not rows:
        p.write_text('',encoding='utf-8'); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
