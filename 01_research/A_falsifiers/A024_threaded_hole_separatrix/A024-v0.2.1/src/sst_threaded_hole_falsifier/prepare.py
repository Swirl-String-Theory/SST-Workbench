from __future__ import annotations
from pathlib import Path
import csv,hashlib,json,secrets,shutil
import numpy as np
from .generators import carrier_catalog,make_thread_bundle,combine
from .topology import thread_link_matrix
from .geometry import min_nonlocal_segment_distance_exact
from .native import min_nonlocal_segment_distance as native_min_nonlocal_segment_distance, HAVE_NATIVE


def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prereg_gap(cs,adjacency=3):
    if HAVE_NATIVE:return native_min_nonlocal_segment_distance(cs.points,cs.offsets,int(adjacency))
    return min_nonlocal_segment_distance_exact(cs,int(adjacency))

def _commit(paths):
    h=hashlib.sha256()
    for p in sorted(paths,key=lambda x:Path(x).name):h.update(Path(p).name.encode());h.update(b'\0');h.update(Path(p).read_bytes());h.update(b'\0')
    return h.hexdigest()


def prepare(project_root,outdir,config_path):
    root=Path(project_root);out=Path(outdir);pub=out/'blind_catalog';priv=out/'private'
    for d in (pub,priv):
        if d.exists():shutil.rmtree(d)
    (pub/'geometry').mkdir(parents=True,exist_ok=True);priv.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'));nC=int(cfg['carrier_n']);nT=int(cfg['thread_n']);core=float(cfg['core']);adj=int(cfg.get('contact_adjacency',3));min_gap_core=float(cfg.get('min_initial_gap_core',2.5));coupling_mode=str(cfg.get('thread_coupling_mode','total_beta'))
    if coupling_mode not in ('total_beta','per_thread_beta'):raise ValueError('thread_coupling_mode must be total_beta or per_thread_beta')
    cats=carrier_catalog(root/'assets/fseries',nC);requested=cfg.get('carrier_ids',list(cats));missing=[x for x in requested if x not in cats]
    if missing:raise KeyError(f'Unknown carrier ids: {missing}')
    rng=np.random.default_rng(int(cfg.get('prepare_seed',271828)));pcands=[];ppairs=[];pubpairs=[];cache={}

    def thread_gamma(gamma_core,beta,nthreads,condition):
        if condition=='null':return 0.0
        return float(beta)*float(gamma_core)/max(int(nthreads),1) if coupling_mode=='total_beta' else float(beta)*float(gamma_core)

    def save_candidate(carrier_id,carrier,threads,nc,gamma_core,beta,nthreads,helix,condition,meta):
        key=(carrier_id,gamma_core,beta,nthreads,helix,condition,coupling_mode)
        if key in cache:return cache[key]
        cs=combine(carrier,threads);tgamma=thread_gamma(gamma_core,beta,nthreads,condition);beta_total=float(nthreads*tgamma/max(abs(gamma_core),1e-30))
        gammas=np.r_[np.full(nc,gamma_core),np.full(nthreads,tgamma)]
        cid='CAND_'+secrets.token_hex(8).upper();rel=f'geometry/{cid}.npz';np.savez_compressed(pub/rel,points=cs.points,offsets=cs.offsets,gammas=gammas,n_carrier_components=np.int64(nc))
        pcands.append({'candidate_id':cid,'carrier_id':carrier_id,'family':meta['family'],'source':meta.get('source',''),'source_qualified':meta.get('source_qualified',True),'condition':condition,'gamma_core':gamma_core,'beta_parameter':beta if condition=='active' else 0.0,'beta_total_thread_over_core':beta_total,'thread_coupling_mode':coupling_mode,'n_threads':nthreads,'helix_turns':helix,'thread_gamma_each':tgamma,'hole_clearance':meta['hole_clearance'],'combined_initial_gap_core':meta['combined_initial_gap_core'],'carrier_self_gap_core':meta['carrier_self_gap_core'],'bundle_radius':meta['bundle_radius'],'thread_density_proxy':nthreads/(np.pi*max(meta['hole_clearance'],1e-6)**2),'link_matrix_json':json.dumps(meta['link_matrix'])})
        cache[key]=(cid,rel);return cid,rel

    qualification=[];pair_specs=cfg.get('pair_specs')
    if pair_specs:
        requested=sorted(set(str(x['carrier_id']) for x in pair_specs))
        missing=[x for x in requested if x not in cats]
        if missing:raise KeyError(f'Unknown carrier ids in pair_specs: {missing}')
    for carrier_id in requested:
        ent=cats[carrier_id];carrier=ent['geometry'];nc=carrier.n_components;carrier_gap=prereg_gap(carrier,adj)/core
        if not ent.get('source_qualified',True):
            qualification.append({'carrier_id':carrier_id,'carrier_self_gap_core':carrier_gap,'status':'EXCLUDED_SOURCE_PROVENANCE'});continue
        if carrier_gap<=min_gap_core:
            qualification.append({'carrier_id':carrier_id,'carrier_self_gap_core':carrier_gap,'status':'FAIL_CARRIER_INITIAL_CLEARANCE'});continue
        specs=[x for x in (pair_specs or []) if str(x.get('carrier_id'))==carrier_id]
        combos=sorted(set((int(x.get('n_threads',3)),float(x.get('helix_turns',1.0))) for x in specs)) if specs else [(int(n),float(h)) for n in cfg.get('n_threads_values',[3]) for h in cfg.get('helix_turns_values',[1.0])]
        for nthreads,helix in combos:
            threads,tmeta=make_thread_bundle(carrier,int(nthreads),float(helix),nT,ent.get('hole_axis',(0,0,1)),core);lm=thread_link_matrix(carrier,threads);link_score=float(np.max(np.abs(lm))) if lm else 0.0;clearance=tmeta['hole_clearance'];combined=combine(carrier,threads);combined_gap=prereg_gap(combined,adj)/core
            if clearance<=float(cfg.get('min_hole_clearance_core',2.4))*core:qstatus='FAIL_HOLE_CLEARANCE'
            elif link_score<float(cfg.get('min_thread_gauss_link',.75)):qstatus='FAIL_THREAD_LINK'
            elif combined_gap<=min_gap_core:qstatus='FAIL_COMBINED_INITIAL_CLEARANCE'
            else:qstatus='PASS'
            qualification.append({'carrier_id':carrier_id,'n_threads':nthreads,'helix_turns':helix,'hole_clearance':clearance,'carrier_self_gap_core':carrier_gap,'combined_initial_gap_core':combined_gap,'max_abs_gauss_link':link_score,'status':qstatus})
            if qstatus!='PASS':continue
            meta={**ent,**tmeta,'link_matrix':lm,'combined_initial_gap_core':combined_gap,'carrier_self_gap_core':carrier_gap}
            local_specs=[x for x in specs if int(x.get('n_threads',3))==nthreads and float(x.get('helix_turns',1.0))==helix] if specs else None
            if local_specs:
                grouped={}
                for x in local_specs:grouped.setdefault(float(x.get('gamma_core',1.0)),[]).append(float(x['beta']))
                gamma_beta=sorted(grouped.items())
            else:gamma_beta=[(float(g),[float(b) for b in cfg.get('beta_values',[-.75,.75])]) for g in cfg.get('gamma_core_values',[1.0])]
            for gamma_core,betas in gamma_beta:
                c0,f0=save_candidate(carrier_id,carrier,threads,nc,float(gamma_core),0.0,int(nthreads),float(helix),'null',meta)
                for beta in betas:
                    if abs(float(beta))<1e-15:continue
                    ca,fa=save_candidate(carrier_id,carrier,threads,nc,float(gamma_core),float(beta),int(nthreads),float(helix),'active',meta);pair='PAIR_'+secrets.token_hex(6).upper();arr=[(c0,f0),(ca,fa)];rng.shuffle(arr)
                    pubpairs.append({'pair_id':pair,'candidate_a':arr[0][0],'geometry_a':arr[0][1],'candidate_b':arr[1][0],'geometry_b':arr[1][1]})
                    beta_total=float(int(nthreads)*thread_gamma(float(gamma_core),float(beta),int(nthreads),'active')/max(abs(float(gamma_core)),1e-30))
                    ppairs.append({'pair_id':pair,'carrier_id':carrier_id,'family':ent['family'],'candidate_null':c0,'candidate_active':ca,'beta_parameter':float(beta),'beta_total_thread_over_core':beta_total,'thread_coupling_mode':coupling_mode,'gamma_core':float(gamma_core),'n_threads':int(nthreads),'helix_turns':float(helix),'campaign_role':str(cfg.get('campaign_role','general'))})
    if not pubpairs:raise RuntimeError('No qualified blind pairs produced; inspect private/qualification.csv by running a looser diagnostic config only if preregistered')
    rng.shuffle(pubpairs)
    with open(pub/'pairs_public.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['pair_id','candidate_a','geometry_a','candidate_b','geometry_b']);w.writeheader();w.writerows(pubpairs)
    with open(priv/'candidate_key.csv','w',newline='',encoding='utf-8') as f:fields=list(pcands[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(pcands)
    with open(priv/'pair_key.csv','w',newline='',encoding='utf-8') as f:fields=list(ppairs[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(ppairs)
    with open(priv/'qualification.csv','w',newline='',encoding='utf-8') as f:fields=sorted({k for r in qualification for k in r});w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(qualification)
    commitment=_commit([priv/'candidate_key.csv',priv/'pair_key.csv',priv/'qualification.csv'])
    manifest={'campaign_format':'SST-THREADED-HOLE-BLIND-2.1','n_pairs':len(pubpairs),'n_candidates':len(pcands),'private_key_commitment_sha256':commitment,'public_pair_sha256':sha256_file(pub/'pairs_public.csv'),'blind_fields_hidden':['carrier_id','family','condition','beta_parameter','beta_total_thread_over_core','thread_density_proxy','source','link_matrix'],'null_semantics':'same qualified carrier and same closed thread geometry, but thread circulation exactly zero','active_semantics':'same geometry, nonzero thread circulation; sign and strength hidden until reveal','strict_initial_clearance_core':min_gap_core,'thread_coupling_mode':coupling_mode,'campaign_role':str(cfg.get('campaign_role','general')),'gravity_note':'Pressure metrics and free exponent fits are anonymous. No Newton exponent enters field evolution or blind scoring.'}
    (pub/'manifest_public.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8');return manifest
