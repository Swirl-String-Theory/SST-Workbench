from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import re
from .formats import load_geometry, classify_non_geometry_file, file_sha256
from .registry import KAtlasSnapshot, infer_topology_hint_from_name
from .blind import geometry_sha256
from .geometry import resample_closed
from .providers import certify_geometry
from .sources import source_provider_info

DEFAULT_EXTENSIONS={'.txt','.xyz','.csv','.vect','.knot','.kp','.kpf'}
SPECIAL_NAMES={'fseries','ideal','ideal.txt'}


def _numeric_xyz_signature(path: Path, *, max_lines: int=128) -> tuple[bool,dict]:
    """Cheap, fail-closed sniff for plain XYZ-like text without fully parsing the file."""
    numeric=0; content=0; comment=0
    try:
        text=path.read_text(encoding='utf-8',errors='ignore')
    except Exception as e:
        return False, {'reason':f'text sniff failed: {type(e).__name__}: {e}'}
    for line in text.splitlines()[:max_lines]:
        s=line.strip()
        if not s: continue
        if s.startswith(('#','//',';')): comment+=1; continue
        if re.match(r'(?i)^(component|comp)\b',s): continue
        content+=1
        toks=re.split(r'[\s,;]+',s)
        vals=[]
        for tok in toks:
            if not tok: continue
            try: vals.append(float(tok))
            except ValueError: break
        if len(vals)>=3: numeric+=1
    # Three independent XYZ rows are enough to classify as a geometry candidate.
    ok=numeric>=3
    return ok, {'numeric_xyz_lines':numeric,'content_lines_sampled':content,'comment_lines_sampled':comment}


def classify_scan_candidate(path: Path, hint: dict|None=None) -> dict:
    """Decide whether a selected file should be parsed as geometry.

    This is intentionally separate from ``load_geometry``. A project tree can contain thousands
    of .txt/.csv support files. Those must not inflate ERROR counts merely because their suffix is
    shared with coordinate files. Strong geometry signatures remain fail-closed: if they are
    recognized and parsing fails, the inventory records ERROR.
    """
    nong=classify_non_geometry_file(path)
    if nong:
        return {'action':'SKIP_METADATA', **nong}
    n=path.name.lower(); ext=path.suffix.lower()
    # Ridgerunner auxiliary VECT products are not centerlines.  They encode
    # contact struts or per-step diagnostic vector/scalar fields and must never
    # be admitted as knot/link geometry merely because they use VECT syntax.
    if re.search(r'(?i)\.(?:struts|dlen|dvdt)\.vect$', n):
        return {'action':'SKIP_NON_GEOMETRY','role':'ridgerunner_diagnostic',
                'reason':'Ridgerunner auxiliary diagnostic VECT, not a centerline'}
    try: head=path.read_bytes()[:4096]
    except Exception as e:
        return {'action':'PARSE','strength':'strong','reason':f'cannot inspect bytes: {type(e).__name__}: {e}'}
    if head.startswith(b'KnotPlot 1.0'):
        return {'action':'PARSE','strength':'strong','reason':'KnotPlot 1.0 binary signature'}
    if head.lstrip().startswith(b'VECT'):
        return {'action':'PARSE','strength':'strong','reason':'VECT signature'}
    if (b'<AB' in head or b'<HT' in head) and b'<Coeff' in head:
        return {'action':'PARSE','strength':'strong','reason':'Gilbert Fourier signature'}
    if ext in {'.xyz','.vect','.knot','.kp','.kpf'} or n in SPECIAL_NAMES:
        return {'action':'PARSE','strength':'strong','reason':'strong geometry filename/extension'}
    if ext in {'.txt','.csv'}:
        looks_xyz,diag=_numeric_xyz_signature(path)
        if looks_xyz:
            return {'action':'PARSE','strength':'content','reason':'XYZ numeric content signature',**diag}
        # If a topology-bearing filename/path strongly claims geometry, malformed data is an error.
        if hint and re.search(r'(?i)(?:^|[\\/_-])(knot|link|torus)[_.-]?\d',str(path)):
            return {'action':'PARSE','strength':'name','reason':'topology-bearing geometry filename',**diag}
        return {'action':'SKIP_NON_GEOMETRY','role':'unrecognized_project_text',
                'reason':'no supported geometry signature in text/csv file',**diag}
    return {'action':'SKIP_NON_GEOMETRY','role':'unsupported_selected_file',
            'reason':f'no supported geometry signature for {ext or "extensionless"} file'}


def scan_dataset(root, *, n_hash: int=512, certify: bool=False, provider: str='auto', extensions=None):
    root=Path(root); extset={x.lower() for x in (extensions or DEFAULT_EXTENSIONS)}; reg=KAtlasSnapshot(); rows=[]
    all_paths=sorted(p for p in root.rglob('*') if p.is_file())
    selected=[]; ignored=Counter(); ignored_examples={}
    for p in all_paths:
        if p.suffix.lower() in extset or p.name.lower() in SPECIAL_NAMES:
            selected.append(p)
        else:
            ext=p.suffix.lower() or '<extensionless>'; ignored[ext]+=1
            ex=ignored_examples.setdefault(ext,[])
            if len(ex)<5: ex.append(str(p.relative_to(root)))
    for path in selected:
        rel=str(path.relative_to(root)); hint=infer_topology_hint_from_name(rel)
        row={
            'path':str(path),'relative_path':rel,
            'topology_hint':hint,
            'topology_kind':hint.get('kind') if hint else None,
            'expected_topology':hint.get('id') if hint else None,
            'expected_components':hint.get('components_hint') if hint else None,
        }
        decision=classify_scan_candidate(path,hint)
        if decision['action']=='SKIP_METADATA':
            row.update({
                'load_status':'SKIPPED_METADATA','source_sha256':file_sha256(path),
                'metadata_role':decision['role'],'provider_id':decision['provider_id'],'reason':decision['reason'],
                'topology_certification':{'status':'UNVERIFIED','pass':False,'provider':'none'}
            })
            rows.append(row); continue
        if decision['action']=='SKIP_NON_GEOMETRY':
            row.update({
                'load_status':'SKIPPED_NON_GEOMETRY','source_sha256':file_sha256(path),
                'metadata_role':decision.get('role','non_geometry'),'reason':decision['reason'],
                'scan_diagnostics':{k:v for k,v in decision.items() if k not in {'action','role','reason'}},
                'topology_certification':{'status':'UNVERIFIED','pass':False,'provider':'none'}
            })
            rows.append(row); continue
        row['scan_candidate']={'strength':decision.get('strength'),'reason':decision.get('reason')}
        try:
            a=load_geometry(path); pi=source_provider_info(a.source_family,str(path))
            row.update({
                'load_status':'OK','source_family':a.source_family,'source_format':a.source_format,
                'source_sha256':a.source_sha256,'components':len(a.components),'n_points':[len(c) for c in a.components],
                'provider_id':pi['provider_id'],'provider_name':pi['name'],'provider_class':pi['class'],
                'provider_catalog_id':pi['catalog_id'],'provider_catalog_sha256':pi['catalog_sha256'],
                'warnings':a.warnings,'metadata':a.metadata,
            })
            row['component_count_matches_hint']=(row['expected_components'] is None or len(a.components)==row['expected_components'])
            row['canonical_geometry_sha256']=[geometry_sha256(resample_closed(c,n_hash)) for c in a.components]
            kid=row['expected_topology'] if row['topology_kind']=='knot' else None
            row['katlas_registered']=bool(kid and reg.has(kid))
            if certify and len(a.components)==1 and kid and reg.has(kid):
                row['topology_certification']=certify_geometry(resample_closed(a.components[0],n_hash),kid,provider=provider,registry=reg).to_dict()
            else:
                note='no geometry topology provider executed'
                if row['topology_kind'] in {'link','torus'}: note='link/torus filename is an expected-topology hint only; no imported-geometry certification executed'
                row['topology_certification']={'status':'UNVERIFIED','pass':False,'provider':'none','notes':[note]}
        except Exception as e:
            row.update({'load_status':'ERROR','error':f'{type(e).__name__}: {e}'})
        rows.append(row)
    statuses=('OK','SKIPPED_METADATA','SKIPPED_NON_GEOMETRY','ERROR')
    counts={s:sum(r.get('load_status')==s for r in rows) for s in statuses}
    return {
        'root':str(root),
        'discovered_file_count':len(all_paths),
        'file_count':len(rows),
        'selected_file_count':len(selected),
        'ignored_extension_counts':dict(sorted(ignored.items(),key=lambda kv:(-kv[1],kv[0]))),
        'ignored_extension_examples':{k:ignored_examples[k] for k in sorted(ignored_examples)},
        'counts':counts,
        'katlas_snapshot_id':reg.snapshot_id,'katlas_snapshot_sha256':reg.sha256,'files':rows
    }


def write_inventory(path, report):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
