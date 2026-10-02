from __future__ import annotations
from pathlib import Path
import re, json
from collections import defaultdict
from .models import Carrier
from .hashing import stable_id, sha256_file
from .gilbert import iter_gilbert_record_headers
from .repo_finder import iter_file_records


def topology_from_path(path):
    """Extract a topology label from source-local path segments, never from version numbers."""
    rawpath=str(path)
    parts=[x for x in re.split(r'[\\/]+',rawpath) if x]
    probes=([parts[-1]] if parts else [rawpath]) + list(reversed(parts[-10:-1]))
    for raw in probes:
        x=str(raw)
        m=re.search(r'(?i)(?:knot|katlas_braid)[._-]?(\d{1,2})[._](\d+)',x)
        if m: return f'{int(m.group(1))}_{int(m.group(2))}'
        m=re.search(r'(?i)(?:^|[^a-z0-9])K?(\d{1,2})([an])[_-]?(\d+)(?:[^a-z0-9]|$)',x)
        if m: return f'{int(m.group(1))}{m.group(2).lower()}_{int(m.group(3))}'
        m=re.fullmatch(r'(\d{1,2})[._](\d+)',x)
        if m and int(m.group(1))>=1: return f'{int(m.group(1))}_{int(m.group(2))}'
        # Link namespaces occasionally appear as L6a4 / L6_3_2. Keep them disjoint.
        m=re.fullmatch(r'(?i)L(\d{1,2})([an])[_-]?(\d+)',x)
        if m: return f'L{int(m.group(1))}{m.group(2).lower()}{int(m.group(3))}'
    return None


def relaxation_stage_from_path(path):
    s=str(path).replace('\\','/').lower()
    if re.search(r'(^|/)(seed|seeds|initial|initial_seeds)(/|$)',s): return 'SEED'
    if re.search(r'(^|/)(n0*600|600)(/|$)',s): return 'N0600'
    if re.search(r'(^|/)(n0*1200|1200)(/|$)',s): return 'N1200'
    if 'nearideal' in s or 'near_ideal' in s or 'near-ideal' in s: return 'NEAR_IDEAL'
    if 'continued' in s or 'continue' in s: return 'CONTINUED'
    if re.search(r'(^|/)(final|finals)(/|$)',s) or '_final' in s or '.final.' in s: return 'FINAL'
    if 'relax' in s: return 'RELAXED_INTERMEDIATE'
    return 'UNSPECIFIED'


def _carrier(path,topo,family,role,repr_,ind,parent=None,meta=None,provider=None,lineage=None,method=None,catalog_id=None):
    p=Path(path); raw=sha256_file(p)
    return Carrier(
        carrier_id=stable_id('CAR',family,str(p.resolve()),raw), topology_id=topo,
        source_family=family, source_role=role, representation=repr_, source_path=str(p),
        variant_id=p.stem, independence_group=ind, parent_source_family=parent, raw_sha256=raw,
        provider_group=provider, lineage_group=lineage, method_group=method, catalog_id=catalog_id,
        metadata=meta or {},
    )


def _infer_a007_family(path, role):
    s=str(path).replace('\\','/').lower()
    if 'katlas_braid' in s:
        return ('katlas_braid_derived','generated_from_topology_reference','xyz','katlas','sst-generated','katlas-braid')
    if 'ridgerunner' in s or 'rawdon' in s or 'cantarella' in s:
        return ('ridgerunner','derived_relaxed_geometry','vect','knotplot','ridgerunner','ridgerunner-relaxation')
    if 'fremlin' in s:
        # Representation is file-specific: .fseries is a coefficient series, while
        # Fremlin .short files are sampled XYZ curves.  Let the repository scanner's
        # representation_hint decide instead of forcing every Fremlin mirror to fseries.
        return ('fremlin_fourier_mirror','mirror_reference_geometry','auto','fremlin_fourier','fremlin','fremlin-fourier')
    if 'gilbert' in s or 'ideal_' in s:
        return ('gilbert_ideal_mirror','mirror_reference_geometry','auto','gilbert_ideal','gilbert','gilbert-ideal')
    if 'knotplot' in s:
        return ('knotplot_library_mirror','mirror_reference_geometry','auto','knotplot_relaxed','knotplot','knotplot')
    if role == 'derived_geometry':
        return ('knot_library_derived','derived_geometry','auto','knot_library','sst-knot-library','derived')
    return ('knot_library_source','upstream_or_mirror_source_geometry','auto',None,'sst-knot-library','source-import')


def _representation_from_record(rec, family):
    hint=rec.get('representation_hint') or ''
    p=Path(rec['path'])
    if family in ('fremlin_fourier','fremlin_fourier_mirror'):
        # Historical A007 mirrors are not extension-clean: some .fseries and .short
        # files are sampled XYZ centerlines. The scanner's content-derived hint wins.
        if hint in ('xyz_short','xyz_text'): return 'xyz'
        if p.suffix.lower()=='.fseries': return 'fremlin_fseries'
        return hint
    if family=='ridgerunner': return 'vect' if p.suffix.lower()=='.vect' else hint
    if family=='ptsa' or family=='ptsa_control': return 'xyz'
    if hint in ('knotplot_ideal_xyz','xyz_text','xyz_short'): return 'xyz'
    if hint=='knotplot_binary': return 'knotplot_binary'
    if hint in ('vect','xyz','npz','npy','qhp','fseries'): return hint
    return hint or p.suffix.lower().lstrip('.') or 'auto'


def discover_from_repo_scan(scan, topology=None):
    """Turn repository finder records into geometry carriers.

    This is deliberately conservative: metadata, registry and quarantine records are not
    admitted as geometry. A005 KAtlas upstream files remain topology references; only
    explicit 3-D derived records can become generated controls.
    """
    out=[]
    # A004 multi-record Gilbert catalogues need record-level virtual carriers.
    for rec in iter_file_records(scan, catalog_id='A004', roles={'geometry_catalog'}):
        gp=Path(rec['path'])
        try:
            raw=sha256_file(gp)
            for r in iter_gilbert_record_headers(gp):
                topo=r.get('canonical_id')
                if not topo or (topology and topo!=topology): continue
                rid=r['attrs'].get('Id')
                out.append(Carrier(
                    carrier_id=stable_id('CAR','gilbert_ideal',str(gp.resolve()),rid,raw),
                    topology_id=topo, source_family='gilbert_ideal',
                    source_role='independent_ideal_reference_geometry', representation='gilbert_ab_record',
                    source_path=str(gp), reference_id=rid, variant_id=rid,
                    independence_group=f'gilbert-ideal:{topo}', provider_group='gilbert',
                    lineage_group=f'gilbert:{topo}', method_group='gilbert-fourier-ideal', catalog_id='A004',
                    raw_sha256=raw, metadata={
                        'gilbert_record_id':rid,
                        'reference_ropelength':r.get('reference_length'),
                        'reference_diameter':float(r['attrs']['D']) if r['attrs'].get('D') else None,
                        'catalog_file':gp.name,
                        'discovery_origin':'repo_source_finder',
                    }))
        except Exception:
            pass

    allowed_roles={'geometry','source_geometry','derived_geometry','generated_geometry','generated_control_geometry'}
    for rec in iter_file_records(scan, roles=allowed_roles):
        cid=rec['catalog_id']; p=Path(rec['path']); role=rec['role']
        if cid=='A004':
            continue
        topo=topology_from_path(p)
        if cid=='A008':
            topo='3_1'  # E009/PTSA v1.0.0 is explicitly trefoil; never infer topology from hash-like filenames.
        if not topo or (topology and topo!=topology):
            continue
        meta={
            'catalog_id':cid,'catalog_slug':rec.get('catalog_slug'),'source_root':rec.get('source_root'),
            'relative_path':rec.get('relative_path'),'repo_role':role,'representation_hint':rec.get('representation_hint'),
            'discovery_origin':'repo_source_finder',
        }
        if cid=='A001':
            if p.name.lower()=='ideal.txt' or rec.get('representation_hint')=='knotplot_ideal_xyz':
                family='knotplot_ideal'; source_role='ideal_reference_geometry'; parent=None
                provider='knotplot'; lineage=f'knotplot:{topo}:ideal'; method='knotplot-ideal'
                ind=f'knotplot-ideal:{topo}'
            else:
                family='knotplot_relaxed'; stage=relaxation_stage_from_path(p); meta['relaxation_stage']=stage
                source_role='relaxed_reference_geometry' if stage=='FINAL' else 'historical_relaxation_state'
                parent=None; provider='knotplot'; lineage=f'knotplot:{topo}:relaxation'; method='knotplot-relaxation'; ind=f'knotplot-relaxed:{topo}'
        elif cid=='A002':
            family='knotplot_fourier_series'; source_role='reference_fourier_geometry'; parent=None
            provider='knotplot'; lineage=f'knotplot-fourier:{topo}'; method='fourier-series'; ind=f'knotplot-fourier:{topo}'
        elif cid=='A003':
            family='knotplot_qhp'; source_role='qhp_reference_or_seed_geometry'; parent=None
            provider='knotplot'; lineage=f'knotplot-qhp:{topo}'; method='qhp'; ind=f'knotplot-qhp:{topo}'
        elif cid=='A005':
            family='katlas_source_derived'; source_role='generated_from_topology_reference'; parent='katlas'
            provider='katlas'; lineage=f'katlas-derived:{topo}'; method='katlas-derived-geometry'; ind=f'katlas-derived:{topo}'
            meta['guard']='Upstream KAtlas is topology/reference data; this 3-D artifact is treated as derived geometry only.'
        elif cid=='A006':
            family='fremlin_fourier'; source_role='independent_reference_geometry'; parent=None
            provider='fremlin'; lineage=f'fremlin:{topo}'; method='fremlin-fourier'; ind=f'fremlin:{topo}'
        elif cid=='A007':
            family,source_role,rep_override,parent,provider,method=_infer_a007_family(p,role)
            lineage=f'{family}:{topo}'; ind=f'{family}:{topo}'
            meta['a007_container_role']=role
        elif cid=='A008':
            if role=='generated_control_geometry':
                family='ptsa_control'; source_role='generated_control_family'; ind='ptsa-control:v1.0.0'
            else:
                family='ptsa'; source_role='generated_experimental_family'; ind='ptsa:v1.0.0'
            parent='sst_generated'; provider='sst_generated'; lineage='ptsa:v1.0.0'; method='ptsa-track-trefoil'
        else:
            continue
        rep=_representation_from_record(rec,family)
        if cid=='A007' and 'rep_override' in locals() and rep_override!='auto': rep=rep_override
        out.append(_carrier(p,topo,family,source_role,rep,ind,parent=parent,meta=meta,provider=provider,lineage=lineage,method=method,catalog_id=cid))
    return out


def discover_workbench(workbench_root, topology=None):
    """Legacy targeted discovery retained for compatibility with builder v0.1.0.

    v0.2.0 build flows prefer repository-wide discovery via ``discover_from_repo_scan``.
    """
    root=Path(workbench_root); out=[]
    if not root.exists(): return out
    def addglob(pattern,family,role,repr_,indfn,parent=None,filterfn=None,provider=None,method=None,catalog_id=None):
        for p in root.glob(pattern):
            if not p.is_file() or (filterfn and not filterfn(p)): continue
            topo=topology_from_path(p)
            if not topo or (topology and topo!=topology): continue
            out.append(_carrier(p,topo,family,role,repr_,indfn(p,topo),parent,provider=provider,lineage=indfn(p,topo),method=method,catalog_id=catalog_id))
    addglob('Ideal_Fremlin_Fseries/fremlin/**/*.fseries','fremlin_fourier','independent_reference_geometry','fremlin_fseries',lambda p,t:f'fremlin:{t}',provider='fremlin',method='fremlin-fourier',catalog_id='A006')
    addglob('Fremlin_FourierSeries/**/*.fseries','fremlin_fourier','independent_reference_geometry','fremlin_fseries',lambda p,t:f'fremlin:{t}',provider='fremlin',method='fremlin-fourier',catalog_id='A006')
    addglob('KnotPlot/Knots_FourierSeries/**/*.fseries','knotplot_fourier_series','reference_fourier_geometry','fremlin_fseries',lambda p,t:f'knotplot-fourier:{t}',provider='knotplot',method='fourier-series',catalog_id='A002')
    addglob('KnotPlot/knots/**/*','knotplot_relaxed','historical_relaxation_state','auto',lambda p,t:f'knotplot-relaxed:{t}',filterfn=lambda p:p.suffix.lower() in ('.txt','.xyz','.vect','.locd','.locf'),provider='knotplot',method='knotplot-relaxation',catalog_id='A001')
    # Legacy KAtlas braid-derived controls inside Knot_Library.
    for kp in root.glob('Knot_Library/**/katlas_braid_*.xyz'):
        topo=topology_from_path(kp)
        if topo and (not topology or topo==topology):
            out.append(_carrier(kp,topo,'katlas_braid_derived','generated_from_topology_reference','xyz',f'katlas-derived:{topo}',parent='katlas',provider='katlas',lineage=f'katlas-derived:{topo}',method='katlas-braid',catalog_id='A007',meta={'guard':'Generated from KAtlas topology/braid data; not an upstream KAtlas 3-D embedding.'}))
    # Gilbert multi-record catalogues.
    for gp in sorted((root/'Ideal_Sources').glob('Ideal*.txt.gz')) if (root/'Ideal_Sources').exists() else []:
        try:
            raw=sha256_file(gp)
            for rec in iter_gilbert_record_headers(gp):
                topo=rec.get('canonical_id')
                if not topo or (topology and topo!=topology): continue
                rid=rec['attrs'].get('Id')
                out.append(Carrier(carrier_id=stable_id('CAR','gilbert_ideal',str(gp.resolve()),rid,raw),topology_id=topo,source_family='gilbert_ideal',source_role='independent_ideal_reference_geometry',representation='gilbert_ab_record',source_path=str(gp),reference_id=rid,variant_id=rid,independence_group=f'gilbert-ideal:{topo}',provider_group='gilbert',lineage_group=f'gilbert:{topo}',method_group='gilbert-fourier-ideal',catalog_id='A004',raw_sha256=raw,metadata={'gilbert_record_id':rid,'reference_ropelength':rec.get('reference_length'),'reference_diameter':float(rec['attrs']['D']) if rec['attrs'].get('D') else None,'catalog_file':gp.name}))
        except Exception:
            pass
    return out


def discover_from_v020(base_root, topology=None):
    root=Path(base_root); out=[]
    if not root.exists(): return out
    ref=root/'manifests'/'REFERENCE_CARRIERS.jsonl'
    if ref.exists():
        with ref.open(encoding='utf-8') as fh:
            for line in fh:
                if not line.strip(): continue
                r=json.loads(line); topo=r.get('topology_id') or r.get('canonical_id') or r.get('canonical_label') or r.get('name')
                if topo and topology and topo!=topology: continue
                sf=r.get('source_family')
                if sf=='knotinfo': fam='knotinfo_3d'; ind=f'knotinfo-3d:{topo}'; provider='knotinfo'; method='knotinfo-3d'
                elif sf in ('knotplot','knotplot_relaxed'): fam='knotplot_relaxed'; ind=f'knotplot-relaxed:{topo}'; provider='knotplot'; method='knotplot-relaxation'
                else: continue
                out.append(Carrier(carrier_id=r.get('reference_id') or r.get('carrier_id'),topology_id=topo,source_family=fam,source_role=r.get('source_role','reference_embedding'),representation='pklsa_v020_compact',reference_id=r.get('reference_id') or r.get('carrier_id'),variant_id=r.get('variant_id'),independence_group=ind,provider_group=provider,lineage_group=ind,method_group=method,raw_sha256=r.get('raw_sha256') or r.get('coordinate_sha256') or r.get('source_record_sha256'),metadata={'v020_record':r,'upstream_representation':r.get('representation'),'discovery_origin':'pklsa_v020_fallback'}))
    cfile=root/'manifests'/'CANDIDATES_V2.jsonl'
    if cfile.exists():
        with cfile.open(encoding='utf-8') as fh:
            for line in fh:
                if not line.strip(): continue
                r=json.loads(line); topo=r.get('canonical_id')
                if topology and topo!=topology: continue
                method=str(r.get('construction_method','')).lower()
                if 'ptsa' in method:
                    fam='ptsa'; parent='sst_generated'; ind='ptsa:v1.0.0'; mgroup='ptsa-track-trefoil'
                elif 'siaf' in method:
                    fam='siaf'; parent=r.get('parent_source_family'); ind=r.get('independence_group','siaf'); mgroup='siaf-control'
                else: continue
                out.append(Carrier(carrier_id=r['candidate_id'],topology_id=topo,source_family=fam,source_role='generated_experimental_family',representation='pklsa_v020_candidate',reference_id=r['candidate_id'],variant_id=r.get('variant_id'),independence_group=ind,parent_source_family=parent,provider_group='sst_generated',lineage_group=ind,method_group=mgroup,raw_sha256=r.get('source_record_sha256'),metadata={'v020_candidate':r,'discovery_origin':'pklsa_v020_fallback'}))
    return out


def reconcile_source_mirrors(carriers):
    """Collapse byte-identical mirrors without erasing provenance.

    Exact raw-byte equality is sufficient to mark a mirror. Geometry equality after
    resampling is deliberately *not* used here because independently produced sources may
    converge to numerically identical sampled curves.
    """
    priority={
        'fremlin_fourier':0,'gilbert_ideal':1,'knotplot_relaxed':2,'knotplot_ideal':3,
        'ridgerunner':4,'knotinfo_3d':5,'ptsa':6,'siaf':7,
        'knotplot_fourier_series':20,'fremlin_fourier_mirror':21,'knotplot_library_mirror':22,
        'gilbert_ideal_mirror':23,'knot_library_source':30,'knot_library_derived':31,
    }
    by_hash=defaultdict(list)
    for c in carriers:
        if c.raw_sha256: by_hash[c.raw_sha256].append(c)
    for _h,cs in by_hash.items():
        if len(cs)<2: continue
        cs.sort(key=lambda c:(priority.get(c.source_family,50), 0 if c.source_path else 1, c.carrier_id))
        canonical=cs[0]
        for c in cs[1:]:
            if c.carrier_id==canonical.carrier_id: continue
            c.metadata=dict(c.metadata or {})
            c.metadata['byte_identical_mirror_of']=canonical.carrier_id
            c.metadata['byte_identical_source_family']=canonical.source_family
            c.source_role='mirror_reference_geometry' if not c.source_role.startswith('generated') else c.source_role
            c.parent_source_family=canonical.source_family
            c.independence_group=canonical.independence_group
            c.provider_group=canonical.provider_group
            c.lineage_group=canonical.lineage_group
    return carriers


def prefer_source_native(carriers):
    """When source-native PTSA is present, suppress v0.2.0 PTSA fallback duplicates.

    v0.2.0 remains a compatibility source for SIAF and any geometry not found natively.
    """
    native_ptsa=any(c.source_family=='ptsa' and c.catalog_id=='A008' and c.source_path for c in carriers)
    if not native_ptsa: return carriers
    return [c for c in carriers if not (c.source_family=='ptsa' and (c.metadata or {}).get('discovery_origin')=='pklsa_v020_fallback')]


def dedupe_carriers(carriers):
    seen={}; out=[]
    for c in carriers:
        key=(c.carrier_id,c.source_path,c.reference_id)
        if key in seen: continue
        seen[key]=1; out.append(c)
    return reconcile_source_mirrors(prefer_source_native(out))
