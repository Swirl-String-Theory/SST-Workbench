from __future__ import annotations
from pathlib import Path
import hashlib,hmac,secrets,json,shutil,numpy as np
from .io import discover,load_curve,sidecars

PACKAGE_VERSION='0.1.2'


def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def canonical_json_bytes(obj, *, pretty=True):
    if pretty:
        txt=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
    else:
        txt=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return txt.encode('utf-8')


def write_json_bytes(path:Path,obj):
    b=canonical_json_bytes(obj,pretty=True)
    path.write_bytes(b)
    return hashlib.sha256(b).hexdigest()


def _inventory(dataset:Path):
    dataset=dataset.resolve()
    rows=[]
    for p in discover(dataset):
        rel=p.resolve().relative_to(dataset).as_posix()
        rows.append({'relpath':rel,'sha256':sha256_file(p)})
    if not rows:
        raise RuntimeError(f'No coordinate files found under {dataset}')
    snap=hashlib.sha256(canonical_json_bytes(rows,pretty=False)).hexdigest()
    return rows,snap


def _shared_seed(state_dir:Path|None,snapshot_sha256:str,holdout_fraction:float,seed_hex=None):
    if seed_hex:
        return bytes.fromhex(seed_hex), 'explicit-seed'
    if state_dir is None:
        return secrets.token_bytes(32), 'ephemeral-random'
    state_dir.mkdir(parents=True,exist_ok=True)
    htag=int(round(float(holdout_fraction)*10000))
    state_file=state_dir/f'{snapshot_sha256[:24]}_h{htag:04d}.json'
    if state_file.exists():
        st=json.loads(state_file.read_text(encoding='utf-8'))
        if st.get('dataset_snapshot_sha256')!=snapshot_sha256:
            raise RuntimeError('blind-state snapshot mismatch')
        if abs(float(st.get('holdout_fraction'))-float(holdout_fraction))>1e-12:
            raise RuntimeError('blind-state holdout fraction mismatch')
        return bytes.fromhex(st['seed_hex']), state_file.name
    st={'version':PACKAGE_VERSION,'dataset_snapshot_sha256':snapshot_sha256,
        'holdout_fraction':float(holdout_fraction),'seed_hex':secrets.token_hex(32)}
    write_json_bytes(state_file,st)
    return bytes.fromhex(st['seed_hex']),state_file.name


def prepare(dataset:Path,run_dir:Path,holdout_fraction=0.3,seed_hex=None,state_dir:Path|None=None):
    dataset=dataset.resolve(); inventory,snapshot=_inventory(dataset)
    file_map={r['relpath']:r['sha256'] for r in inventory}
    seed,state_id=_shared_seed(state_dir,snapshot,holdout_fraction,seed_hex)
    bdir=run_dir/'blind'; cdir=bdir/'cases'; cdir.mkdir(parents=True,exist_ok=True)
    private={'version':PACKAGE_VERSION,'seed_hex':seed.hex(),'blind_state_id':state_id,
             'dataset':str(dataset),'dataset_snapshot_sha256':snapshot,'cases':{}}
    public={'version':PACKAGE_VERSION,'n_cases':0,'dataset_snapshot_sha256':snapshot,
            'blind_state_id':state_id,'holdout_fraction':float(holdout_fraction),'cases':[]}
    for rel,digest in file_map.items():
        p=dataset/Path(rel)
        try: comps,pinfo=load_curve(p,return_info=True)
        except Exception: continue
        # Include the relative path as well as content digest so byte-identical duplicate
        # files cannot collide on case ID or overwrite one another.
        case_key=(rel+'\0'+digest).encode('utf-8')
        tag=hmac.new(seed,case_key,hashlib.sha256).hexdigest()
        cid='C'+tag[:12].upper()
        split='holdout' if (int(tag[12:20],16)/0xffffffff)<holdout_fraction else 'train'
        case_path=cdir/f'{cid}.npz'
        np.savez_compressed(case_path, **{f'component_{i}':c for i,c in enumerate(comps)})
        sc=sidecars(p); copied={}
        for k,sp in sc.items():
            dst=cdir/f'{cid}.{k}{sp.suffix}'
            shutil.copy2(sp,dst); copied[k]=dst.name
        meta={'parser':pinfo,'component_lengths':[int(len(c)) for c in comps],
              'n_components':len(comps),'coordinate_sha256':digest}
        write_json_bytes(cdir/f'{cid}.meta.json',meta)
        private['cases'][cid]={'source':str(p.resolve()),'relative_source':rel,'sha256':digest,
                               'parser':pinfo,'sidecars':{k:str(v.resolve()) for k,v in sc.items()}}
        public['cases'].append({'case_id':cid,'split':split,'sidecars':sorted(copied.keys()),
                                'n_components':len(comps),'parser_method':pinfo.get('method','unknown')})
    public['n_cases']=len(public['cases'])
    if not public['n_cases']: raise RuntimeError('Files were found but none parsed as coordinate curves')
    private_hash=write_json_bytes(bdir/'private_mapping.json',private)
    public['private_commitment_sha256']=private_hash
    write_json_bytes(bdir/'public_manifest.json',public)
    return public
