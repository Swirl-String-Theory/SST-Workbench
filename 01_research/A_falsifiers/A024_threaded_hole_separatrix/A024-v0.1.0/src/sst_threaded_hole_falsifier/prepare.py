from __future__ import annotations
from pathlib import Path
import csv,hashlib,json,secrets
import numpy as np
from .generators import carrier_catalog,make_thread_bundle,combine,hole_clearance
from .topology import thread_link_matrix

def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _commit(paths):
    h=hashlib.sha256()
    for p in sorted(paths,key=lambda x:Path(x).name):h.update(Path(p).name.encode());h.update(b'\0');h.update(Path(p).read_bytes());h.update(b'\0')
    return h.hexdigest()

def prepare(project_root,outdir,config_path):
    root=Path(project_root);out=Path(outdir);pub=out/'blind_catalog';priv=out/'private'
    import shutil
    for d in (pub,priv):
        if d.exists():shutil.rmtree(d)
    (pub/'geometry').mkdir(parents=True,exist_ok=True);priv.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'));nC=int(cfg['carrier_n']);nT=int(cfg['thread_n']);core=float(cfg['core'])
    cats=carrier_catalog(root/'assets/fseries',nC);requested=cfg.get('carrier_ids',list(cats));missing=[x for x in requested if x not in cats]
    if missing:raise KeyError(f'Unknown carrier ids: {missing}')
    rng=np.random.default_rng(int(cfg.get('prepare_seed',271828)));pcands=[];ppairs=[];pubpairs=[];cache={}
    def save_candidate(carrier_id,carrier,threads,nc,gamma_core,beta,nthreads,helix,condition,meta):
        key=(carrier_id,gamma_core,beta,nthreads,helix,condition)
        if key in cache:return cache[key]
        cs=combine(carrier,threads);tgamma=0.0 if condition=='null' else beta*gamma_core/max(nthreads,1);gammas=np.r_[np.full(nc,gamma_core),np.full(nthreads,tgamma)]
        cid='CAND_'+secrets.token_hex(8).upper();rel=f'geometry/{cid}.npz';np.savez_compressed(pub/rel,points=cs.points,offsets=cs.offsets,gammas=gammas,n_carrier_components=np.int64(nc))
        pcands.append({'candidate_id':cid,'carrier_id':carrier_id,'family':meta['family'],'source':meta.get('source',''),'source_qualified':meta.get('source_qualified',True),'condition':condition,'gamma_core':gamma_core,'beta_total_thread_over_core':beta if condition=='active' else 0.0,'n_threads':nthreads,'helix_turns':helix,'thread_gamma_each':tgamma,'hole_clearance':meta['hole_clearance'],'bundle_radius':meta['bundle_radius'],'thread_density_proxy':nthreads/(np.pi*max(meta['hole_clearance'],1e-6)**2),'link_matrix_json':json.dumps(meta['link_matrix'])})
        cache[key]=(cid,rel);return cid,rel
    qualification=[]
    for carrier_id in requested:
        ent=cats[carrier_id]
        if not ent.get('source_qualified',True):
            qualification.append({'carrier_id':carrier_id,'status':'EXCLUDED_SOURCE_PROVENANCE'});continue
        carrier=ent['geometry'];nc=carrier.n_components
        for nthreads in cfg.get('n_threads_values',[3]):
            for helix in cfg.get('helix_turns_values',[1.0]):
                threads,tmeta=make_thread_bundle(carrier,int(nthreads),float(helix),nT,ent.get('hole_axis',(0,0,1)),core)
                lm=thread_link_matrix(carrier,threads);link_score=float(np.max(np.abs(lm))) if lm else 0.0
                clearance=tmeta['hole_clearance']
                qstatus=('FAIL_CLEARANCE' if clearance<=float(cfg.get('min_hole_clearance_core',2.4))*core else ('FAIL_THREAD_LINK' if link_score<0.75 else 'PASS'))
                qualification.append({'carrier_id':carrier_id,'n_threads':nthreads,'helix_turns':helix,'hole_clearance':clearance,'max_abs_gauss_link':link_score,'status':qstatus})
                if qstatus!='PASS':continue
                meta={**ent,**tmeta,'link_matrix':lm}
                for gamma_core in cfg.get('gamma_core_values',[1.0]):
                    c0,f0=save_candidate(carrier_id,carrier,threads,nc,float(gamma_core),0.0,int(nthreads),float(helix),'null',meta)
                    for beta in cfg.get('beta_values',[-.75,.75]):
                        if abs(float(beta))<1e-15:continue
                        ca,fa=save_candidate(carrier_id,carrier,threads,nc,float(gamma_core),float(beta),int(nthreads),float(helix),'active',meta)
                        pair='PAIR_'+secrets.token_hex(6).upper();arr=[(c0,f0),(ca,fa)];rng.shuffle(arr)
                        pubpairs.append({'pair_id':pair,'candidate_a':arr[0][0],'geometry_a':arr[0][1],'candidate_b':arr[1][0],'geometry_b':arr[1][1]})
                        ppairs.append({'pair_id':pair,'carrier_id':carrier_id,'family':ent['family'],'candidate_null':c0,'candidate_active':ca,'beta':float(beta),'gamma_core':float(gamma_core),'n_threads':int(nthreads),'helix_turns':float(helix)})
    if not pubpairs:raise RuntimeError('No qualified blind pairs produced')
    rng.shuffle(pubpairs)
    with open(pub/'pairs_public.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['pair_id','candidate_a','geometry_a','candidate_b','geometry_b']);w.writeheader();w.writerows(pubpairs)
    with open(priv/'candidate_key.csv','w',newline='',encoding='utf-8') as f:
        fields=list(pcands[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(pcands)
    with open(priv/'pair_key.csv','w',newline='',encoding='utf-8') as f:
        fields=list(ppairs[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(ppairs)
    with open(priv/'qualification.csv','w',newline='',encoding='utf-8') as f:
        fields=sorted({k for r in qualification for k in r});w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(qualification)
    commitment=_commit([priv/'candidate_key.csv',priv/'pair_key.csv',priv/'qualification.csv'])
    manifest={'campaign_format':'SST-THREADED-HOLE-BLIND-1','n_pairs':len(pubpairs),'n_candidates':len(pcands),'private_key_commitment_sha256':commitment,'public_pair_sha256':sha256_file(pub/'pairs_public.csv'),'blind_fields_hidden':['carrier_id','family','condition','beta','thread_density_proxy','source','link_matrix'],'null_semantics':'same carrier and same closed thread geometry, but thread circulation exactly zero','active_semantics':'same geometry, nonzero thread circulation; sign and strength hidden until reveal','gravity_note':'Pressure-Poisson metrics are scored separately from self-confinement; no 1/r target enters the dynamics.'}
    (pub/'manifest_public.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return manifest
