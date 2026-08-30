from pathlib import Path
import json,hashlib,secrets,random
import numpy as np
from .geometry import discover,resample_closed,normalize,perturb
from .util import clean_json

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def prepare(dataset,workdir,cfg):
    work=Path(workdir); (work/'prepared/candidates').mkdir(parents=True,exist_ok=True); (work/'private').mkdir(parents=True,exist_ok=True)
    files=discover(dataset); maxc=int(cfg.get('max_carriers',8)); files=files[:maxc]
    seed=int(cfg.get('blind_seed',20260827)); rng=random.Random(seed)
    secret_packet=rng.choice([-1,1]); secret_breath=rng.choice([-1,1])
    public=[]; private=[]; n=int(cfg['n_points'])
    centers=cfg.get('packet_centers',[0.0]); breath_arms=cfg.get('breathing_arms',[-1,1])
    pair_i=0
    for ci,(path,raw) in enumerate(files):
        base,scale=normalize(resample_closed(raw,n)); base_reference_lengths=np.linalg.norm(np.roll(base,-1,axis=0)-base,axis=1); carrier_id=hashlib.sha256((str(path)+str(seed)).encode()).hexdigest()[:16]
        for ba in breath_arms:
            physical_breath=int(ba)*secret_breath
            breath_only=perturb(base,float(cfg['breathing_eps']),physical_breath,0.0,1,0.0,float(cfg['packet_width_frac']))
            dt_reference_ds=float(np.min(np.linalg.norm(np.roll(breath_only,-1,axis=0)-breath_only,axis=1)))
            for center in centers:
                pair_id=f'P{pair_i:05d}'; pair_i+=1
                rows=[]
                for anon_packet in (-1,1):
                    physical_packet=anon_packet*secret_packet
                    x=perturb(base,float(cfg['breathing_eps']),physical_breath,float(cfg['packet_eps']),physical_packet,float(center),float(cfg['packet_width_frac']))
                    cid=secrets.token_hex(8); rel=f'prepared/candidates/{cid}.npz'; np.savez_compressed(work/rel,x=x,reference_lengths=base_reference_lengths)
                    rec={'candidate_id':cid,'pair_id':pair_id,'carrier_id':carrier_id,'data':rel,'packet_arm':anon_packet,'breathing_arm':int(ba),'packet_center_frac':float(center),'dt_reference_ds':dt_reference_ds}
                    public.append(rec); rows.append(cid)
                    private.append({'candidate_id':cid,'pair_id':pair_id,'carrier_id':carrier_id,'source_path':str(path),'source_scale':scale,'physical_packet_polarity':physical_packet,'physical_breathing_sign':physical_breath,'packet_center_frac':float(center)})
    rng.shuffle(public)
    (work/'blind_catalog.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in public),encoding='utf-8')
    priv={'secret_packet_flip':secret_packet,'secret_breath_flip':secret_breath,'rows':private}
    pb=json.dumps(priv,sort_keys=True,indent=2).encode(); (work/'private/reveal_map.json').write_bytes(pb)
    commitment=sha256_bytes(pb)
    summary={'format':'SST-BSRP-PREPARE-1.0','n_carriers':len(files),'n_candidates':len(public),'n_pairs':pair_i,'blind_fields_hidden':['source_path','physical_packet_polarity','physical_breathing_sign','source_scale'],'private_key_commitment_sha256':commitment,'condition_semantics_read_by_runner':False}
    (work/'prepare_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    return summary

def load_catalog(work):
    return [json.loads(x) for x in (Path(work)/'blind_catalog.jsonl').read_text().splitlines() if x.strip()]
