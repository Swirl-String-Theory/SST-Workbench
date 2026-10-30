"""Immutable E010 v0.4.0 atlas -> explicit falsifier dataset contract.

Works with an extracted E010 portable payload *or* the original portable ZIP.
Uses the actual, unchanged sst_pklsa reader, including its raw/parsed hash checks.
Lazy ZIP materialization extracts only original geometry members selected for loading.
No automatic physics admission, normalization, topology proof, or dynamics.
"""
from __future__ import annotations
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import zipfile
from typing import Iterable

import numpy as np

EXPECTED_INDEX_SHA256 = '70af49e67406e26187607eef5c624a88989e8fd5938d0c6f42ba3b2d23b75341'
EXPECTED_ZIP_SHA256 = '2051ad2e9a0b51857197e6688b09d9be48bd562c01ec0e7613eddfebeb174d82'
INDEX_SCHEMA = 'PKLSA-COMBINED-SEED-INDEX-1'
DATASET_SCHEMA = 'SST-ATLAS-CONSUMER-DATASET-1'
MODULE_DIRS = ('sst_pklsa/', 'pklsa_builder/')

# Frozen upstream parser module hashes from the published E010 v0.4.0 ZIP.
# Directory-based operation does not trust an edited parser just because its index matches.
UPSTREAM_MODULE_SHA256 = {
    'pklsa_builder/__init__.py': '43b66f43c7894d9bd92c29297820967d8e918da857da86a3c2d53322857295f6',
    'pklsa_builder/fseries.py': 'd4746c49f174b64d1150c62d1ec073017651041a739019888e252ace3d55a43c',
    'pklsa_builder/gilbert.py': '7f53621af6cd10f4f4bf14b6dd8dd882db14659d85614e525b8e19d4e6e9b2c4',
    'pklsa_builder/hashing.py': '6c6a886f060cff2edef897f7798b8e253c1c976f43fd4d95c21264c266d555a4',
    'pklsa_builder/io_geometry.py': '597d5e3b06b0a91884edd2a7ffa99b2c7160940c68c9da39addb0d0c32796d26',
    'pklsa_builder/models.py': '280b0d965040c922ea122654b86257f168a1742f7da18e19a98e69a4103d0170',
    'sst_pklsa/__init__.py': 'd100cfb17d5c3f6393e4e91b114393957693ee0a7b3c54aaa276c17c6b7355fa',
    'sst_pklsa/combined_atlas.py': '8740a35aa1228b093395b2de183f1beb101f9f695607f4ac36512e9bf326a2ad',
}

class AtlasContractError(RuntimeError):
    """An atlas pin, hash, schema or output contract is violated."""

class AdmissionError(AtlasContractError):
    """Selection or export was not explicitly permitted."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def safe_relpath(relative: str) -> PurePosixPath:
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise AtlasContractError('Unsafe atlas relative path')
    p = PurePosixPath(relative)
    if p.is_absolute() or any(s in ('', '.', '..') for s in relative.split('/')):
        raise AtlasContractError(f'Unsafe atlas path: {relative}')
    return p


def resample_closed_arclength(component: np.ndarray, count: int) -> np.ndarray:
    """Numerical interpolation only; NOT independently resolved geometric data.

    Treat final point as connected to first. Identical endpoint is rejected rather
    than quietly assuming how the upstream polygon should be interpreted.
    """
    a = np.asarray(component, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3 or len(a) < 3 or not np.isfinite(a).all():
        raise AtlasContractError('Expected finite Nx3 closed polygon')
    if count < 3:
        raise AtlasContractError('Resampling requires >=3 vertices')
    edges = np.linalg.norm(np.roll(a, -1, axis=0) - a, axis=1)
    if not np.isfinite(edges).all() or np.any(edges <= 1e-14):
        raise AtlasContractError('Degenerate polygon edge; do not interpolate silently')
    arclen = np.r_[0.0, np.cumsum(edges)]
    t = np.linspace(0.0, arclen[-1], count, endpoint=False)
    full = np.concatenate((a, a[:1]), axis=0)
    result = np.stack([np.interp(t, arclen, full[:, j]) for j in range(3)], axis=1)
    return result


def geometry_summary(components: list[np.ndarray]) -> dict:
    summaries=[]
    for c in components:
        a=np.asarray(c,dtype=np.float64)
        if a.ndim!=2 or a.shape[1]!=3 or len(a)<3 or not np.isfinite(a).all():
            raise AtlasContractError('Invalid geometry')
        ed=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
        if float(ed.min())<=1e-14: raise AtlasContractError('Degenerate polygon edge')
        summaries.append({
            'point_count': int(len(a)), 'polygon_length_source_units': float(ed.sum()),
            'min_segment_source_units':float(ed.min()),
            'median_segment_source_units':float(np.median(ed)),
            'max_segment_source_units':float(ed.max()),
            'bounds_min':a.min(axis=0).tolist(),'bounds_max':a.max(axis=0).tolist(),
            'polygon_closed_by_periodic_last_to_first_edge':True
        })
    return {'component_count':len(summaries),'components':summaries,
            'geometric_qualification':'POLYGON_STRUCTURE_ONLY',
            'finite_core':'NOT_CERTIFIED','full_isotopy':'NOT_CERTIFIED',
            'dynamics':'NOT_RUN'}


class AtlasBridge:
    """Read-only bridge to pinned E010 v0.4.0.

    Use `with AtlasBridge(path) as bridge:` to clean up the ZIP temporary cache.
    The adapter never edits or overwrites the E010 payload.
    """
    def __init__(self, path, *, expected_index_sha256=EXPECTED_INDEX_SHA256,
                 expected_zip_sha256=EXPECTED_ZIP_SHA256):
        self.input_path = Path(path).expanduser().resolve()
        self._tmp = None
        self._zip = None
        self._zip_prefix = None
        self._zip_members = set()
        self._reader = None
        self._reader_module_root = None
        self._expected_index = expected_index_sha256
        if not self.input_path.exists(): raise AtlasContractError(f'Atlas not found: {self.input_path}')
        try:
            if self.input_path.is_file():
                if self.input_path.suffix.lower() != '.zip':
                    raise AtlasContractError('Atlas must be extracted directory or portable ZIP')
                actual_zip = sha256_file(self.input_path)
                if expected_zip_sha256 and actual_zip != expected_zip_sha256:
                    raise AtlasContractError('Portable ZIP SHA-256 does not match pinned E010 v0.4.0')
                self._zip_sha = actual_zip
                self._zip = zipfile.ZipFile(self.input_path)
                names=self._zip.namelist()
                if len(names)!=len(set(names)):
                    raise AtlasContractError('Duplicate ZIP member names')
                roots = {n.split('/')[0] for n in names if n.endswith('COMBINED_INDEX.json') and n.count('/')==1}
                if len(roots)!=1: raise AtlasContractError('Missing/ambiguous E010 payload root')
                self._zip_prefix = next(iter(roots)) + '/'
                for n in names:
                    if not n.startswith(self._zip_prefix): raise AtlasContractError('Unexpected ZIP root member')
                    relative=n[len(self._zip_prefix):]
                    if relative and not relative.endswith('/'): safe_relpath(relative)
                    self._zip_members.add(relative)
                self._tmp=tempfile.TemporaryDirectory(prefix='e010_bridge_')
                self.root=Path(self._tmp.name)
                self._materialize('COMBINED_INDEX.json')
                # Import upstream readers unchanged; these are the original E010 Python modules.
                for relative in self._zip_members:
                    if relative.endswith('.py') and relative.startswith(MODULE_DIRS):
                        self._materialize(relative)
            else:
                self.root=self.input_path
                self._zip_sha=None
            index_file=self.root/'COMBINED_INDEX.json'
            if not index_file.is_file(): raise AtlasContractError('COMBINED_INDEX.json missing')
            self.index_sha = sha256_file(index_file)
            if expected_index_sha256 and self.index_sha != expected_index_sha256:
                raise AtlasContractError('COMBINED_INDEX.json does not match pinned E010 v0.4.0')
            self.index=json.loads(index_file.read_text(encoding='utf-8'))
            if self.index.get('schema')!=INDEX_SCHEMA: raise AtlasContractError('Unsupported E010 index schema')
            if self.index.get('no_scientific_promotion') is not True:
                raise AtlasContractError('Atlas unexpectedly asserts scientific promotion')
            self.records={r['id']:r for r in self.index['records']}
            if len(self.records)!=len(self.index['records']) or len(self.records)!=self.index['record_count']:
                raise AtlasContractError('Duplicate IDs or index count mismatch')
            for relative, expected in UPSTREAM_MODULE_SHA256.items():
                module_file=self.root/relative
                if not module_file.is_file() or sha256_file(module_file)!=expected:
                    raise AtlasContractError('Upstream parser module mismatch: '+relative)
            self._load_original_reader()
        except BaseException:
            self.close()
            raise

    def _materialize(self, relative):
        if self._zip is None:return
        safe_relpath(relative)
        if relative not in self._zip_members:
            raise AtlasContractError(f'Missing source member: {relative}')
        dest=(self.root/relative).resolve()
        if not dest.is_relative_to(self.root.resolve()):
            raise AtlasContractError('ZIP extraction path escapes temporary directory')
        if dest.is_file():return
        dest.parent.mkdir(parents=True,exist_ok=True)
        with self._zip.open(self._zip_prefix+relative) as src, dest.open('xb') as dst:
            shutil.copyfileobj(src,dst)

    def _load_original_reader(self):
        root_text=str(self.root.resolve())
        # Prevent mixing reader modules originating from two separate atlas versions.
        for module_name in list(sys.modules):
            if module_name.split('.')[0] in ('sst_pklsa','pklsa_builder'):
                module=sys.modules[module_name]
                filename=getattr(module,'__file__',None)
                if filename is not None and not Path(filename).resolve().is_relative_to(self.root.resolve()):
                    raise AtlasContractError('Different upstream PKLSA reader already imported; use a fresh process')
        if root_text not in sys.path: sys.path.insert(0,root_text)
        from sst_pklsa import CombinedSeedAtlas
        self._reader=CombinedSeedAtlas(self.root)
        self._reader_module_root=self.root.resolve()

    def close(self):
        # Remove only upstream modules resolved from this bridge's atlas root.
        # The bridge does not support two distinct atlas versions concurrently.
        module_root = getattr(self, '_reader_module_root', None)
        if module_root is not None:
            for name in list(sys.modules):
                if name.split('.')[0] in ('sst_pklsa', 'pklsa_builder'):
                    module = sys.modules[name]
                    filename = getattr(module, '__file__', None)
                    if filename and Path(filename).resolve().is_relative_to(module_root):
                        del sys.modules[name]
            if str(module_root) in sys.path: sys.path.remove(str(module_root))
            self._reader_module_root = None
        self._reader = None
        if getattr(self,'_zip',None) is not None:
            self._zip.close();self._zip=None
        if getattr(self,'_tmp',None) is not None:
            self._tmp.cleanup();self._tmp=None

    def __enter__(self): return self
    def __exit__(self,exc_type,exc,tb):self.close()

    def _ensure_active(self):
        if self._reader is None or (self.input_path.is_file() and self._tmp is None):
            raise AtlasContractError('Bridge is closed')

    def _ensure_allowed(self, rec, allow_research):
        if rec['research_only'] and not allow_research:
            raise AdmissionError('Ruban research geometry needs explicit allow_research=True')

    def describe(self, identity, *, allow_research=False):
        self._ensure_active()
        if identity not in self.records:raise KeyError(identity)
        rec=self.records[identity]
        self._ensure_allowed(rec,allow_research)
        return deepcopy(rec)

    def query(self, *, ids=None, topology=None, embedding=None, collection=None, variant=None,
              provider=None, independence_group=None, component_count=None,
              min_points=None, b0_min=None, b0_max=None, historical_status=None,
              allow_research=False, unique_geometry=False, limit=None):
        """Pure metadata selection; no geometry I/O. Deterministic ID ordering."""
        self._ensure_active()
        requested=set(ids) if ids is not None else None
        if requested is not None:
            missing=requested-self.records.keys()
            if missing:raise KeyError('Unknown record IDs: '+', '.join(sorted(missing)[:10]))
        accepted=[];geometry_seen=set()
        for ident,rec in sorted(self.records.items()):
            if requested is not None and ident not in requested:continue
            if rec['research_only'] and not allow_research:
                if requested is not None: raise AdmissionError('Requested research record requires explicit opt-in: '+ident)
                continue
            if topology is not None and rec.get('topology_id')!=topology:continue
            if embedding is not None and rec.get('parametric_embedding')!=embedding:continue
            if collection is not None and rec['collection']!=collection:continue
            if variant is not None and rec.get('variant','historical')!=variant:continue
            if provider is not None and rec.get('source_provider')!=provider:continue
            if independence_group is not None and rec.get('source_independence_group')!=independence_group:continue
            if component_count is not None and rec['component_count']!=component_count:continue
            if min_points is not None and min(rec['component_points'])<min_points:continue
            if historical_status is not None and rec.get('historical_topology_status')!=historical_status:continue
            b=rec.get('B0')
            if b0_min is not None and (b is None or b<b0_min-1e-12):continue
            if b0_max is not None and (b is None or b>b0_max+1e-12):continue
            if unique_geometry:
                h=rec['geometry_sha256']
                if h in geometry_seen:continue
                geometry_seen.add(h)
            accepted.append(ident)
            if limit is not None and len(accepted)>=limit:break
        return accepted

    def load(self, identity, *, allow_research=False):
        self._ensure_active()
        rec=self.describe(identity,allow_research=allow_research)
        if self._zip is not None:
            if rec['collection']=='ruban_v036':
                for comp in rec['components']: self._materialize(comp['path'])
            else:
                self._materialize(rec['raw_path'])
        return self._reader.load(identity,allow_research=allow_research)

    def source_summary(self, identity, *, allow_research=False):
        rec=self.describe(identity,allow_research=allow_research)
        fields=('id','collection','topology_id','topology_mapping_status','parametric_embedding',
                'B0','R0','variant','parent_id','source_seed_id','source_provider','source_document','original_carrier_id',
                'source_independence_group','component_count','component_points',
                'geometry_sha256','raw_sha256','research_only','production_admission',
                'historical_topology_status','units','gates','finite_core_qualified',
                'polygon_embedding_certificate','dynamic_stability','components','raw_path')
        summary={k:deepcopy(rec.get(k)) for k in fields if k in rec}
        if rec['collection']=='historical_v031':
            carrier=rec['carrier']
            summary['historical_carrier']={k:deepcopy(carrier.get(k)) for k in
                ('representation','source_family','source_role','lineage_group',
                 'independence_group','parent_carrier_id','parent_source_family','catalog_id')}
        return summary

    def export_dataset(self, ids: Iterable[str], output, *, allow_research=False,
                       resample_points=None, scale=1.0, consumer='unspecified',
                       max_records=100, duplicate_policy='preserve'):
        """Create-only export. No overwrite, even on failure. Returns manifest path.

        Resampling is tagged as interpolation. Scaling is source-coordinate scaling,
        not an automatic SI conversion. Consumer qualification remains NOT_GRANTED.
        """
        self._ensure_active()
        ids=list(ids)
        if not ids or len(ids)>max_records:
            raise AdmissionError(f'Expected 1..{max_records} selected IDs; specify --max-records explicitly')
        if len(set(ids))!=len(ids):raise AtlasContractError('Duplicate selection IDs')
        if duplicate_policy not in ('preserve','reject'):
            raise AtlasContractError('Unknown duplicate policy')
        if resample_points is not None and (not isinstance(resample_points,int) or resample_points<3):
            raise AtlasContractError('Invalid resample points')
        if not math.isfinite(scale) or scale<=0:raise AtlasContractError('Scale must be finite >0')
        if not isinstance(consumer,str) or not consumer.strip() or len(consumer)>120:
            raise AtlasContractError('Invalid consumer label')
        target=Path(output).expanduser().resolve()
        if target.exists():raise AtlasContractError('Export refuses existing output path: '+str(target))
        if target == self.root or target.is_relative_to(self.root.resolve()):
            raise AtlasContractError('Do not export inside the original atlas')
        # Reserve target non-destructively, then populate. Any failed export is removed.
        target.mkdir(parents=True,exist_ok=False)
        try:
            items=[];files={};seen={}
            for identity in ids:
                rec=self.describe(identity,allow_research=allow_research)
                if duplicate_policy=='reject' and rec['geometry_sha256'] in seen:
                    raise AtlasContractError('Identical ordered float64 geometry in export: '+identity)
                seen[rec['geometry_sha256']]=identity
                native=self.load(identity,allow_research=allow_research)
                exports=[]
                for a in native:
                    x=resample_closed_arclength(a,resample_points) if resample_points is not None else np.asarray(a).copy()
                    exports.append(x*scale)
                sub=target/'seeds'/identity
                sub.mkdir(parents=True,exist_ok=False)
                members=[]
                for j,coords in enumerate(exports):
                    filename=f'component_{j:03d}.xyz'
                    dest=sub/filename
                    np.savetxt(dest,coords,fmt='%.17g')
                    relative=dest.relative_to(target).as_posix()
                    files[relative]=sha256_file(dest)
                    members.append({'component_index':j,'relative_path':relative,'sha256':files[relative],
                                    'native_point_count':int(len(native[j])),
                                    'exported_point_count':int(len(coords))})
                items.append({
                    'atlas_record':self.source_summary(identity,allow_research=allow_research),
                    'exported_components':members,
                    'geometry_metrics':geometry_summary(exports),
                    'transforms':{
                        'arclength_interpolation':resample_points is not None,
                        'requested_points_per_component':resample_points,
                        'source_coordinate_multiplication':scale,
                        'SI_units_established':False,
                        'topology_preservation_certified':False,
                        'note':'Derived coordinates are not an independent measured source.' if resample_points is not None else 'Native source coordinates, without interpolation.'
                    },
                    'consumer_science_admission':'NOT_GRANTED',
                })
            manifest={
                'schema':DATASET_SCHEMA,'adapter_version':'0.1.0',
                'consumer':consumer,'atlas':{
                    'version':'v0.4.0','source_name':self.input_path.name,
                    'index_sha256':self.index_sha,'portable_zip_sha256':self._zip_sha or EXPECTED_ZIP_SHA256,
                    'record_count':self.index['record_count'],
                    'immutable_source':'YES','scientific_gate':'NOT_RUN'},
                'selection':{'ids':ids,'duplicate_policy':duplicate_policy,
                             'allow_research':allow_research},
                'coordinate_policy':{
                    'source_native_units_preserved':scale==1.0,
                    'automatic_SI_conversion':False,
                    'external_physical_scale_required':True},
                'qualification':{
                    'source_integrity':'VERIFIED_PER_SELECTED_RECORD',
                    'export_readback':'PENDING_AT_MANIFEST_WRITE',
                    'scientific_admission':'NOT_GRANTED',
                    'dynamical_stability':'NOT_TESTED',
                    'finite_core':'NOT_CERTIFIED',
                    'topology':'SOURCE_LABEL_ONLY_UNLESS_SEPARATELY_PROVEN'},
                'records':items,'files_sha256':files}
            # Verify every exported CSV before publication (float64 roundtrip)
            for item in items:
                for c in item['exported_components']:
                    path=target/c['relative_path']
                    read=np.loadtxt(path,dtype=np.float64,ndmin=2)
                    if read.shape!=(c['exported_point_count'],3) or not np.isfinite(read).all():
                        raise AtlasContractError('Export readback shape/finite check failed')
                    if sha256_file(path)!=c['sha256']:
                        raise AtlasContractError('Export readback hash failed')
            manifest['qualification']['export_readback']='PASS_FINITE_SHAPE_AND_HASH'
            blob=canonical_json_bytes(manifest)
            path=target/'DATASET_MANIFEST.json'
            path.write_bytes(blob)
            (target/'DATASET_MANIFEST.json.sha256').write_text(sha256_bytes(blob)+'  DATASET_MANIFEST.json\n',encoding='ascii')
            return path
        except BaseException:
            shutil.rmtree(target,ignore_errors=True)
            raise


def verify_export(target):
    target=Path(target).expanduser().resolve()
    manifest_path=target/'DATASET_MANIFEST.json'
    digest=(target/'DATASET_MANIFEST.json.sha256').read_text(encoding='ascii').split()[0]
    if sha256_file(manifest_path)!=digest:raise AtlasContractError('Dataset manifest SHA mismatch')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema')!=DATASET_SCHEMA:raise AtlasContractError('Dataset schema mismatch')
    expected=set(manifest['files_sha256'])|{'DATASET_MANIFEST.json','DATASET_MANIFEST.json.sha256'}
    present={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
    if expected!=present:raise AtlasContractError('Extra/missing exported files')
    for rel,expected_sha in manifest['files_sha256'].items():
        path=(target/safe_relpath(rel)).resolve()
        if not path.is_relative_to(target) or sha256_file(path)!=expected_sha:
            raise AtlasContractError('Dataset file hash mismatch: '+rel)
    if manifest['qualification']['scientific_admission']!='NOT_GRANTED':
        raise AtlasContractError('Unexpected scientific qualification')
    return {'status':'PASS_DATASET_INTEGRITY_ONLY','records':len(manifest['records']),
            'files':len(manifest['files_sha256']),'manifest_sha256':digest,
            'scientific':'NOT_GRANTED'}
