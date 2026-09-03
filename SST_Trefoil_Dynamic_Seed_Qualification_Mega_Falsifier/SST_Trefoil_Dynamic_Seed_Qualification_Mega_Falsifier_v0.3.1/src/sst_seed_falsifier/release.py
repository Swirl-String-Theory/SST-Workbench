from __future__ import annotations
from pathlib import Path
import hashlib,json
from . import __version__


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def release_identity(root=None):
    root=Path(root) if root else Path(__file__).resolve().parents[2]
    p=root/'RELEASE.json'
    if not p.is_file(): return {'match':False,'error':'RELEASE.json missing','runtime_version':__version__}
    d=json.loads(p.read_text(encoding='utf-8'))
    return {'match':str(d.get('version'))==str(__version__),'runtime_version':__version__,
            'declared_version':str(d.get('version')),'release_sha256':sha256_file(p),'release':d}
