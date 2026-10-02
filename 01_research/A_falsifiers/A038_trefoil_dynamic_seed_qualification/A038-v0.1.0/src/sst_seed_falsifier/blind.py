import secrets,hmac,hashlib,json
from pathlib import Path
from .io import dump_json

def make_blind_ids(records,outdir):
    out=Path(outdir); (out/'private').mkdir(parents=True,exist_ok=True); key=secrets.token_bytes(32); mapping={}; pub=[]
    for i,r in enumerate(records):
        msg=f"{i}|{r['geom_sha']}".encode(); aid='C'+hmac.new(key,msg,hashlib.sha256).hexdigest()[:14].upper(); mapping[aid]=r; pub.append({'candidate_id':aid,'geom_sha':r['geom_sha']})
    (out/'private'/'blind_key.bin').write_bytes(key); dump_json(out/'private'/'identity_map.json',mapping)
    commitment=hashlib.sha256(key).hexdigest(); dump_json(out/'public_manifest.json',{'format':'SST-TREFOIL-SEED-BLIND-1','n_candidates':len(pub),'private_key_commitment_sha256':commitment,'candidates':pub,'identity_read_by_scoring':False})
    return pub,mapping
