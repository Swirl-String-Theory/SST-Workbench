from __future__ import annotations
from pathlib import Path
import hashlib,json,secrets
import numpy as np
from .geometry import read_xyz,resample_closed

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def _hash_resampled(x,n):
    y=resample_closed(x,n)
    return sha256_bytes(np.ascontiguousarray(y,dtype='<f8').tobytes()),y

def _load_registry(path):
    if not path: return set()
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(f'historical registry not found: {p}')
    d=json.loads(p.read_text(encoding='utf-8'))
    return set(d.get('canonical64_sha256',d.get('hashes',[])))

def prepare(input_dir,out_dir,pattern,n_points,identity_hash_points,novelty_hash_points,mode,registry_path,min_unique):
    inp=Path(input_dir); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    priv=out.parent/'private_reveal'; priv.mkdir(parents=True,exist_ok=True)
    files=sorted(inp.rglob(pattern))
    if not files:
        raise FileNotFoundError(f'no files matching {pattern} under {inp}')
    seen=_load_registry(registry_path)
    groups={}
    for p in files:
        raw=read_xyz(p)
        ident,_=_hash_resampled(raw,identity_hash_points)
        nov,_=_hash_resampled(raw,novelty_hash_points)
        gh,x=_hash_resampled(raw,n_points)
        q=groups.setdefault(ident,{'canonical_sha256':ident,'novelty_sha25664':nov,'geometry_sha256':gh,'x':x,'sources':[]})
        q['sources'].append(str(p.resolve()))
        if q['geometry_sha256']!=gh:
            raise RuntimeError('identity hash collision with differing analysis geometry')
        if q['novelty_sha25664']!=nov:
            raise RuntimeError('identity hash collision with differing novelty hash')
    all_unique=sorted(groups.values(),key=lambda q:q['canonical_sha256'])
    n_seen=sum(q['novelty_sha25664'] in seen for q in all_unique)
    if mode=='confirmatory':
        selected=[q for q in all_unique if q['novelty_sha25664'] not in seen]
    elif mode=='legacy_audit':
        selected=all_unique
    else:
        raise ValueError('mode must be confirmatory or legacy_audit')
    salt=secrets.token_hex(16)
    keyed=[]
    for q in selected:
        bh=sha256_bytes((salt+q['canonical_sha256']).encode())
        keyed.append((bh,q))
    keyed.sort(key=lambda z:z[0])
    reveal=[]; public=[]
    for i,(_,q) in enumerate(keyed,1):
        bid=f'B{i:04d}'
        np.save(out/f'{bid}.npy',q['x'])
        public.append({'blind_id':bid,'canonical_sha256':q['canonical_sha256'],'novelty_sha25664':q['novelty_sha25664'],'geometry_sha256':q['geometry_sha256'],'n':len(q['x'])})
        names=[Path(s).name for s in q['sources']]
        reveal.append({'blind_id':bid,'canonical_sha256':q['canonical_sha256'],'novelty_sha25664':q['novelty_sha25664'],'geometry_sha256':q['geometry_sha256'],
                       'sources':q['sources'],'source_names':names,'duplicate_count':len(q['sources'])})
    audit={
        'format':'SST-PFD-DATASET-AUDIT-2.0','mode':mode,'pattern':pattern,
        'identity_hash_points':int(identity_hash_points),'novelty_hash_points':int(novelty_hash_points),'analysis_points':int(n_points),
        'n_source_files':len(files),'n_unique_before_novelty':len(all_unique),
        'n_duplicate_files_removed':len(files)-len(all_unique),'n_historical_seen_unique':n_seen,
        'n_selected_unique':len(selected),'min_unique_required':int(min_unique),
        'confirmatory_eligible':bool(mode=='confirmatory' and len(selected)>=min_unique),
        'legacy_audit_only':bool(mode!='confirmatory'),
        'max_source_multiplicity':max((len(q['sources']) for q in all_unique),default=0),
        'unique_fraction':len(all_unique)/len(files) if files else 0.0,
    }
    (out/'sealed_manifest.json').write_text(json.dumps({'format':'SST-PFD-BLIND-MANIFEST-2.0','items':public},indent=2),encoding='utf-8')
    (out/'dataset_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    rk={'format':'SST-PFD-REVEAL-2.0','salt':salt,'mode':mode,'items':reveal}
    rtxt=json.dumps(rk,indent=2)
    (priv/'reveal_key.json').write_text(rtxt,encoding='utf-8')
    (out/'reveal_key_sha256.txt').write_text(sha256_bytes(rtxt.encode())+'\n',encoding='utf-8')
    return audit
