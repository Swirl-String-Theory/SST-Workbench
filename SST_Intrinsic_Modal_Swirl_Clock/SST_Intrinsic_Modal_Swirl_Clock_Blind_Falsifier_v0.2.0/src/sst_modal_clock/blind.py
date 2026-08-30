from pathlib import Path
import hashlib,json,random,secrets
import numpy as np
from .geometry import discover,resample_closed,normalize,broadband_probe
from .solver import segment_lengths
from .util import clean_json

def prepare(dataset,work,cfg):
    work=Path(work); (work/'prepared').mkdir(parents=True,exist_ok=True); (work/'private').mkdir(parents=True,exist_ok=True)
    files=discover(dataset,cfg.get('source_regex')); files=files[:int(cfg.get('max_carriers',9999))]
    rng=random.Random(int(cfg.get('blind_seed',20260827))); flip=rng.choice([-1,1]); public=[]; private=[]; n=int(cfg['n_points']); eps=float(cfg['probe_eps'])
    for path,raw in files:
        base,scale=normalize(resample_closed(raw,n)); probe=broadband_probe(base,tuple(cfg.get('probe_harmonics',[1,2,3,4])))
        carrier=hashlib.sha256((str(path.resolve())+'|'+str(cfg.get('blind_seed',20260827))).encode()).hexdigest()[:16]; pair='P'+carrier[:10]; ref=segment_lengths(base); dtref=float(np.min(ref))
        for arm in (-1,0,1):
            physical=arm*flip; x=base+physical*eps*probe if arm else base.copy(); cid=secrets.token_hex(8); rel=f'prepared/{cid}.npz'
            np.savez_compressed(work/rel,x=x,x_reference=base,reference_lengths=ref)
            public.append({'candidate_id':cid,'pair_id':pair,'carrier_id':carrier,'probe_arm':arm,'data':rel,'dt_reference_ds':dtref})
            private.append({'candidate_id':cid,'pair_id':pair,'carrier_id':carrier,'source_path':str(path),'source_name':path.name,'source_scale':scale,'physical_probe_sign':physical})
    rng.shuffle(public); (work/'blind_catalog.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in public),encoding='utf-8')
    priv={'secret_probe_flip':flip,'rows':private}; pb=json.dumps(priv,sort_keys=True,indent=2).encode(); (work/'private/reveal_map.json').write_bytes(pb)
    s={'format':'SST-INTRINSIC-MODAL-PREPARE-2.0','n_carriers':len(files),'n_pairs':len(files),'n_candidates':len(public),'candidate_arms':[-1,0,1],'blind_fields_hidden':['source_path','source_name','source_scale','physical_probe_sign'],'private_key_commitment_sha256':hashlib.sha256(pb).hexdigest(),'seed_source':'Ridgerunner/KnotPlot relaxed centerlines','qhp_used':False,'baseline_arm_added':True}
    (work/'prepare_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return s

def load_catalog(work):
    return [json.loads(x) for x in (Path(work)/'blind_catalog.jsonl').read_text().splitlines() if x.strip()]
