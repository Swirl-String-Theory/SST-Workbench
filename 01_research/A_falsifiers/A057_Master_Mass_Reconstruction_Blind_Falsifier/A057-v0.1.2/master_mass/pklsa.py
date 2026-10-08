from __future__ import annotations
from pathlib import Path
import json,sys,re
import numpy as np
from .utils import sha256_file,geometry_sha256,crossing_number

E010_REL=Path('01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas')

def locate_e010(workbench: Path):
    fam=workbench/E010_REL
    cand=sorted([p for p in fam.glob('E010-v0.3.*') if p.is_dir()],key=lambda p:tuple(int(x) for x in re.findall(r'\d+',p.name)[-3:]),reverse=True)
    for p in cand:
        outs=list(p.glob('E010_PKLSA_Production_Knot_Link_Basis_v0.3.*-outputs'))
        if outs and (outs[0]/'RELEASE.json').is_file(): return p,outs[0]
    raise FileNotFoundError(f'No E010-v0.3.x production release beneath {fam}')

def _import_loader(e010):
    s=str(e010)
    if s not in sys.path:sys.path.insert(0,s)
    from pklsa_builder.io_geometry import load_geometry
    try:
        from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_components
    except Exception: find_gilbert_record=sample_gilbert_components=None
    return load_geometry,find_gilbert_record,sample_gilbert_components

def _remap_source(path_str,workbench):
    if not path_str:return None
    p=Path(path_str)
    if p.exists():return p
    s=str(path_str).replace('\\','/')
    marker='SST-Workbench/'
    if marker in s:return workbench/Path(s.split(marker,1)[1])
    return workbench/p if not p.is_absolute() else p

def _load_row_geometry(row,e010,workbench):
    carrier=row.get('carrier',row); rep=carrier.get('representation');sp=_remap_source(carrier.get('source_path'),workbench)
    if sp is None or not sp.is_file(): raise FileNotFoundError(str(sp))
    if carrier.get('raw_sha256'):
        actual=sha256_file(sp)
        if actual!=carrier['raw_sha256']: raise ValueError('raw_sha256 mismatch')
    load,find_gilbert_record,sample_gilbert_components=_import_loader(e010)
    if rep=='gilbert_ab_record':
        if find_gilbert_record is None:raise RuntimeError('Gilbert loader unavailable')
        rec=find_gilbert_record(sp,carrier.get('topology_id'))
        native_n=int((carrier.get('metadata') or {}).get('native_sample_n',4096))
        comps=sample_gilbert_components(rec,n=max(4096,native_n))
    else: comps=load(sp,representation=rep)
    comps=[np.asarray(c,dtype=float) for c in comps]
    expected=row.get('geometry_sha256')
    actual=geometry_sha256(comps)
    if expected and actual!=expected:raise ValueError('geometry_sha256 mismatch')
    return comps,sp,actual

def _independence_map(qdir):
    p=qdir/'source_independence.json'
    if not p.is_file():return {}
    try:d=json.loads(p.read_text(encoding='utf-8'))
    except Exception:return {}
    rows=[]
    if isinstance(d,list):rows=d
    elif isinstance(d,dict):
        for k in ('entries','carriers','rows','results'):
            if isinstance(d.get(k),list):rows=d[k];break
    out={}
    for r in rows:
        if isinstance(r,dict):out[r.get('carrier_id') or r.get('carrier',{}).get('carrier_id')]=r
    return out

def topology_features(topology_dir: Path):
    """Best-effort extraction of scalar topology-reference descriptors with provenance paths.

    Only explicit reference JSON under the E010 topology directory is inspected.  Missing
    descriptors remain missing; no values are synthesized from topology names.
    """
    td=Path(topology_dir)/'topology'; found={}; provenance={}
    wanted={
        'hyperbolic_volume':('hyperbolic_volume','hyperbolic volume','volume_hyperbolic','volume'),
        'genus':('genus','seifert_genus'),
        'bridge_index':('bridge_index','bridge number','bridge_number'),
        'braid_index':('braid_index','braid index'),
        'crossing_number':('crossing_number','crossing number'),
    }
    def walk(obj,path=()):
        if isinstance(obj,dict):
            for k,v in obj.items():
                kp=' '.join(str(k).lower().replace('-','_').split())
                for dest,names in wanted.items():
                    if dest in found: continue
                    match=kp in names or (dest=='hyperbolic_volume' and 'hyperbol' in kp and 'vol' in kp)
                    if match and isinstance(v,(int,float)) and np.isfinite(v):
                        # Bare 'volume' is admitted only when positive and comes from topology reference data.
                        if float(v)>0: found[dest]=float(v);provenance[dest]='/'.join(path+(str(k),))
                walk(v,path+(str(k),))
        elif isinstance(obj,list):
            for i,v in enumerate(obj): walk(v,path+(str(i),))
    if td.is_dir():
        for fp in sorted(td.rglob('*.json')):
            try: walk(json.loads(fp.read_text(encoding='utf-8')), (fp.name,))
            except Exception: continue
    return {"values":found,"provenance":provenance}

def discover_carriers(workbench,config):
    e010,out=locate_e010(Path(workbench)); release=json.loads((out/'RELEASE.json').read_text(encoding='utf-8'))
    roots=[]
    atlas=out/'atlas'
    if atlas.is_dir(): roots.extend([p for p in atlas.iterdir() if p.is_dir()])
    poc=out/'poc'/'atlas'
    if poc.is_dir():
        for p in poc.iterdir():
            if p.is_dir() and not any(q.name==p.name for q in roots):roots.append(p)
    requested=set(config.get('requested_topologies') or []);maxc=int(config.get('max_crossing',999));tops=[]
    for td in roots:
        top=td.name;cn=crossing_number(top)
        if requested and top not in requested:continue
        if cn is not None and cn>maxc:continue
        tops.append(td)
    tops=sorted(tops,key=lambda p:p.name)
    if config.get('max_topologies',0):tops=tops[:int(config['max_topologies'])]
    entries=[]
    for td in tops:
        q=td/'qualification'; gm=q/'geometry_metrics.jsonl'; tfeat=topology_features(td)
        if not gm.is_file():continue
        indep=_independence_map(q); rows=[]
        for line in gm.read_text(encoding='utf-8',errors='replace').splitlines():
            try:r=json.loads(line)
            except Exception:continue
            car=r.get('carrier',{}); qual=r.get('qualification',{}) or {}; lit=qual.get('literature_gates',{}) or {}
            if lit.get('hard_gate_pass') is False:continue
            ir=indep.get(car.get('carrier_id'),{}) or {}; ev=(ir.get('evidence_independence_class') or ir.get('evidence_class') or ir.get('classification') or '').upper()
            if 'MIRROR_NOT_INDEPENDENT' in ev or 'BYTE_IDENTICAL' in ev:continue
            if ir.get('raw_duplicate_of'):continue
            rows.append(r)
        # deterministic diversity-first selection
        rows.sort(key=lambda r:(str(r.get('carrier',{}).get('independence_group')),str(r.get('carrier',{}).get('carrier_id'))))
        cap=int(config.get('max_carriers_per_topology',0)); chosen=[];seen=set()
        for r in rows:
            car=r.get('carrier',{});grp=car.get('independence_group') or car.get('provider_group') or car.get('source_family')
            if grp not in seen:chosen.append(r);seen.add(grp)
        for r in rows:
            if r not in chosen:chosen.append(r)
        if cap:chosen=chosen[:cap]
        for r in chosen:
            car=r.get('carrier',{}); rec={"topology_id":td.name,"topology_dir":str(td),"topology_features":tfeat,"carrier":car,"qualification":r.get('qualification',{}),"geometry_sha256":r.get('geometry_sha256'),"independence":indep.get(car.get('carrier_id'),{})}
            try:
                comps,sp,gh=_load_row_geometry(r,e010,Path(workbench));rec.update({"ok":True,"components":comps,"resolved_source_path":str(sp),"verified_geometry_sha256":gh})
            except Exception as ex:rec.update({"ok":False,"error":f'{type(ex).__name__}: {ex}'})
            entries.append(rec)
    return {"e010":str(e010),"output":str(out),"release":release,"entries":entries}
