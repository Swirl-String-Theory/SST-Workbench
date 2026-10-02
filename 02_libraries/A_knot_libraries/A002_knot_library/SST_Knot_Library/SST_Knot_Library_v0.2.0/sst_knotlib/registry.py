from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from importlib import resources
from .models import TopologyReference


def normalize_knot_id(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip().replace(' ', '_').replace('.', '_').replace('-', '_')
    m = re.fullmatch(r'(\d+)_?(\d+)', s)
    if m:
        return f'{int(m.group(1))}_{int(m.group(2))}'
    return s


def infer_knot_id_from_name(name: str) -> str | None:
    raw=str(name).replace('\\','/')
    parts=[p for p in raw.split('/') if p]
    patterns=[r'(?<!\d)(\d{1,2})[._-](\d{1,3})(?!\d)', r'(?i)knot[_-]?(\d{1,2})[_-](\d{1,3})']
    # Search the file token first, then nearest parent outward. This handles .../6.2/ideal.txt.
    for token in reversed(parts):
        for pat in patterns:
            m=re.search(pat,token)
            if m:
                c,n=int(m.group(1)),int(m.group(2))
                if c>=3 and n>=1: return f'{c}_{n}'
    return None



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
