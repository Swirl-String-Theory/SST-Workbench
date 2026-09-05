from __future__ import annotations
import hashlib, json, secrets
from pathlib import Path
import numpy as np
from .io import save_xyz


def geometry_sha256(points):
    p=np.asarray(points,dtype='<f8')
    return hashlib.sha256(p.tobytes(order='C')).hexdigest()


def make_blind_campaign(candidates, outdir, seed=None):
    """Write anonymous geometry files + private reveal manifest.

    candidates: iterable of (label, points, metadata)
    """
    out=Path(outdir); pub=out/'public'; priv=out/'private'
    pub.mkdir(parents=True,exist_ok=True); priv.mkdir(parents=True,exist_ok=True)
    items=list(candidates)
    if seed is None:
        seed = secrets.randbits(128)
    rng=np.random.default_rng(seed); order=rng.permutation(len(items))
    public=[]; reveal=[]
    for anon_i,src_i in enumerate(order):
        label,pts,meta=items[src_i]
        anon=f'C{anon_i+1:04d}'
        fn=f'{anon}.xyz'; save_xyz(pub/fn,pts)
        h=geometry_sha256(pts)
        public.append({'candidate_id':anon,'file':fn,'sha256':h})
        reveal.append({'candidate_id':anon,'source_label':label,'sha256':h,'metadata':meta})
    (pub/'manifest.json').write_text(json.dumps(public,indent=2),encoding='utf-8')
    reveal_text=json.dumps(reveal,indent=2)
    (priv/'reveal.json').write_text(reveal_text,encoding='utf-8')
    (priv/'blind_seed.txt').write_text(str(seed)+'\n',encoding='utf-8')
    commitment=hashlib.sha256(reveal_text.encode()).hexdigest()
    (pub/'reveal_commitment.sha256').write_text(commitment+'\n',encoding='utf-8')
    return commitment
