from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path
from importlib import resources
from .models import TopologyReference


def normalize_knot_id(value: str | None) -> str | None:
    """Normalize Alexander-Briggs/Rolfsen knot labels only.

    This function intentionally does not normalize link or torus-family labels.  Keeping the
    namespaces separate prevents a filename such as ``link_4.2.1`` from being silently treated
    as the (nonexistent) knot ``4_2``.
    """
    if value is None:
        return None
    s = str(value).strip().replace(' ', '_').replace('.', '_').replace('-', '_')
    if s.upper().startswith('K'):
        s=s[1:]
    m = re.fullmatch(r'(\d+)_?(\d+)', s)
    if m:
        return f'{int(m.group(1))}_{int(m.group(2))}'
    return s


def _clean_token(token: str) -> str:
    # Numeric parent labels such as '6.2' are topology tokens, not filename extensions.
    low=token.lower()
    known_exts=('.txt','.xyz','.csv','.vect','.knot','.kp','.kpf','.dat')
    return token[:-len(next(e for e in known_exts if low.endswith(e)))] if any(low.endswith(e) for e in known_exts) else token


def infer_topology_hint_from_name(name: str) -> dict | None:
    """Infer an *expected* topology label from a path without certifying it.

    Returned IDs use disjoint namespaces:
      - knots: ``3_1``
      - links encoded as crossing/component/index: ``L4_2_1``
      - torus families: ``T(2,3)``

    The inference is metadata only.  It is never a topology certification.
    """
    raw=str(name).replace('\\','/')
    parts=[p for p in raw.split('/') if p]

    # File token first, then nearest parent outward.
    for token0 in reversed(parts):
        token=_clean_token(token0)
        low=token.lower()
        if re.search(r'(?i)(?:^|[_-])v\d+\.\d+(?:\.\d+)?(?:$|[_-])', token0):
            continue

        # KnotPlot link convention seen in SST datasets: link_<crossings>.<components>.<index>_final
        m=re.search(r'(?i)(?:^|[_-])link[_-]?(\d+)[._-](\d+)[._-](\d+)(?:[_-]|$)', token)
        if m:
            c,components,idx=map(int,m.groups())
            return {
                'kind':'link', 'id':f'L{c}_{components}_{idx}', 'crossings':c,
                'components_hint':components, 'index':idx, 'source':'filename'
            }

        # Explicit torus family.  Do not convert this to a Rolfsen knot label.
        m=re.search(r'(?i)(?:^|[_-])torus[_-]?(\d+)[._-](\d+)(?:[_-]|$)', token)
        if m:
            p,q=map(int,m.groups())
            return {
                'kind':'torus', 'id':f'T({p},{q})', 'p':p, 'q':q,
                'components_hint':math.gcd(p,q), 'source':'filename'
            }

        # Explicit knot prefix.
        m=re.search(r'(?i)(?:^|[_-])knot[_-]?(\d{1,2})[._-](\d{1,3})(?:[_-]|$)', token)
        if m:
            c,n=map(int,m.groups())
            if c>=3 and n>=1:
                return {'kind':'knot','id':f'{c}_{n}','crossings':c,'index':n,'components_hint':1,'source':'filename'}

        # Plain parent/file tokens such as 6.2, 7_4, 3_1_AB.  Require a token boundary.
        m=re.search(r'(?<!\d)(\d{1,2})[._-](\d{1,3})(?!\d)', token)
        if m:
            c,n=map(int,m.groups())
            if c>=3 and n>=1:
                return {'kind':'knot','id':f'{c}_{n}','crossings':c,'index':n,'components_hint':1,'source':'path_token'}
    return None


def infer_knot_id_from_name(name: str) -> str | None:
    """Backward-compatible knot-only inference.

    Link and torus-family filenames now deliberately return ``None`` here.
    Use :func:`infer_topology_hint_from_name` when those namespaces are needed.
    """
    h=infer_topology_hint_from_name(name)
    return h['id'] if h and h.get('kind')=='knot' else None


class KAtlasSnapshot:
    def __init__(self, path: str | Path | None = None, sha256_path: str | Path | None = None, verify: bool = True):
        if path is None:
            path = resources.files('sst_knotlib.data').joinpath('katlas_snapshot_v1.json')
        self.path = Path(str(path))
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if verify:
            if sha256_path is None:
                sha256_path = self.path.with_suffix('.sha256')
            expected = Path(sha256_path).read_text(encoding='ascii').split()[0].strip().lower()
            if self.sha256.lower() != expected:
                raise ValueError(f'KAtlas snapshot SHA-256 mismatch: expected {expected}, got {self.sha256}')
        self.data = json.loads(raw.decode('utf-8'))
        self.snapshot_id = self.data['snapshot_id']
        self.records = self.data['records']

    def ids(self):
        return sorted(self.records, key=lambda s: tuple(int(x) for x in s.split('_') if x.isdigit()))

    def has(self, knot_id: str) -> bool:
        return normalize_knot_id(knot_id) in self.records

    def raw(self, knot_id: str):
        kid = normalize_knot_id(knot_id)
        if kid not in self.records:
            raise KeyError(kid)
        return self.records[kid]

    def get(self, knot_id: str) -> TopologyReference:
        kid = normalize_knot_id(knot_id)
        r = dict(self.raw(kid))
        braid = r.get('braid') or {}
        known = {'name','crossings','components','pd','gauss','dt','conway','braid','determinant','signature','hyperbolic','hyperbolic_volume','source_url','source_accessed'}
        return TopologyReference(
            knot_id=kid,
            source='Knot Atlas offline snapshot',
            source_url=r.get('source_url'),
            snapshot_id=self.snapshot_id,
            crossings=r.get('crossings'),
            components=r.get('components'),
            dt=tuple(r['dt']) if r.get('dt') is not None else None,
            gauss=tuple(r['gauss']) if r.get('gauss') is not None else None,
            pd=tuple(tuple(x) for x in r['pd']) if r.get('pd') is not None else None,
            braid_strands=braid.get('strands'),
            braid_word=tuple(braid.get('word', [])) if braid else None,
            determinant=r.get('determinant'),
            signature=r.get('signature'),
            hyperbolic=r.get('hyperbolic'),
            hyperbolic_volume=r.get('hyperbolic_volume'),
            extra={k:v for k,v in r.items() if k not in known},
        )

    def report(self):
        return {
            'schema': self.data.get('schema'),
            'snapshot_id': self.snapshot_id,
            'sha256': self.sha256,
            'record_count': len(self.records),
            'ids': self.ids(),
            'verified': True,
        }
