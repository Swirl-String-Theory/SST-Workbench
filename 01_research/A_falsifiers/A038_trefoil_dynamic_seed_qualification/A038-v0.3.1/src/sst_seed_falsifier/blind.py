import secrets,hmac,hashlib,json
from pathlib import Path
from .io import dump_json
from .evidence import object_sha256

def sealed_private_dir(outdir):
    out=Path(outdir)
    return out.parent/f'{out.name}_sealed_private'

def make_blind_ids(records,outdir,private_dir=None):
    out=Path(outdir); private=Path(private_dir) if private_dir is not None else sealed_private_dir(out)
    private.mkdir(parents=True,exist_ok=True); key=secrets.token_bytes(32); mapping={}; pub=[]
    for i,r in enumerate(records):
        msg=f"{i}|{r['geom_sha']}".encode(); aid='C'+hmac.new(key,msg,hashlib.sha256).hexdigest()[:14].upper(); mapping[aid]=r; pub.append({'candidate_id':aid,'geom_sha':r['geom_sha']})
    (private/'blind_key.bin').write_bytes(key); dump_json(private/'identity_map.json',mapping)
    commitment=hashlib.sha256(key).hexdigest(); dump_json(out/'public_manifest.json',{'format':'SST-TREFOIL-SEED-BLIND-3','n_candidates':len(pub),'private_key_commitment_sha256':commitment,'private_key_commitment_hash_basis':'raw_bytes_sha256_v1','identity_map_commitment_sha256':object_sha256(mapping),'identity_map_commitment_hash_basis':'canonical_json_sorted_compact_ascii_v1','sealed_private_bundle_name':private.name,'candidates':pub,'identity_read_by_scoring':False})
    return pub,mapping
