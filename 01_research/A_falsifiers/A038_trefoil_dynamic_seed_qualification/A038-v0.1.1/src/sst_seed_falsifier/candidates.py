from pathlib import Path
import numpy as np
from .geometry import resample_closed,normalize_length,normal_frame,min_nonlocal_vertex_distance,segment_lengths
from .io import discover_sources,geom_sha,dump_json
from .blind import make_blind_ids

def analytic_trefoil(n=256):
    t=np.linspace(0,2*np.pi,n,endpoint=False); x=np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]; return x

def generate(dataset,out,cfg):
    out=Path(out); (out/'geometries').mkdir(parents=True,exist_ok=True)
    src=discover_sources(dataset,cfg['source_regex'],cfg.get('extensions',['.txt','.xyz','.dat']))
    if not src:
        if not cfg.get('allow_analytic_fallback',False): raise RuntimeError(f'No trefoil sources matched under {dataset}; refusing silent analytic fallback')
        src=[(Path('ANALYTIC_TORUS_TREFOIL'),analytic_trefoil(max(256,int(cfg['candidate_n']))))]
    # deduplicate source shapes after common resample/normalization
    uniq=[]; seen=set()
    for p,x in src:
        y=normalize_length(resample_closed(x,int(cfg['candidate_n'])),cfg.get('target_length',2*np.pi)); h=geom_sha(y,10)
        if h not in seen: seen.add(h); uniq.append((p,y))
    rng=np.random.default_rng(int(cfg.get('candidate_seed',1729))); max_sources=int(cfg.get('max_sources',12)); uniq=uniq[:max_sources]
    rec=[]; per=int(cfg.get('variants_per_source',12)); maxc=int(cfg.get('max_candidates',128));
    for si,(p,base) in enumerate(uniq):
        # include exact normalized base
        pars=[{'xy_scale':1.0,'z_scale':1.0,'mode':0,'normal_amp':0.0,'binormal_amp':0.0,'phase':0.0}]
        for j in range(max(0,per-1)):
            pars.append({'xy_scale':float(rng.uniform(*cfg.get('xy_scale_range',[.92,1.08]))),'z_scale':float(rng.uniform(*cfg.get('z_scale_range',[.82,1.18]))),'mode':int(rng.integers(1,int(cfg.get('max_deform_mode',6))+1)),'normal_amp':float(rng.uniform(*cfg.get('normal_amp_range',[-.06,.06]))),'binormal_amp':float(rng.uniform(*cfg.get('binormal_amp_range',[-.05,.05]))),'phase':float(rng.uniform(0,2*np.pi))})
        for j,pa in enumerate(pars):
            x=base.copy(); x[:,0:2]*=pa['xy_scale']; x[:,2]*=pa['z_scale']; x=normalize_length(x,cfg.get('target_length',2*np.pi));
            if pa['mode']:
                _,n,b=normal_frame(x); s=np.arange(len(x))/len(x); f=np.cos(2*np.pi*pa['mode']*s+pa['phase'])[:,None]; x=x+pa['normal_amp']*f*n+pa['binormal_amp']*f*b; x=normalize_length(resample_closed(x,len(x)),cfg.get('target_length',2*np.pi))
            gap=min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3))); ds=float(np.mean(segment_lengths(x))); ratio=gap/max(ds,1e-15)
            if ratio<float(cfg.get('min_initial_gap_over_ds',1.35)): continue
            rec.append({'source':str(p),'source_index':si,'variant_index':j,'parameters':pa,'initial_gap_over_ds':ratio,'geom_sha':geom_sha(x),'x':x})
            if len(rec)>=maxc: break
        if len(rec)>=maxc: break
    if len(rec)<2: raise RuntimeError('Too few geometry-qualified trefoil candidates')
    pub,mapping=make_blind_ids([{k:v for k,v in r.items() if k!='x'} for r in rec],out)
    # assignment is in record order by make_blind_ids
    for r,pubrow in zip(rec,pub): np.save(out/'geometries'/f"{pubrow['candidate_id']}.npy",r['x'])
    dump_json(out/'prepare_summary.json',{'n_source_files':len(src),'n_unique_sources':len(uniq),'n_candidates':len(rec),'dataset':str(dataset),'source_identities_hidden':True,'parameter_identities_hidden':True})
    return len(rec)
