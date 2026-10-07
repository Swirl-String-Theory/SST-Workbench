from __future__ import annotations
from pathlib import Path
import json,secrets,hashlib,random,itertools
from .prepare import _skeletons,_build_factor_geometry,_anon,_component_labels,_composition_class,ARCHITECTURES
from .pklsa import write_upstream_plan,audit_required_topologies,materialize_anchor_geometry
from .geometry import save_components_npz,geometry_sha256,pairwise_link_matrix
from .seal import sha256_file

MIXED_BITS=['001','010','100','011','101','110']


def _same_provider_strata(strata):
    x=[s for s in strata if s['5_2']['provider_group']==s['6_1']['provider_group']]
    return x if x else strata[:min(2,len(strata))]


def prepare_certification(output_dir:Path,workbench:Path,n=128,preset='basic'):
    output_dir.mkdir(parents=True,exist_ok=True); pub=output_dir/'blind_inputs'; priv=output_dir/'_private'; pub.mkdir(exist_ok=True); priv.mkdir(exist_ok=True)
    write_upstream_plan(workbench,output_dir/'UPSTREAM_PLAN.json')
    if not workbench or not workbench.exists(): raise RuntimeError('v0.2.0 certification requires the local Workbench PKLSA/E011 sources')
    aud=audit_required_topologies(workbench); loaded={}
    for top in ('5_2','6_1'):
        loaded[top]=[]
        for a in sorted(aud[top]['anchors'],key=lambda z:(z.get('provider_group',''),z.get('static_seed_id',''))):
            loaded[top].append({'provider_group':a.get('provider_group'),'seed_id':a.get('static_seed_id'),'curve':materialize_anchor_geometry(a,workbench,n)})
    strata=[]
    for idx,(a52,a61) in enumerate(itertools.product(loaded['5_2'],loaded['6_1'])):
        strata.append({'stratum_id':f'S{idx:02d}','5_2':a52,'6_1':a61})
    if preset=='basic': use=_same_provider_strata(strata); linked_arches=['G','B']; u_bits=['001','011']
    elif preset=='extended': use=strata; linked_arches=['G','B']; u_bits=['001','011']
    elif preset=='full': use=strata; linked_arches=['G','B']; u_bits=MIXED_BITS
    else: raise ValueError(preset)
    skeletons=_skeletons(n); geoms={}; meta={}
    for st in use:
        cases=[(code,bits) for code in linked_arches for bits in MIXED_BITS] + [('U',bits) for bits in u_bits]
        for code,bits in cases:
                key=f'C2@@{code}@@{bits}@@{st["stratum_id"]}'
                comps,cert=_build_factor_geometry(code,bits,st['5_2']['curve'],st['6_1']['curve'],skeletons,n)
                geoms[key]=comps; meta[key]={'semantic_kind':'certification_cell','architecture_code':code,'twist_bits':bits,
                    'components':_component_labels(bits),'provider_stratum':{'stratum_id':st['stratum_id'],
                    '5_2':{'provider_group':st['5_2']['provider_group'],'static_seed_id':st['5_2']['seed_id']},
                    '6_1':{'provider_group':st['6_1']['provider_group'],'static_seed_id':st['6_1']['seed_id']}},
                    'construction_certificate':cert,**_composition_class(bits)}
    salt=secrets.token_hex(32); labels=list(geoms); random.SystemRandom().shuffle(labels); mapping={}; manifest=[]
    for key in labels:
        aid=_anon(salt,key); comps=geoms[key]; path=pub/f'{aid}.npz'; save_components_npz(path,comps); m=meta[key]
        m=m|{'case_key':key,'geometry_sha256':geometry_sha256(comps),'private_pairwise_link_matrix':pairwise_link_matrix(comps).tolist(),**ARCHITECTURES[m['architecture_code']]}
        mapping[aid]=m; manifest.append({'anonymous_id':aid,'file':path.name,'sha256':sha256_file(path),'geometry_sha256':geometry_sha256(comps),'component_count':3})
    private={'schema':'A054-CERT-PRIVATE-MAPPING-2.0','salt':salt,'mapping':mapping,'preset':preset}
    pp=priv/'PRIVATE_MAPPING.json'; pp.write_text(json.dumps(private,indent=2)+'\n')
    out={'schema':'A054-CERT-BLIND-MANIFEST-2.0','version':'0.2.0','preset':preset,'scientific_ready':True,'candidate_count':len(manifest),
         'candidates':manifest,'private_mapping_sha256':sha256_file(pp),
         'selection_preregistration':'BASIC/EXTENDED certify all mixed 5_2/6_1 assignments in both linked skeletons; BASIC uses same-provider strata, EXTENDED all provider pairs. U controls use canonical 001 and 011 in BASIC/EXTENDED. FULL includes all three architectures and all mixed assignments.',
         'v011_evidence_freeze':'v0.1.1 established architecture dominance and a small G-specific preference for opposing 6_1; v0.2.0 does not tune gates to those effect sizes.'}
    (output_dir/'BLIND_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n')
    (output_dir/'PREPARE_STATUS.json').write_text(json.dumps({'status':'PREPARED_FULL','candidate_count':len(manifest),'preset':preset},indent=2)+'\n')
    return out
