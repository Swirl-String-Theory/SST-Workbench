from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, hashlib, os

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PACKAGE_ROOT / 'configs' / 'source_contract_v1.json'

@dataclass(frozen=True)
class ResolvedSource:
    source_id: str
    path: str | None
    status: str
    role: str
    kind: str
    provider_group: str | None
    method_group: str | None
    admit_geometry: bool
    required: bool
    resolution_mode: str | None = None

class Workbench:
    def __init__(self, root: str | Path, contract: str | Path = DEFAULT_CONTRACT):
        self.root = Path(root).resolve()
        self.contract_path = Path(contract).resolve()
        if not self.root.exists():
            raise FileNotFoundError(self.root)
        self.contract = json.loads(self.contract_path.read_text(encoding='utf-8'))

    @classmethod
    def open(cls, root: str | Path, contract: str | Path = DEFAULT_CONTRACT):
        return cls(root, contract)

    def _resolve_one(self, spec: dict) -> ResolvedSource:
        for rel in spec.get('canonical_paths', []):
            p = self.root / rel
            if p.exists():
                return ResolvedSource(spec['source_id'], str(p), 'RESOLVED', spec.get('role',''), spec.get('kind',''), spec.get('provider_group'), spec.get('method_group'), bool(spec.get('admit_geometry')), bool(spec.get('required')), 'canonical')
        # Explicit legacy aliases only; never auto-admit heuristic hits.
        for alias in spec.get('legacy_globs', []):
            direct = self.root / alias
            if direct.exists():
                return ResolvedSource(spec['source_id'], str(direct), 'RESOLVED_LEGACY_ALIAS', spec.get('role',''), spec.get('kind',''), spec.get('provider_group'), spec.get('method_group'), bool(spec.get('admit_geometry')), bool(spec.get('required')), 'legacy')
            # basename search for moved legacy folders
            if '/' not in alias and '\\' not in alias:
                hits = [p for p in self.root.rglob(alias) if p.exists()]
                if len(hits) == 1:
                    return ResolvedSource(spec['source_id'], str(hits[0]), 'RESOLVED_LEGACY_SEARCH', spec.get('role',''), spec.get('kind',''), spec.get('provider_group'), spec.get('method_group'), bool(spec.get('admit_geometry')), bool(spec.get('required')), 'legacy-search')
        status = 'REQUIRED_SOURCE_MISSING' if spec.get('required') else 'OPTIONAL_SOURCE_MISSING'
        return ResolvedSource(spec['source_id'], None, status, spec.get('role',''), spec.get('kind',''), spec.get('provider_group'), spec.get('method_group'), bool(spec.get('admit_geometry')), bool(spec.get('required')), None)

    def resolve_sources(self) -> list[ResolvedSource]:
        return [self._resolve_one(s) for s in self.contract.get('sources', [])]

    def registry_paths(self) -> dict:
        reg = self.contract.get('registry', {})
        return {k: str(self.root / v) for k, v in reg.items()}

    def doctor(self) -> dict:
        src = self.resolve_sources()
        required = [s for s in src if s.required]
        missing = [s for s in required if not s.path]
        return {
            'schema': 'SST-PKLSA-DOCTOR-1',
            'workbench_root': str(self.root),
            'marker_present': (self.root / '.sst-workbench-root').exists(),
            'registry': self.registry_paths(),
            'source_contract': str(self.contract_path),
            'coverage': {
                'required_total': len(required),
                'required_resolved': len(required) - len(missing),
                'required_missing': len(missing),
                'pass': len(missing) == 0,
            },
            'sources': [s.__dict__ for s in src],
        }

    def inventory(self, deep_hash: bool = False) -> dict:
        records=[]
        for src in self.resolve_sources():
            if not src.path:
                records.append({'source_id':src.source_id,'status':src.status,'path':None})
                continue
            p=Path(src.path)
            files=[p] if p.is_file() else [x for x in p.rglob('*') if x.is_file() and '.venv' not in x.parts and '__pycache__' not in x.parts]
            total=0
            hashes=[]
            for f in files:
                try: total += f.stat().st_size
                except OSError: pass
                if deep_hash:
                    h=hashlib.sha256()
                    try:
                        with f.open('rb') as fh:
                            for chunk in iter(lambda: fh.read(1024*1024), b''): h.update(chunk)
                        hashes.append({'path':str(f),'sha256':h.hexdigest()})
                    except OSError: pass
            records.append({'source_id':src.source_id,'status':src.status,'path':str(p),'file_count':len(files),'bytes':total,'files':hashes if deep_hash else None})
        return {'schema':'SST-PKLSA-INVENTORY-1','workbench_root':str(self.root),'deep_hash':deep_hash,'sources':records}

    def bridges(self) -> dict:
        # Explicitly report the current namespace collision risk rather than importing either provider blindly.
        candidates=[]
        for rel in [
            '02_libraries/A_knot_libraries/A001_knot_geometry_library',
            '02_libraries/A_knot_libraries/A002_knot_library',
        ]:
            p=self.root/rel
            if p.exists():
                providers=list(p.rglob('sst_knotlib'))
                candidates.append({'catalog_path':rel,'sst_knotlib_dirs':[str(x) for x in providers]})
        total=sum(len(x['sst_knotlib_dirs']) for x in candidates)
        return {'schema':'SST-PKLSA-BRIDGES-1','providers':candidates,'top_level_sst_knotlib_count':total,'ambiguous':total>1,'policy':'Do not place multiple sst_knotlib providers on PYTHONPATH simultaneously; PKLSA keeps provider provenance explicit.'}
