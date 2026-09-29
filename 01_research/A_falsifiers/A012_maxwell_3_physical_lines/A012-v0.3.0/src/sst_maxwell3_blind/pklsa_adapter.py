from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import hashlib
import importlib
import json
import os
import re
import sys

import numpy as np

PKLSA_FAMILY_REL = Path('01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas')


def _semver_key(name: str):
    m = re.search(r'v(\d+)\.(\d+)\.(\d+)', name)
    return tuple(map(int, m.groups())) if m else (-1, -1, -1)


def resolve_workbench_root(explicit: str | Path | None = None) -> Path:
    candidates=[]
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get('SST_WORKBENCH_ROOT'):
        candidates.append(Path(os.environ['SST_WORKBENCH_ROOT']))
    cwd=Path.cwd().resolve()
    candidates += list(cwd.parents) + [cwd]
    here=Path(__file__).resolve()
    candidates += list(here.parents)
    candidates.append(Path(r'C:\workspace\projects\SST-Workbench'))
    seen=set()
    for p in candidates:
        try: q=p.resolve()
        except Exception: q=p
        s=str(q).lower()
        if s in seen: continue
        seen.add(s)
        if (q/'10_docs'/'registry').exists() or (q/PKLSA_FAMILY_REL).exists():
            return q
    raise FileNotFoundError('SST-Workbench root not found. Pass --workbench or set SST_WORKBENCH_ROOT.')


def resolve_pklsa_release(workbench: Path, explicit: str | Path | None = None) -> tuple[Path, dict]:
    if explicit:
        rel=Path(explicit)
        p=rel if rel.is_absolute() else workbench/rel
        candidates=[p]
    else:
        fam=workbench/PKLSA_FAMILY_REL
        candidates=sorted([p for p in fam.glob('E010-v0.3.*') if p.is_dir()], key=lambda x:_semver_key(x.name), reverse=True)
    if not candidates:
        raise FileNotFoundError(f'No E010 PKLSA v0.3.x release under {workbench/PKLSA_FAMILY_REL}')
    for p in candidates:
        out=p/f'E010_PKLSA_Production_Knot_Link_Basis_{p.name.replace("E010-","")}-outputs'
        release=out/'RELEASE.json'
        if release.exists():
            d=json.loads(release.read_text(encoding='utf-8'))
            if not str(d.get('e010_version','')).startswith('0.3.'):
                continue
            return p,d
    raise FileNotFoundError('Found PKLSA v0.3.x release directories but no usable production RELEASE.json output.')


def outputs_dir(release_root: Path) -> Path:
    name=release_root.name.replace('E010-','')
    p=release_root/f'E010_PKLSA_Production_Knot_Link_Basis_{name}-outputs'
    if not p.exists(): raise FileNotFoundError(p)
    return p


def _load_e010_modules(release_root: Path):
    root=str(release_root)
    if root not in sys.path:
        sys.path.insert(0,root)
    io=importlib.import_module('pklsa_builder.io_geometry')
    hashing=importlib.import_module('pklsa_builder.hashing')
    try:
        native=importlib.import_module('pklsa_builder._native')
    except Exception:
        native=None
    return io,hashing,native


def _remap_source_path(recorded: str, workbench: Path) -> Path:
    p=Path(recorded)
    if p.exists(): return p
    s=str(recorded).replace('/','\\')
    marker='SST-Workbench\\'
    i=s.lower().find(marker.lower())
    if i>=0:
        suffix=s[i+len(marker):].replace('\\',os.sep)
        q=workbench/Path(suffix)
        if q.exists(): return q
    # Last resort: accept relative path only when it resolves inside current workbench.
    q=workbench/p
    if q.exists(): return q
    raise FileNotFoundError(f'PKLSA carrier source bytes unavailable after root remap: {recorded}')


def _sha256_file(path: Path, chunk=1024*1024):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def _read_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def _iter_topology_dirs(out: Path):
    # Full atlas is authoritative. POC is only a fallback for a topology absent from full atlas.
    atlas=out/'atlas'
    seen=set()
    if atlas.exists():
        for d in sorted([x for x in atlas.iterdir() if x.is_dir()]):
            seen.add(d.name); yield d
    poc=out/'poc'/'atlas'
    if poc.exists():
        for d in sorted([x for x in poc.iterdir() if x.is_dir()]):
            if d.name not in seen: yield d


def _carrier_envelopes(topo_dir: Path):
    for role in ('sources','generated'):
        d=topo_dir/role
        if d.exists():
            for p in sorted(d.rglob('CAR_*.json')):
                yield p


@dataclass
class PKLSACarrier:
    topology_id: str
    carrier_id: str
    catalog_id: str | None
    source_family: str | None
    provider_group: str | None
    method_group: str | None
    lineage_group: str | None
    independence_group: str | None
    evidence_independence_class: str | None
    source_role: str | None
    representation: str | None
    source_path: str
    raw_sha256: str
    geometry_sha256: str
    literature_hard_gate_pass: bool
    finest_resolution: int | None
    reach: float | None
    thickness: float | None
    normalization_scale: float
    observable_status: dict
    geometry_duplicate_of: str | None
    raw_duplicate_of: str | None
    envelope_sha256: str
    qualification_contract_sha256: str
    envelope_path: str
    topology_dir: str

    def blind_summary(self):
        def h(x):
            if x is None: return None
            return hashlib.sha256(('SST-MAXWELL3-BLIND-ID-v1|'+str(x)).encode()).hexdigest()[:16]
        return {
            'topology_h':h(self.topology_id), 'carrier_h':h(self.carrier_id),
            'provider_h':h(self.provider_group), 'independence_h':h(self.independence_group),
            'evidence_independence_class':self.evidence_independence_class, 'component_source_role':self.source_role, 'literature_hard_gate_pass':self.literature_hard_gate_pass,
            'finest_resolution':self.finest_resolution, 'reach':self.reach, 'envelope_sha256':self.envelope_sha256, 'qualification_contract_sha256':self.qualification_contract_sha256,
        }


class PKLSARepository:
    def __init__(self, workbench: Path, release_root: Path, release_meta: dict):
        self.workbench=Path(workbench).resolve(); self.release_root=Path(release_root).resolve(); self.release_meta=release_meta
        self.out=outputs_dir(self.release_root)
        self.io,self.hashing,self.native=_load_e010_modules(self.release_root)

    @classmethod
    def open(cls, workbench=None, release=None):
        wb=resolve_workbench_root(workbench); rr,meta=resolve_pklsa_release(wb,release)
        return cls(wb,rr,meta)

    def release_checks(self):
        d=self.release_meta
        def fh(rel):
            p=self.release_root/rel
            return _sha256_file(p) if p.exists() else None
        required=['source_native_mode','source_contract_gate_pass','a001_a008_coverage_gate_pass','canonical_identity_admission_gate_pass','identity_database_gate_pass','topology_database_ingest_gate_pass','unregistered_source_gate_pass']
        checks={k:bool(d.get(k)) for k in required}
        return {
            'e010_version':d.get('e010_version'), 'checks':checks, 'pass':all(checks.values()),
            'global_full_campaign_gate_pass':bool(d.get('full_campaign_gate_pass')),
            'global_publication_ready_geometry_layer':bool(d.get('publication_ready_geometry_layer')),
            'topology_count':d.get('topology_count'), 'failed_topology_count':d.get('failed_topology_count'), 'release_json_sha256':_sha256_file(self.out/'RELEASE.json'), 'loader_sha256':fh('pklsa_builder/io_geometry.py'), 'hashing_sha256':fh('pklsa_builder/hashing.py'), 'native_source_sha256':fh('cpp/pklsa_native.cpp'),
            'policy':'Global all-topology campaign status is recorded but not used to admit a carrier; each topology/carrier must pass the local fail-closed contract.'
        }

    def discover(self, policy: dict, topology_include: Iterable[str] | None=None, max_topologies: int=0, max_carriers_per_topology: int=0):
        release=self.release_checks()
        if not release['pass']:
            raise RuntimeError(f'PKLSA release preflight failed: {release}')
        includes=set(topology_include or [])
        result=[]; rejected=[]; topo_count=0
        for td in _iter_topology_dirs(self.out):
            if includes and td.name not in includes: continue
            q=td/'qualification'
            summary=q/'summary.json'; metrics=q/'geometry_metrics.json'; indep=q/'source_independence.json'
            if not indep.exists(): indep=q/'source_independence_ledger.json'
            if not (summary.exists() and metrics.exists() and indep.exists()):
                rejected.append({'topology_h':hashlib.sha256(('topology|'+td.name).encode()).hexdigest()[:16],'reason':'missing_qualification_contract'}); continue
            sm=_read_json(summary)
            if policy.get('require_topology_qualification_gate',True) and not sm.get('qualification_gate_pass',False):
                rejected.append({'topology_h':hashlib.sha256(('topology|'+td.name).encode()).hexdigest()[:16],'reason':'topology_qualification_gate_fail'}); continue
            mm=_read_json(metrics); ii=_read_json(indep)
            qh=hashlib.sha256()
            for qp in (summary,metrics,indep): qh.update(qp.read_bytes()); qh.update(b'\0')
            qualification_contract_sha256=qh.hexdigest()
            m_by={x['carrier_id']:x for x in mm.get('carriers',[])}
            i_by={x['carrier_id']:x for x in ii.get('entries',[])}
            e_by={}
            for ep in _carrier_envelopes(td):
                try:
                    ed=_read_json(ep); c=ed.get('carrier',ed); cid=c.get('carrier_id')
                    if cid: e_by[cid]=(ep,ed)
                except Exception:
                    continue
            candidates=[]
            for cid,m in m_by.items():
                ind=i_by.get(cid); ep_ed=e_by.get(cid)
                if ind is None or ep_ed is None:
                    rejected.append({'topology_h':hashlib.sha256(('topology|'+td.name).encode()).hexdigest()[:16],'carrier_h':hashlib.sha256(cid.encode()).hexdigest()[:12],'reason':'missing_independence_or_envelope'}); continue
                ep,ed=ep_ed; c=ed.get('carrier',ed)
                reasons=[]
                if policy.get('require_literature_hard_gate',True) and not m.get('literature_hard_gate_pass',False): reasons.append('literature_hard_gate_fail')
                eic=ind.get('evidence_independence_class')
                if policy.get('exclude_mirrors',True) and eic in ('BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT','MIRROR_NOT_INDEPENDENT'): reasons.append('mirror_not_independent')
                if policy.get('exclude_raw_duplicates',True) and ind.get('raw_duplicate_of'): reasons.append('raw_duplicate')
                if policy.get('exclude_geometry_duplicates',True) and ind.get('geometry_duplicate_of'): reasons.append('geometry_duplicate')
                if reasons:
                    rejected.append({'topology_h':hashlib.sha256(('topology|'+td.name).encode()).hexdigest()[:16],'carrier_h':hashlib.sha256(cid.encode()).hexdigest()[:12],'reason':'+'.join(reasons)}); continue
                fm=m.get('finest_metrics',{}); sc=m.get('scale_context',{})
                candidates.append(PKLSACarrier(
                    topology_id=str(c.get('topology_id',td.name)), carrier_id=cid, catalog_id=c.get('catalog_id'), source_family=c.get('source_family'),
                    provider_group=ind.get('provider_group') or c.get('provider_group'), method_group=ind.get('method_group') or c.get('method_group'),
                    lineage_group=ind.get('lineage_group') or c.get('lineage_group'), independence_group=ind.get('independence_group') or c.get('independence_group'),
                    evidence_independence_class=eic, source_role=c.get('source_role'), representation=c.get('representation') or c.get('metadata',{}).get('representation_hint'),
                    source_path=str(c.get('source_path')), raw_sha256=str(c.get('raw_sha256')), geometry_sha256=str(ed.get('geometry_sha256')),
                    literature_hard_gate_pass=bool(m.get('literature_hard_gate_pass')), finest_resolution=m.get('finest_resolution'),
                    reach=fm.get('reach'), thickness=fm.get('thickness') or fm.get('Thi'), normalization_scale=float(sc.get('normalization_scale',1.0)),
                    observable_status=m.get('observable_status',{}), geometry_duplicate_of=ind.get('geometry_duplicate_of'), raw_duplicate_of=ind.get('raw_duplicate_of'),
                    envelope_sha256=_sha256_file(ep), qualification_contract_sha256=qualification_contract_sha256, envelope_path=str(ep), topology_dir=str(td)))
            if not candidates: continue
            # Deterministic, provenance-first ordering; never score by a physics observable.
            candidates.sort(key=lambda c:((c.evidence_independence_class!='UPSTREAM_REFERENCE'),str(c.provider_group),str(c.independence_group),str(c.carrier_id)))
            if max_carriers_per_topology>0: candidates=candidates[:max_carriers_per_topology]
            result.extend(candidates); topo_count+=1
            if max_topologies>0 and topo_count>=max_topologies: break
        
        class_counts={}
        for x in result: class_counts[x.evidence_independence_class or 'UNSPECIFIED']=class_counts.get(x.evidence_independence_class or 'UNSPECIFIED',0)+1
        return result,{'release':release,'admitted':len(result),'admitted_topologies':len(set(x.topology_id for x in result)),'evidence_class_counts':class_counts,'rejected_count':len(rejected),'rejected':rejected[:200],'rejected_truncated':len(rejected)>200}

    def load_verified(self, carrier: PKLSACarrier, fseries_n=4096):
        p=_remap_source_path(carrier.source_path,self.workbench)
        raw=_sha256_file(p)
        if raw.lower()!=carrier.raw_sha256.lower():
            raise ValueError(f'raw SHA mismatch for carrier {carrier.carrier_id}')
        comps=self.io.load_geometry(p,representation=carrier.representation,fseries_n=fseries_n)
        comps=[np.ascontiguousarray(np.asarray(c,float)[:,:3]) for c in comps]
        gh=self.hashing.geometry_sha256(comps)
        if gh.lower()!=carrier.geometry_sha256.lower():
            raise ValueError(f'PKLSA geometry SHA mismatch for carrier {carrier.carrier_id}')
        # Apply the E010 declared global translation/scale convention. Relative link placement remains unchanged.
        allp=np.vstack(comps); ctr=np.mean(allp,axis=0); s=float(carrier.normalization_scale)
        norm=[np.ascontiguousarray((c-ctr)*s,float) for c in comps]
        return norm,{'raw_sha256_verified':True,'geometry_sha256_verified':True,'normalization_scale':s,'component_count':len(norm)}

    def exact_linking(self,A,B):
        if self.native is not None and hasattr(self.native,'linking_number_exact'):
            return float(self.native.linking_number_exact(np.ascontiguousarray(A,float),np.ascontiguousarray(B,float))), 'pklsa_cpp_exact'
        return float(linking_number_exact_python(A,B)), 'python_exact_solid_angle'


def _triangle_solid_angle(a,b,c):
    na=np.linalg.norm(a); nb=np.linalg.norm(b); nc=np.linalg.norm(c)
    if min(na,nb,nc)<=1e-15: return 0.0
    num=float(np.dot(a,np.cross(b,c)))
    den=float(na*nb*nc + np.dot(a,b)*nc + np.dot(b,c)*na + np.dot(c,a)*nb)
    return 2.0*np.arctan2(num,den)


def _segment_pair_solid_angle(a0,a1,b0,b1):
    r00=b0-a0; r10=b0-a1; r11=b1-a1; r01=b1-a0
    return _triangle_solid_angle(r00,r10,r11)+_triangle_solid_angle(r00,r11,r01)


def linking_number_exact_python(A,B):
    A=np.asarray(A,float); B=np.asarray(B,float); s=0.0
    for i in range(len(A)):
        a0=A[i]; a1=A[(i+1)%len(A)]
        for j in range(len(B)):
            s += _segment_pair_solid_angle(a0,a1,B[j],B[(j+1)%len(B)])
    return s/(4*np.pi)
