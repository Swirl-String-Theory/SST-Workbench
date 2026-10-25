from __future__ import annotations
from pathlib import Path
import csv, re
from .topology_db import lookup_database_records
from .hashing import write_json, sha256_file


def _clean(v):
    if v is None:
        return None
    s = str(v).strip()
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s or None


def load_katlas_record(base_root, topology_id):
    if not base_root:
        return None
    p = Path(base_root) / 'sources' / 'katlas_catalog_extract.csv'
    if not p.exists():
        return None
    with p.open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r.get('id') == topology_id:
                return {'source_file': str(p), 'source_sha256': sha256_file(p), 'record': r}
    return None


def load_topology_database_record(registry_dir, topology_id):
    prefix = 'linkinfo' if str(topology_id).upper().startswith('L') else 'knotinfo'
    hits = lookup_database_records(registry_dir, prefix, topology_id)
    if not hits:
        return None
    return {
        'query_label': topology_id,
        'database': prefix,
        'records': hits,
        'record_count': len(hits),
    }


def build_topology_reference_files(topology_dir, topology_id, base_root, registry_dir):
    d = Path(topology_dir)
    d.mkdir(parents=True, exist_ok=True)
    db = load_topology_database_record(registry_dir, topology_id) if registry_dir else None
    ka = load_katlas_record(base_root, topology_id) if base_root else None

    db_name = 'linkinfo' if str(topology_id).upper().startswith('L') else 'knotinfo'
    write_json(d / f'{db_name}.json', db or {
        'query_label': topology_id, 'database': db_name, 'status': 'UNAVAILABLE_OR_NOT_MAPPED'
    })
    write_json(d / 'topology_database.json', db or {
        'query_label': topology_id, 'database': db_name, 'status': 'UNAVAILABLE_OR_NOT_MAPPED'
    })
    write_json(d / 'katlas.json', ka or {'query_label': topology_id, 'status': 'UNAVAILABLE'})

    # Representation-level comparisons are deliberately conservative. PD/DT/Gauss/braid
    # are not unique textual encodings, so differing strings are not called a mismatch.
    comp = {
        'topology_id': topology_id,
        'database': db_name,
        'fields': {},
        'guard': 'Different PD/DT/Gauss/braid strings are not automatically mismatches; these representations are non-unique and require canonical conversion before equality testing.',
    }
    if db and ka and db.get('records'):
        dbr = db['records'][0]
        dnot = dbr.get('notations', {})
        kar = ka['record']
        for name, kkey in [('PD', 'pd'), ('Gauss', 'gauss'), ('DT', 'dt'), ('Braid', 'braid')]:
            a = _clean(dnot.get(name))
            b = _clean(kar.get(kkey))
            if a is None or b is None:
                status = 'MISSING_ONE_OR_BOTH'
            elif re.sub(r'\W+', '', a).lower() == re.sub(r'\W+', '', b).lower():
                status = 'EXACT_NORMALIZED_STRING_MATCH'
            else:
                status = 'AVAILABLE_BOTH_NONUNIQUE_REPRESENTATION'
            comp['fields'][name] = {'topology_database': a, 'katlas': b, 'status': status}
        comp['database_aliases'] = dbr.get('aliases', [])
        comp['notation_labels'] = dbr.get('notation_labels', {})
    write_json(d / 'reference_comparison.json', comp)
    return {'database': db, db_name: db, 'katlas': ka, 'comparison': comp}
