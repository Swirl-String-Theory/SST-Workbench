from __future__ import annotations
import hashlib, json
from pathlib import Path

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def freeze_outputs(outdir:Path)->dict:
    files=[]
    for p in sorted(outdir.rglob('*')):
        if p.is_file() and p.name not in {'FROZEN_SHA256.json','results_unblinded.json'}:
            files.append({'path':str(p.relative_to(outdir)).replace('\\','/'),'sha256':sha256_file(p),'bytes':p.stat().st_size})
    frozen={'format':1,'frozen':True,'files':files}
    (outdir/'FROZEN_SHA256.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')
    return frozen

def verify_frozen(outdir:Path)->dict:
    p=outdir/'FROZEN_SHA256.json'
    if not p.exists(): return {'ok':False,'reason':'FROZEN_SHA256.json missing'}
    spec=json.loads(p.read_text(encoding='utf-8')); bad=[]
    for e in spec.get('files',[]):
        q=outdir/e['path']
        if not q.exists() or sha256_file(q)!=e['sha256']: bad.append(e['path'])
    return {'ok':not bad,'bad':bad,'count':len(spec.get('files',[]))}
