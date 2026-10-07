from __future__ import annotations
from pathlib import Path
import hashlib, json, random, re, secrets
import numpy as np

from .geometry import (
    resample_closed_curve, normalize_total_length, save_components_npz,
    geometry_sha256, pairwise_link_matrix,
)
from .composite import loose_components, decorate_skeleton
from .seal import sha256_file

KNOTS = ['3_1','4_1','5_1','5_2','6_1','6_2','6_3','7_1','7_2','7_3','7_4','7_5','7_6','7_7']
SKELETONS = {
    'S631': {'file':'6_3_1__knotplot_final.txt','label':'6^3_1','topology':'L6a5'},
    'S632': {'file':'6_3_2__knotplot_final.txt','label':'6^3_2','topology':'L6a4_Borromean'},
    'S633': {'file':'6_3_3__knotplot_final.txt','label':'6^3_3','topology':'L6n1'},
    'T33':  {'file':'T_3_3__knotplot_final.txt','label':'T(3,3)','topology':'L6n1'},
}
DIRECT_LINKS = {
    'D631':  {'file':'6_3_1__knotplot_final.txt','label':'6^3_1','topology':'L6a5'},
    'D632':  {'file':'6_3_2__knotplot_final.txt','label':'6^3_2','topology':'L6a4_Borromean'},
    'D633':  {'file':'6_3_3__knotplot_final.txt','label':'6^3_3','topology':'L6n1'},
    'DT33':  {'file':'T_3_3__knotplot_final.txt','label':'T(3,3)','topology':'L6n1'},
    'DT69':  {'file':'T_6_9__knotplot_final.txt','label':'T(6,9)','topology':'3_component_torus'},
    'DT615': {'file':'T_6_15__knotplot_final.txt','label':'T(6,15)','topology':'3_component_torus'},
    'DT621': {'file':'T_6_21__knotplot_final.txt','label':'T(6,21)','topology':'3_component_torus'},
}
MIXED = ['001','010','100','011','101','110']  # 0=5_2, 1=6_1


def _anon(salt,label):
    return 'CAND_'+hashlib.sha256((salt+'|'+label).encode()).hexdigest()[:16]


def _read_xyz_components(path:Path):
    raw=path.read_text(encoding='utf-8',errors='strict').replace('\r\n','\n').strip()
    chunks=[c.strip() for c in re.split(r'\n\s*\n',raw) if c.strip()]
    out=[]
    for c in chunks:
        arr=np.loadtxt(c.splitlines(),dtype=float)
        arr=np.asarray(arr,float)
        if arr.ndim==1: arr=arr[None,:]
        if arr.shape[1]!=3 or len(arr)<8: raise ValueError(f'invalid xyz component in {path}')
        out.append(arr)
    if not out: raise ValueError(f'no xyz components in {path}')
    return out


def _knot_file(data_root:Path,k):
    kp=data_root/'knots'/f'{k}__knotplot_final.txt'
    if kp.exists(): return kp,'knotplot_final'
    gb=data_root/'knots'/f'{k}__gilbert_Ideal_record.txt'
    if gb.exists(): return gb,'gilbert_Ideal_fallback'
    raise FileNotFoundError(k)


def _load_knots(data_root:Path,n):
    out={}; provenance={}
    for k in KNOTS:
        p,provider=_knot_file(data_root,k)
        comps=_read_xyz_components(p)
        if len(comps)!=1: raise ValueError(f'{k} source is not single-component')
        curve=resample_closed_curve(comps[0],max(n,192))
        out[k]=curve
        provenance[k]={'provider':provider,'file':p.name,'sha256':sha256_file(p)}
    return out,provenance


def _load_link(path:Path,n):
    comps=_read_xyz_components(path)
    if len(comps)!=3: raise ValueError(f'{path.name}: expected 3 components, got {len(comps)}')
    return normalize_total_length([resample_closed_curve(c,n) for c in comps])


def _source_snapshot(data_root:Path):
    rows=[]
    for p in sorted(data_root.rglob('*.txt')):
        rows.append({'relative_path':str(p.relative_to(data_root)).replace('\\','/'),'sha256':sha256_file(p),'bytes':p.stat().st_size})
    return rows


def prepare_discovery(output_dir:Path, package_root:Path, n=144):
    output_dir=Path(output_dir); package_root=Path(package_root)
    output_dir.mkdir(parents=True,exist_ok=True); pub=output_dir/'blind_inputs'; priv=output_dir/'_private'; pub.mkdir(exist_ok=True); priv.mkdir(exist_ok=True)
    data_root=package_root/'data'/'source_native'
    knots,kprov=_load_knots(data_root,n)
    skeletons={code:_load_link(data_root/'links'/meta['file'],n) for code,meta in SKELETONS.items()}
    direct={code:_load_link(data_root/'links'/meta['file'],n) for code,meta in DIRECT_LINKS.items()}

    geoms={}; meta={}; failures={}
    # A. homogeneous low-crossing knot controls and linked embeddings
    for k in KNOTS:
        key=f'HOM@@U@@{k}'
        geoms[key]=loose_components([knots[k]]*3,n=n)
        meta[key]={'semantic_kind':'unlinked_homogeneous','architecture_code':'U','component_knots':[k,k,k],'component_provider':kprov[k]}
        for scode in SKELETONS:
            key=f'HOM@@{scode}@@{k}'
            try:
                comps,cert=decorate_skeleton(skeletons[scode],[knots[k]]*3,n=n)
                geoms[key]=comps
                meta[key]={'semantic_kind':'homogeneous_decorated','architecture_code':scode,'component_knots':[k,k,k],
                           'component_provider':kprov[k],'construction_certificate':cert,'skeleton':SKELETONS[scode]}
            except Exception as e:
                failures[key]=f'{type(e).__name__}: {e}'

    # B. historical 5_2/6_1 mixed controls, all permutations, linked skeletons only.
    for bits in MIXED:
        labels=['6_1' if b=='1' else '5_2' for b in bits]
        for scode in SKELETONS:
            key=f'MIX@@{scode}@@{bits}'
            try:
                comps,cert=decorate_skeleton(skeletons[scode],[knots[x] for x in labels],n=n)
                geoms[key]=comps
                meta[key]={'semantic_kind':'historical_mixed_control','architecture_code':scode,'component_knots':labels,
                           'mixed_bits':bits,'construction_certificate':cert,'skeleton':SKELETONS[scode]}
            except Exception as e:
                failures[key]=f'{type(e).__name__}: {e}'

    # C. direct source-native 3-component links.
    for code,comps in direct.items():
        key=f'DIRECT@@{code}'
        p=data_root/'links'/DIRECT_LINKS[code]['file']
        geoms[key]=comps
        meta[key]={'semantic_kind':'source_native_link','architecture_code':code,'component_knots':None,
                   'direct_link':DIRECT_LINKS[code], 'source_file':p.name,'source_sha256':sha256_file(p)}

    expected = len(KNOTS)*(1+len(SKELETONS)) + len(MIXED)*len(SKELETONS) + len(DIRECT_LINKS)
    scientific_ready=(len(geoms)==expected and not failures)
    salt=secrets.token_hex(32); labels=list(geoms); random.SystemRandom().shuffle(labels)
    mapping={}; manifest=[]
    for key in labels:
        comps=geoms[key]; aid=_anon(salt,key); path=pub/f'{aid}.npz'; save_components_npz(path,comps)
        mm=dict(meta[key]); mm.update({'case_key':key,'geometry_sha256':geometry_sha256(comps),
                                      'private_pairwise_link_matrix':pairwise_link_matrix(comps).tolist()})
        mapping[aid]=mm
        manifest.append({'anonymous_id':aid,'file':path.name,'sha256':sha256_file(path),'geometry_sha256':geometry_sha256(comps),'component_count':3})
    private={'schema':'A054-PRIVATE-MAPPING-3.0','version':'0.3.0','salt':salt,'mapping':mapping,'failures':failures,
             'knot_candidates':KNOTS,'skeleton_codes':list(SKELETONS),'direct_link_codes':list(DIRECT_LINKS),
             'source_snapshot':_source_snapshot(data_root),'expected_case_count':expected}
    pp=priv/'PRIVATE_MAPPING.json'; pp.write_text(json.dumps(private,indent=2)+'\n')
    public={'schema':'A054-BLIND-MANIFEST-3.0','version':'0.3.0','scientific_ready':scientific_ready,'candidate_count':len(manifest),
            'expected_case_count':expected,'candidates':manifest,'private_mapping_sha256':sha256_file(pp),'semantic_identity_fields_excluded':True,
            'circulation_sectors':[f'Q{i}' for i in range(8)],
            'design_public':{'candidate_knot_level_count':len(KNOTS),'source_skeleton_level_count':len(SKELETONS),'direct_link_count':len(DIRECT_LINKS),
                             'historical_mixed_control_count':len(MIXED)*len(SKELETONS),
                             'note':'No knot/link identity is exposed to blind evaluation; no mass, charge or particle label is encoded.'}}
    (output_dir/'BLIND_MANIFEST.json').write_text(json.dumps(public,indent=2)+'\n')
    (output_dir/'PREPARE_STATUS.json').write_text(json.dumps({'status':'PREPARED_FULL' if scientific_ready else 'PREPARED_PARTIAL_FAIL_CLOSED',
                                                              'candidate_count':len(manifest),'expected_case_count':expected,'failure_count':len(failures)},indent=2)+'\n')
    return public
