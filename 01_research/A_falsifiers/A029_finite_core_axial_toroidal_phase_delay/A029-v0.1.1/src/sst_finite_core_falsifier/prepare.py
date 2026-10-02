from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,secrets,shutil
import numpy as np
from .geometry import carrier_catalog,geometry_stats
from .model import Candidate

def _hashid(s):return hashlib.sha256(s.encode()).hexdigest()[:16]
def prepare(root,outdir,config_path):
    root=Path(root);out=Path(outdir);cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if out.exists(): shutil.rmtree(out)
    priv=out/'private';pub=out/'blind_catalog';geo=pub/'geometry';priv.mkdir(parents=True,exist_ok=True);geo.mkdir(parents=True,exist_ok=True)
    cats=carrier_catalog(root/'assets'/'fseries',int(cfg.get('carrier_n',320))); key=secrets.token_hex(16); rng=np.random.default_rng(int(cfg.get('blind_seed',20260821))); rows=[];keys=[];candidates={}
    carriers=cfg.get('carriers',list(cats));profiles=cfg.get('profiles',['gaussian']);mus=cfg.get('axial_ratios',[-1.,1.]);cores=cfg.get('core_fractions',[.06]);ms=cfg.get('m_values',[1,2]);ns=cfg.get('n_values',[1,2]);offs=cfg.get('control_offsets',[.37])
    pairnum=0
    for cid in carriers:
        ent=cats[cid]
        if ent.get('source_qualified',True) is False:continue
        gs=geometry_stats(ent['components'])
        for prof in profiles:
          for mu in mus:
           for core in cores:
            if core*gs['curvature_max']>float(cfg.get('prepare_max_core_curvature',.36)):continue
            for m in ms:
             for n in ns:
              for offmag in offs:
               sign=-1 if rng.random()<.5 else 1; off=float(sign*offmag)
               common=dict(components=ent['components'],profile_name=prof,axial_ratio=float(mu),core_fraction=float(core),m=int(m),n=int(n),radial_levels=cfg.get('radial_levels',[28,36,44]),radial_n_dispersion=int(cfg.get('radial_n_dispersion',44)),rmax=float(cfg.get('radial_rmax',5.0)),metadata={})
               ca=Candidate(closure_offset=0.0,**common); cb=Candidate(closure_offset=off,**common)
               true=[('CLOSED',ca),('SYMMETRIC_CONTROL',cb)]; rng.shuffle(true); ids=[]
               for condition,c in true:
                   token=_hashid(f'{key}|{cid}|{prof}|{mu}|{core}|{m}|{n}|{off}|{condition}'); rel=f'geometry/{token}.npz'; c.to_npz(pub/rel);candidates[token]=rel;ids.append((token,condition,rel))
               pid=f'P{pairnum:05d}';pairnum+=1; rows.append({'pair_id':pid,'candidate_a':ids[0][0],'candidate_b':ids[1][0],'geometry_a':ids[0][2],'geometry_b':ids[1][2]})
               keys.append({'pair_id':pid,'carrier_id':cid,'family':ent['family'],'profile':prof,'axial_ratio':float(mu),'core_fraction':float(core),'m':int(m),'n':int(n),'control_offset':off,'candidate_a':ids[0][0],'condition_a':ids[0][1],'candidate_b':ids[1][0],'condition_b':ids[1][1]})
    with open(pub/'pairs_public.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys() if rows else ['pair_id']);w.writeheader();w.writerows(rows)
    (priv/'pair_key.json').write_text(json.dumps(keys,indent=2,sort_keys=True)+'\n',encoding='utf-8');commit=hashlib.sha256((priv/'pair_key.json').read_bytes()).hexdigest();(out/'PREPARE_SUMMARY.json').write_text(json.dumps({'format':'SST-FINITE-CORE-PREPARE-1.1','n_pairs':len(rows),'n_candidates':len(candidates),'private_key_commitment_sha256':commit,'blind_fields_hidden':['carrier_id','family','condition','profile','axial_ratio','core_fraction','m','n','control_offset']},indent=2)+'\n',encoding='utf-8');return json.loads((out/'PREPARE_SUMMARY.json').read_text())
