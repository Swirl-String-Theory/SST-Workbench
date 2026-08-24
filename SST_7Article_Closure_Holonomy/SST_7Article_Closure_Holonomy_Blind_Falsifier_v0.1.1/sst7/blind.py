from __future__ import annotations
from pathlib import Path
import hashlib,hmac,secrets,json,shutil,numpy as np
from .io import discover,load_curve,sidecars

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def prepare(dataset:Path,run_dir:Path,holdout_fraction=0.3,seed_hex=None):
    files=discover(dataset)
    if not files: raise RuntimeError(f'No coordinate files found under {dataset}')
    bdir=run_dir/'blind'; cdir=bdir/'cases'; cdir.mkdir(parents=True,exist_ok=True)
    seed=bytes.fromhex(seed_hex) if seed_hex else secrets.token_bytes(32)
    private={'seed_hex':seed.hex(),'dataset':str(dataset.resolve()),'cases':{}}
    public={'version':'0.1.1','n_cases':0,'cases':[]}
    for p in files:
        try: comps=load_curve(p)
        except Exception: continue
        digest=sha256_file(p)
        tag=hmac.new(seed,digest.encode(),hashlib.sha256).hexdigest()
        cid='C'+tag[:12].upper()
        split='holdout' if (int(tag[12:20],16)/0xffffffff)<holdout_fraction else 'train'
        np.savez_compressed(cdir/f'{cid}.npz', **{f'component_{i}':c for i,c in enumerate(comps)})
        sc=sidecars(p); copied={}
        for k,sp in sc.items():
            dst=cdir/f'{cid}.{k}{sp.suffix}'
            shutil.copy2(sp,dst); copied[k]=dst.name
        private['cases'][cid]={'source':str(p.resolve()),'sha256':digest,'sidecars':{k:str(v.resolve()) for k,v in sc.items()}}
        public['cases'].append({'case_id':cid,'split':split,'sidecars':sorted(copied.keys())})
    public['n_cases']=len(public['cases'])
    if not public['n_cases']: raise RuntimeError('Files were found but none parsed as coordinate curves')
    priv_txt=json.dumps(private,indent=2,sort_keys=True)
    (bdir/'private_mapping.json').write_text(priv_txt,encoding='utf-8')
    public['private_commitment_sha256']=hashlib.sha256(priv_txt.encode()).hexdigest()
    pub_txt=json.dumps(public,indent=2,sort_keys=True)
    (bdir/'public_manifest.json').write_text(pub_txt,encoding='utf-8')
    return public
