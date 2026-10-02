from pathlib import Path
import hashlib,json,random,secrets,re
import numpy as np
from .geometry import discover,resample_closed,normalize,broadband_probe,normalize_components
from .solver import segment_lengths
from .sources import discover_all_sources
from .util import clean_json

def _write_prepared(work,cfg,seed_rows,seed_source_label,source_summary=None):
    work=Path(work);(work/'prepared').mkdir(parents=True,exist_ok=True);(work/'private').mkdir(parents=True,exist_ok=True)
    rng=random.Random(int(cfg.get('blind_seed',20260827)));flip=rng.choice([-1,1]);public=[];private=[];eps=float(cfg['probe_eps']);priority_rx=[re.compile(x,re.I) for x in cfg.get('priority_topology_patterns',cfg.get('priority_source_patterns',[]))];priority_groups=set();topology_groups=set();prov_counts={};family_carrier_slots=set()
    for item in seed_rows:
        path=item['path'];source_name=item['source_name'];topology=item['topology_id'];provenance=item.get('provenance','relaxed');record=item.get('source_record_id',source_name);base=item['base'];offsets=np.asarray(item['component_offsets'],dtype=np.int64);scale=float(item['scale']);metadata=item.get('metadata',{})
        topology_group=hashlib.sha256((topology+'|group|'+str(cfg.get('blind_seed',20260827))).encode()).hexdigest()[:14]
        source_family={'relaxed':'KnotPlot','fseries':'Fremlin','ideal':'Gilbert','ideal_links':'Gilbert','katlas':'Katlas'}.get(provenance,provenance)
        provenance_group=hashlib.sha256((source_family+'|source-family|'+str(cfg.get('blind_seed',20260827))).encode()).hexdigest()[:12]
        carrier=hashlib.sha256((str(path)+'|'+record+'|'+provenance+'|'+str(cfg.get('blind_seed',20260827))).encode()).hexdigest()[:16]
        pair='P'+carrier[:10];probe=broadband_probe(base,tuple(cfg.get('probe_harmonics',[1,2,3,4])),offsets);ref=segment_lengths(base,offsets);dtref=float(np.min(ref));priority=bool(any(rx.search(topology) for rx in priority_rx));priority_groups.add(topology_group) if priority else None;topology_groups.add(topology_group);prov_counts[source_family]=prov_counts.get(source_family,0)+1;family_carrier_slots.add((topology,source_family))
        for arm in (-1,0,1):
            physical=arm*flip;x=base+physical*eps*probe if arm else base.copy();cid=secrets.token_hex(8);rel=f'prepared/{cid}.npz';np.savez_compressed(work/rel,x=x,x_reference=base,reference_lengths=ref,component_offsets=offsets)
            public.append({'candidate_id':cid,'pair_id':pair,'carrier_id':carrier,'topology_group_id':topology_group,'provenance_group_id':provenance_group,'probe_arm':arm,'data':rel,'dt_reference_ds':dtref,'certification_priority':priority,'n_components':int(len(offsets)-1)})
            private.append({'candidate_id':cid,'pair_id':pair,'carrier_id':carrier,'topology_group_id':topology_group,'provenance_group_id':provenance_group,'topology_id':topology,'provenance':provenance,'source_path':str(path),'source_name':source_name,'source_record_id':record,'source_scale':scale,'physical_probe_sign':physical,'certification_priority':priority,'n_components':int(len(offsets)-1),'source_metadata':metadata})
    rng.shuffle(public);(work/'blind_catalog.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in public),encoding='utf-8');priv={'secret_probe_flip':flip,'rows':private};pb=json.dumps(clean_json(priv),sort_keys=True,indent=2).encode();(work/'private/reveal_map.json').write_bytes(pb)
    s={'format':'SST-INTRINSIC-MODAL-PREPARE-2.2.6','n_carriers':len(seed_rows),'n_shape_seed_carriers':len(seed_rows),'n_source_family_carriers':len(family_carrier_slots),'carrier_definition':'source-family carrier = one selected library family per topology; shape variants remain separate internal carrier_ids','n_topology_groups':len(topology_groups),'n_pairs':len(seed_rows),'n_candidates':len(public),'n_certification_priority_topology_groups':len(priority_groups),'candidate_arms':[-1,0,1],'blind_fields_hidden':['topology_id','provenance','source_path','source_name','source_record_id','source_scale','physical_probe_sign'],'private_key_commitment_sha256':hashlib.sha256(pb).hexdigest(),'seed_source':seed_source_label,'qhp_used':False,'baseline_arm_added':True,'priority_role_visible_but_identity_hidden':True,'provenance_hidden_during_primary_scoring':True,'source_family_counts_blind':{hashlib.sha256((k+'|source-family|'+str(cfg.get('blind_seed',20260827))).encode()).hexdigest()[:12]:v for k,v in prov_counts.items()},'source_discovery':source_summary}
    (work/'prepare_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8');return s

def prepare(dataset,work,cfg):
    files=discover(dataset,cfg.get('source_regex'));files=files[:int(cfg.get('max_carriers',9999))];n=int(cfg['n_points']);seed=[]
    for path,raw in files:
        base,scale=normalize(resample_closed(raw,n));seed.append({'path':path,'source_name':path.name,'topology_id':path.stem,'provenance':'relaxed','source_record_id':path.name,'base':base,'component_offsets':np.asarray([0,n],dtype=np.int64),'scale':scale,'metadata':{}})
    return _write_prepared(work,cfg,seed,'Ridgerunner/KnotPlot relaxed centerlines')

def prepare_provenance(work,cfg,config_base=None,libraries=None,min_carriers=None,kind=None,topology=None):
    records,summary=discover_all_sources(cfg,config_base=config_base,libraries=libraries,min_carriers=min_carriers,kind=kind,topology=topology);maxc=int(cfg.get('max_carriers',9999));records=records[:maxc];n=int(cfg['n_points']);seed=[]
    for r in records:
        try: base,offsets,scale=normalize_components(r.components,n)
        except Exception: continue
        seed.append({'path':r.source_path,'source_name':r.source_name,'topology_id':r.topology_id,'provenance':r.provenance,'source_record_id':r.source_record_id,'base':base,'component_offsets':offsets,'scale':scale,'metadata':r.metadata})
    if not seed: raise RuntimeError(f'No provenance source geometries were prepared. Discovery summary: {summary}')
    return _write_prepared(work,cfg,seed,'selected library provenance geometries (Fremlin/Gilbert/Katlas/KnotPlot)',summary)

def scan_provenance(cfg,config_base=None,libraries=None,min_carriers=None,kind=None,topology=None):
    records,summary=discover_all_sources(cfg,config_base=config_base,libraries=libraries,min_carriers=min_carriers,kind=kind,topology=topology);by_top={};variant_counts={}
    fammap={'relaxed':'KnotPlot','fseries':'Fremlin','ideal':'Gilbert','ideal_links':'Gilbert','katlas':'Katlas'}
    for r in records:
        fam=fammap.get(r.provenance,r.provenance);by_top.setdefault(r.topology_id,set()).add(fam)
        variant_counts.setdefault(r.topology_id,{})[fam]=variant_counts.setdefault(r.topology_id,{}).get(fam,0)+1
    summary['matched_topologies_ge2']=sum(len(v)>=2 for v in by_top.values());summary['matched_topologies_ge3']=sum(len(v)>=3 for v in by_top.values());summary['carrier_definition']='distinct source family per topology; Fremlin variants are shape seeds, not extra carriers';summary['topology_source_counts']={k:len(v) for k,v in sorted(by_top.items())};summary['topology_carrier_counts']=dict(summary['topology_source_counts']);summary['topology_variant_counts']={k:variant_counts[k] for k in sorted(variant_counts)};return summary

def load_catalog(work): return [json.loads(x) for x in (Path(work)/'blind_catalog.jsonl').read_text().splitlines() if x.strip()]
