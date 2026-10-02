from __future__ import annotations
from pathlib import Path
import csv,hashlib,json,secrets
import numpy as np
from .loaders import parse_ideal_txt,parse_js_catalog,parse_fseries,parse_xyz,normalize_topology,topology_from_relaxed_filename
from .model import CurveSet
from .geometry import resample_closed,canonicalize,canonical_phase_orientation

TORUS_PRIMARY={'3_1','5_1','7_1','8_19','9_1','10_124'}

def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha256_bytes(b):return hashlib.sha256(b).hexdigest()

def discover_source_paths(base,ideal=None,ideal_js=None,fseries_root=None,relaxed_root=None):
    b=Path(base).resolve()
    def first(paths):
        for p in paths:
            if p and Path(p).exists():return str(Path(p).resolve())
        return None
    ideal=first([ideal,b/'SSTcore/resources/ideal.txt',b/'KnotPlot/ideal.txt',b/'VortexLab/ideal.txt',b/'ideal.txt'])
    ideal_js=first([ideal_js,b/'SSTcore/resources/ideal_knots_data.js',b/'VortexLab/ideal_knots_data.js',b/'ideal_knots_data.js'])
    fseries_root=first([fseries_root,b/'KnotPlot/Knots_FourierSeries',b/'SSTcore/resources/Knots_FourierSeries',b/'Knots_FourierSeries'])
    relaxed_root=first([relaxed_root,b/'KnotPlot/knots/final',b/'KnotPlot/knots'])
    return {'ideal':ideal,'ideal_js':ideal_js,'fseries_root':fseries_root,'relaxed_root':relaxed_root}

def load_ideal(path=None,js=None,n=1024):
    if js and Path(js).exists():return parse_js_catalog(js,'IDEAL_KNOT_DB',n),str(js)
    if path and Path(path).exists():return parse_ideal_txt(path,n),str(path)
    return [],None

def load_fseries(root,n=1024,include_variants=False):
    root=Path(root);entries=[]
    js=next(iter(root.rglob('fourier_knots_data.js')),None) if root.is_dir() else None
    if js:
        try:return parse_js_catalog(js,'FSERIES_KNOT_DB',n),str(js)
        except Exception:pass
    for p in sorted(root.rglob('*.fseries')):
        try:
            e=parse_fseries(p,n,harmonic_start=1);e['source_path']=str(p)
            if include_variants or e['variant']=='canonical':entries.append(e)
        except Exception:continue
    return entries,str(root)

def load_relaxed(root,n=1024):
    out=[]
    if not root or not Path(root).exists():return out,None
    for p in sorted(Path(root).glob('*.txt')):
        if not p.name.lower().endswith('_final.txt'):continue
        try:
            comps=parse_xyz(p);top=topology_from_relaxed_filename(p)
            out.append({'topology':normalize_topology(top),'variant':'final','components':comps,'source_path':str(p),'meta':{'loader':'coordinate-final'}})
        except Exception:continue
    return out,str(root)

def _index(entries):
    d={}
    for e in entries:
        d.setdefault(normalize_topology(e['topology']),[]).append(e)
    return d

def _choose_canonical(lst):
    if not lst:return None
    can=[e for e in lst if e.get('variant')=='canonical']
    return (can or lst)[0]

def _make_geom(entry,n):
    comps=[resample_closed(c,n) for c in entry['components']]
    cs,_=canonicalize(CurveSet.from_components(comps),1.0)
    comps=[resample_closed(canonical_phase_orientation(c),n) for c in cs.components()]
    return CurveSet.from_components(comps)

def _private_commitment(paths):
    h=hashlib.sha256()
    for p in sorted(paths,key=lambda x:Path(x).name):
        h.update(Path(p).name.encode());h.update(b'\0');h.update(Path(p).read_bytes());h.update(b'\0')
    return h.hexdigest()

def prepare(outdir,base='.',ideal=None,ideal_js=None,fseries_root=None,relaxed_root=None,mode='torus',n=192,seed=1729,include_variants=False,include_relaxed_control=False):
    out=Path(outdir);public=out/'blind_catalog';private=out/'private';
    if public.exists():
        import shutil;shutil.rmtree(public)
    if private.exists():
        import shutil;shutil.rmtree(private)
    (public/'geometry').mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
    paths=discover_source_paths(base,ideal,ideal_js,fseries_root,relaxed_root)
    ideals,ideal_src=load_ideal(paths['ideal'],paths['ideal_js'],max(n,512))
    if not ideals:
        raise FileNotFoundError('No ideal source found. Set SST_FVI_IDEAL or SST_FVI_IDEAL_JS, or place ideal.txt/ideal_knots_data.js in a known Workbench location.')
    if not paths['fseries_root']:
        raise FileNotFoundError('No Fremlin Knots_FourierSeries root found. Set SST_FVI_FSERIES.')
    fseries,fs_src=load_fseries(paths['fseries_root'],max(n,512),include_variants)
    if not fseries:raise RuntimeError('No usable .fseries curves found')
    relaxed,rel_src=load_relaxed(paths['relaxed_root'],max(n,512)) if include_relaxed_control else ([],None)
    I,F,R=_index(ideals),_index(fseries),_index(relaxed)
    common=sorted(set(I)&set(F))
    if mode=='torus':common=[t for t in common if t in TORUS_PRIMARY]
    if not common:raise RuntimeError(f'No common topology IDs between ideal and fseries. ideal={len(I)} fseries={len(F)}')
    rng=np.random.default_rng(seed);pub_pairs=[];priv_cands=[];priv_pairs=[]
    def candidate(entry,family,topology):
        cs=_make_geom(entry,n);cid='CAND_'+secrets.token_hex(8).upper();fn=f'geometry/{cid}.npz';np.savez_compressed(public/fn,points=cs.points,offsets=cs.offsets)
        sp=entry.get('source_path') or (ideal_src if family=='ideal' else fs_src if family=='fseries' else rel_src) or ''
        sh=sha256_file(sp) if sp and Path(sp).is_file() else sha256_bytes(str(sp).encode())
        priv_cands.append({'candidate_id':cid,'source_family':family,'topology':topology,'variant':entry.get('variant',''),'source_path':sp,'source_sha256':sh})
        return cid,fn,cs.n_components
    for top in common:
        eI=_choose_canonical(I[top]);eF=_choose_canonical(F[top])
        cI,fI,ncI=candidate(eI,'ideal',top);cF,fF,ncF=candidate(eF,'fseries',top)
        if ncI!=ncF:continue
        pair='PAIR_'+secrets.token_hex(6).upper();arr=[(cI,fI),(cF,fF)];rng.shuffle(arr)
        pub_pairs.append({'pair_id':pair,'candidate_a':arr[0][0],'geometry_a':arr[0][1],'candidate_b':arr[1][0],'geometry_b':arr[1][1],'n_components':ncI})
        priv_pairs.append({'pair_id':pair,'comparison':'fseries_vs_ideal','topology':top,'candidate_ideal':cI,'candidate_fseries':cF})
        if include_relaxed_control and top in R:
            eR=_choose_canonical(R[top]);cR,fR,ncR=candidate(eR,'relaxed',top)
            if ncR==ncF:
                pair2='PAIR_'+secrets.token_hex(6).upper();arr=[(cR,fR),(cF,fF)];rng.shuffle(arr)
                pub_pairs.append({'pair_id':pair2,'candidate_a':arr[0][0],'geometry_a':arr[0][1],'candidate_b':arr[1][0],'geometry_b':arr[1][1],'n_components':ncR})
                priv_pairs.append({'pair_id':pair2,'comparison':'fseries_vs_relaxed','topology':top,'candidate_relaxed':cR,'candidate_fseries':cF})
    rng.shuffle(pub_pairs)
    with open(public/'pairs_public.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['pair_id','candidate_a','geometry_a','candidate_b','geometry_b','n_components']);w.writeheader();w.writerows(pub_pairs)
    with open(private/'candidate_key.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id','source_family','topology','variant','source_path','source_sha256']);w.writeheader();w.writerows(priv_cands)
    pfields=sorted({k for r in priv_pairs for k in r})
    with open(private/'pair_key.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=pfields);w.writeheader();w.writerows(priv_pairs)
    commitment=_private_commitment([private/'candidate_key.csv',private/'pair_key.csv'])
    manifest={'campaign_format':'SST-FVI-BLIND-1','n_pairs':len(pub_pairs),'n_candidates':len({r['candidate_id'] for r in priv_cands}),'resample_n_per_component':n,'preparation_seed':seed,'public_pair_sha256':sha256_file(public/'pairs_public.csv'),'private_key_commitment_sha256':commitment,'blind_fields_hidden':['source_family','topology','source_path','comparison'],'preparation_mode':mode,'note':'Source/topology identities are absent from the public catalog. Numerical scoring must not read private/.'}
    (public/'manifest_public.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    # Human-readable source discovery is deliberately private.
    (private/'source_discovery.json').write_text(json.dumps(paths,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return manifest
