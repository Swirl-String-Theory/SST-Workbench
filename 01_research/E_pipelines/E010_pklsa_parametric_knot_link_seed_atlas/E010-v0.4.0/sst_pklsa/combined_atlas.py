"""Portable reader using the byte-preserved v0.3.1 geometry parsers.

Loads native coordinates without normalization, relaxation or scientific promotion.
Hash equality is exact ordered float64 geometry equality, not isotopy equivalence.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath

import numpy as np
from pklsa_builder.models import Carrier
from pklsa_builder.io_geometry import load_geometry
from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_components
from pklsa_builder.hashing import geometry_sha256

SCHEMA = 'PKLSA-COMBINED-SEED-INDEX-1'


class AtlasIntegrityError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise AtlasIntegrityError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, relative):
    root = Path(root).resolve()
    need(isinstance(relative, str) and relative != '', 'Empty/non-string path')
    p = PurePosixPath(relative)
    need(not p.is_absolute() and '\\' not in relative and ':' not in relative
         and all(part not in ('', '.', '..') for part in relative.split('/')), 'Unsafe path: '+relative)
    result = (root / p).resolve()
    need(result.is_relative_to(root) and result != root, 'Escaping path: '+relative)
    return result


def valid_components(parts, expected_count=None, expected_points=None):
    need(isinstance(parts, list) and len(parts) > 0, 'No components')
    if expected_count is not None:
        need(len(parts) == expected_count, 'Component count mismatch')
    for i, a in enumerate(parts):
        need(a.ndim == 2 and a.shape[1] == 3 and len(a) >= 3 and np.isfinite(a).all(),
             f'Invalid finite Nx3 component {i}')
        if expected_points is not None:
            need(len(a) == expected_points[i], f'Point count mismatch: component {i}')
    return parts


def load_historical(carrier, local_path):
    c = Carrier.from_dict({**carrier, 'source_path': str(local_path)})
    if c.representation == 'gilbert_ab_record':
        record = find_gilbert_record(c.source_path, c.topology_id)
        parts = sample_gilbert_components(record, n=max(4096, c.metadata.get('native_sample_n', 4096)))
    else:
        parts = load_geometry(c.source_path, representation=c.representation)
    return valid_components(parts)


def load_ruban_component(path):
    # The upstream generic XYZ parser accepts comments/skips invalid rows. The
    # declared Ruban contract is stricter: exactly 1024 rows of three finite floats.
    strict = np.loadtxt(path, dtype=np.float64, comments=None, ndmin=2)
    valid_components([strict], 1, [1024])
    parts = load_geometry(path, representation='xyz')
    valid_components(parts, 1, [1024])
    need(np.array_equal(strict, parts[0]), 'Strict/raw XYZ parser mismatch')
    return parts[0]


def verify_file_manifest(root):
    root = Path(root)
    manifest = json.loads((root/'FILE_MANIFEST.json').read_text(encoding='utf-8'))
    need(manifest.get('schema') == 'PKLSA-PORTABLE-FILE-MANIFEST-1', 'File manifest schema')
    for relative, expected in manifest['files'].items():
        p = safe_path(root, relative)
        need(p.is_file() and sha(p) == expected, 'File integrity: '+relative)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.name != 'FILE_MANIFEST.json'}
    need(actual == set(manifest['files']), 'Missing or unexpected payload files')
    return len(manifest['files'])


class CombinedSeedAtlas:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.index = json.loads((self.root/'COMBINED_INDEX.json').read_text(encoding='utf-8'))
        need(self.index.get('schema') == SCHEMA, 'Combined index schema mismatch')
        self._records = {}
        for record in self.index['records']:
            identity = record['id']
            need(identity not in self._records, 'Duplicate ID: '+identity)
            need(record['collection'] in ('historical_v031', 'ruban_v036'), 'Unknown collection')
            if record['collection'] == 'ruban_v036':
                need(record['production_admission'] is False and record['research_only'] is True,
                     'Research admission policy violation')
                need(record['gates']['scientific'] == 'NOT_RUN', 'Scientific promotion prohibited')
                need(record['dynamic_stability'] == 'NOT_TESTED', 'Dynamic status changed')
                need(record['state'] == 'RESEARCH_GEOMETRY_UNADMITTED', 'Research state changed')
                need([c['component_index'] for c in record['components']]
                     == list(range(record['component_count'])), 'Component order mismatch')
                for c in record['components']:
                    safe_path(self.root, c['path'])
            else:
                safe_path(self.root, record['raw_path'])
            self._records[identity] = record
        need(len(self._records) == self.index['record_count'], 'Index record count mismatch')
        for record in self._records.values():
            if record['collection'] != 'ruban_v036':
                continue
            parent = record.get('parent_id')
            if record['variant'] == 'perturbed':
                need(parent in self._records and self._records[parent]['variant'] == 'nominal',
                     'Missing nominal parent')
                need(self._records[parent]['source_seed_id'] == record['source_seed_id'], 'Parent identity mismatch')
            else:
                need(record['variant'] == 'nominal' and parent is None, 'Invalid variant')

    def list_ids(self, *, include_research=False, collection=None):
        return [identity for identity, r in self._records.items()
                if (include_research or not r['research_only'])
                and (collection is None or r['collection'] == collection)]

    def describe(self, identity):
        return deepcopy(self._records[identity])

    def provenance(self, identity):
        r = self.describe(identity)
        return {k: r.get(k) for k in ('collection', 'source_seed_id', 'original_carrier_id',
                'source_document', 'source_provider', 'source_independence_group', 'units',
                'variant', 'parent_id', 'geometry_sha256', 'gates', 'research_only',
                'production_admission', 'historical_topology_status')}

    def load(self, identity, *, allow_research=False):
        r = self._records[identity]
        need(not r['research_only'] or allow_research, 'Research geometry requires allow_research=True')
        if r['collection'] == 'historical_v031':
            path = safe_path(self.root, r['raw_path'])
            need(path.is_file() and sha(path) == r['raw_sha256'], 'Historical source hash mismatch')
            parts = load_historical(r['carrier'], path)
        else:
            parts = []
            for c in r['components']:
                path = safe_path(self.root, c['path'])
                need(path.is_file() and sha(path) == c['sha256'], 'Research component hash mismatch')
                parts.append(load_ruban_component(path))
        valid_components(parts, r['component_count'], r['component_points'])
        need(geometry_sha256(parts) == r['geometry_sha256'], 'Parsed geometry hash mismatch')
        return parts
