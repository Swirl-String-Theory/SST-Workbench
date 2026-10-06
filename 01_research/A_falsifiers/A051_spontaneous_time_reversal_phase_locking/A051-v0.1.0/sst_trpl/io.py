from __future__ import annotations
from pathlib import Path
import json, hashlib
import numpy as np

def load_manifest(path):
    path=Path(path); m=json.loads(path.read_text(encoding='utf-8'))
    arr=path.parent/m['arrays_file']; z=np.load(arr,allow_pickle=False)
    return m,z['t'],z['eta'],z['energy'],(z['residual'] if 'residual' in z.files else None)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
