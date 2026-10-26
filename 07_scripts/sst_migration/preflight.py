"""Read-only source audit and persistent, single-item pilot preflight queue.

This program deliberately cannot migrate or execute scientific code. Release
promotion requires a reviewed per-family adapter and a passing source audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK = Path('06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10')
E010 = Path('01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas')
PRODUCTION = E010 / 'E010-v0.3.1/E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs'
VIEW = E010 / 'E010-v0.3.1/E010_PKLSA_Multiseed_View_v0.3.4-outputs'
PILOTS = {
    'A011': ('A011-v0.3.1', 'A011-v0.4.0', 'Standalone geometry / Python-native parity',
             'Map geometry inputs and independent physical/thermodynamic observables; freeze unchanged thresholds.'),
    'A054': ('A054-v0.5.1', 'A054-v0.6.0', 'E013 / E011 provider-dependent state selection',
             'Require E013-COMMON-CARRIER-MANIFEST-1 and E011 provider anchors; preserve stage 30 and deduplicate enabled versions.'),
    'A065': ('A065-v0.4.3', 'A065-v0.5.0', 'Blind seals / historical and synthetic source lanes',
             'Verify immutable D01/D02/D03 seals; audit source-specific README and contracts; synthetic lanes cannot qualify physical PKLSA claims.'),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def locked(state):
    lock = state / 'queue.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, json.dumps({'pid': os.getpid(), 'created': now()}).encode())
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        lock.unlink()


def inventory(root):
    hp = root / '10_docs/registry/family_hierarchy.json'
    cp = root / '10_docs/registry/catalog_index.json'
    hierarchy, catalog = read(hp), read(cp)
    records = {}
    def add(entry, source):
        if entry.get('kind') != 'falsifier' and entry.get('letter') != 'A_falsifiers':
            return
        rel = entry['path']
        row = records.setdefault(rel, {'id': entry['catalog_id'], 'path': rel, 'registry': {}})
        row['registry'][source] = {'latest': entry.get('latest'), 'versions': entry.get('declared_versions', entry.get('versions', []))}
    for domain in hierarchy['hierarchy'].values():
        for letter in domain.values():
            for entry in letter.values():
                add(entry, 'hierarchy')
    for domain in catalog['by_domain'].values():
        for entry in domain.values():
            add(entry, 'catalog')
    for path in sorted((root / '01_research/A_falsifiers').iterdir()):
        if path.is_dir() and re.match(r'^A\d{3}_', path.name):
            rel = path.relative_to(root).as_posix()
            records.setdefault(rel, {'id': path.name[:4], 'path': rel, 'registry': {}})
    for row in records.values():
        path = root / row['path']
        row['exists'] = path.is_dir()
        row['disk_versions'] = sorted(p.name for p in path.iterdir() if p.is_dir() and p.name.startswith(row['id'] + '-')) if path.is_dir() else []
        row['family_sha256'] = sha(path / 'FAMILY.yaml') if (path / 'FAMILY.yaml').is_file() else None
        row['family_latest'] = None
        if row['family_sha256']:
            match = re.search(r'^latest:\s*(\S+)', (path / 'FAMILY.yaml').read_text(encoding='utf-8-sig'), re.M)
            row['family_latest'] = match[1].strip('"\'') if match else None
        row['issues'] = []
        if len(row['registry']) != 2:
            row['issues'].append('NOT_IN_BOTH_CANONICAL_INDICES')
        if not row['family_sha256']:
            row['issues'].append('MISSING_FAMILY_YAML')
        for source, entry in row['registry'].items():
            declared = {v['directory'] for v in entry['versions'] if 'directory' in v}
            if declared != set(row['disk_versions']):
                row['issues'].append(source.upper() + '_VERSION_DRIFT')
        row['version_metadata'] = {}
        for version in row['disk_versions']:
            vp = path / version
            row['version_metadata'][version] = {n: sha(vp / n) for n in ['project.json', '.sst_framework_root', 'science_contract.json', 'pyproject.toml', 'requirements.txt'] if (vp / n).is_file()}
    return {'created': now(), 'registry_hashes': {str(p.relative_to(root)): sha(p) for p in [hp, cp]}, 'families': sorted(records.values(), key=lambda x: (x['id'], x['path']))}


def checked_child(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Manifest path escapes source root')
    return path


def audit(root):
    fw = root / FRAMEWORK
    manifest = read(fw / 'PACKAGE_MANIFEST.json')
    failures = []
    for entry in manifest['files']:
        path = checked_child(fw, entry['path'])
        actual = sha(path) if path.is_file() else None
        if actual != entry['sha256']:
            failures.append({'path': entry['path'], 'expected': entry['sha256'], 'actual': actual})
    release = read(root / VIEW / 'SELECTION_RELEASE.json')
    hashes = []
    for relative, expected in release['source_manifest_sha256'].items():
        path = checked_child(root / PRODUCTION, relative)
        actual = sha(path) if path.is_file() else None
        hashes.append({'path': relative, 'expected': expected, 'actual': actual, 'pass': expected == actual})
    index = read(root / VIEW / 'ACTIVE_ATLAS_INDEX.json')
    carriers = index['carriers']
    absent = [x['topology_id'] for x in carriers if not (root / PRODUCTION / 'atlas' / x['topology_id']).is_dir()]
    pins = [FRAMEWORK / 'PACKAGE_MANIFEST.json', FRAMEWORK / 'CANONICAL_FREEZE.json', FRAMEWORK / 'RELEASE_INFO.json', VIEW / 'SELECTION_RELEASE.json', VIEW / 'ACTIVE_ATLAS_INDEX.json']
    return {
        'created': now(), 'pins': {p.as_posix(): sha(root / p) for p in pins},
        'framework': {'manifest_entries': len(manifest['files']), 'failures': failures, 'status': 'PASS' if not failures else 'BLOCKED_SOURCE_INTEGRITY'},
        'pklsa': {'source_hashes': hashes, 'source_hash_status': 'PASS' if all(x['pass'] for x in hashes) else 'FAIL',
                  'active_count': len(carriers), 'historical_statuses': dict(Counter(x['historical_status'] for x in carriers)),
                  'missing_topology_paths': absent, 'qualification': release['status'],
                  'geometry_payload_hashes_verified': False,
                  'scientifically_qualified_for_pilots': False,
                  'development_v035': read(root / E010 / 'E010-v0.3.5/VALIDATION_REPORT.json')},
        'runtime': {'python': os.sys.version, 'executables': {x: shutil.which(x) for x in ['pdflatex', 'g++', 'cl', 'icx', 'pdftoppm']},
                    'framework_venv_present': (fw / '.venv/Scripts/python.exe').is_file(), 'native_backend_retested': False},
    }


def initialize(root, state):
    state.mkdir(parents=True, exist_ok=True)
    with locked(state):
        if (state / 'queue.json').exists():
            raise FileExistsError('Queue exists; initialization never overwrites a queue')
        inv, evidence = inventory(root), audit(root)
        atomic(state / 'inventory.json', inv)
        atomic(state / 'source_audit.json', evidence)
        jobs = []
        for row in inv['families']:
            pilot = PILOTS.get(row['id'])
            jobs.append({'id': row['id'], 'family_path': row['path'], 'pilot': bool(pilot),
                         'source_version': pilot[0] if pilot else None, 'proposed_version': pilot[1] if pilot else None,
                         'architecture': pilot[2] if pilot else None, 'adapter_requirements': pilot[3] if pilot else 'Manual per-family adapter review required',
                         'status': 'PENDING_PREFLIGHT' if pilot else 'WAITING_PILOT',
                         'migration_gate': 'NOT_RUN', 'execution_gate': 'NOT_RUN', 'scientific_gate': 'NOT_RUN'})
        jobs.sort(key=lambda j: (not j['pilot'], j['id'], j['family_path']))
        atomic(state / 'queue.json', {'schema': 'SST-MIGRATION-PREFLIGHT-1', 'created': now(), 'scheduling_enabled': False, 'pilot_validated': False, 'jobs': jobs})
    return {'families': len(jobs), 'versions_on_disk': sum(len(x['disk_versions']) for x in inv['families']), 'framework': evidence['framework']['status']}


def next_item(root, state):
    with locked(state):
        queue = read(state / 'queue.json')
        job = next((x for x in queue['jobs'] if x['pilot'] and x['status'] == 'PENDING_PREFLIGHT'), None)
        if job is None:
            return {'status': 'NO_PENDING_PILOT_PREFLIGHT', 'pilot_validated': queue['pilot_validated']}
        evidence = audit(root)
        current = inventory(root)
        initial = read(state / 'inventory.json')
        blockers = ['PER_FAMILY_ADAPTER_NOT_IMPLEMENTED', 'DATASET_ADMISSION_AND_PAYLOAD_HASH_AUDIT_REQUIRED']
        if evidence['framework']['status'] != 'PASS':
            blockers.append('FRAMEWORK_MANIFEST_MISMATCH')
        if evidence['pklsa']['source_hash_status'] != 'PASS':
            blockers.append('PKLSA_SOURCE_HASH_MISMATCH')
        if current['registry_hashes'] != initial['registry_hashes']:
            blockers.append('REGISTRY_CHANGED_AFTER_INITIALIZATION')
        row = next(x for x in current['families'] if x['path'] == job['family_path'])
        if row['issues']:
            blockers.append('REGISTRY_RECONCILIATION_REQUIRED')
        if not (root / job['family_path'] / job['source_version']).is_dir():
            blockers.append('SOURCE_VERSION_MISSING')
        if (root / job['family_path'] / job['proposed_version']).exists():
            blockers.append('DESTINATION_ALREADY_EXISTS_CHOOSE_NEW_VERSION')
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        result = dict(job, status='BLOCKED_PREFLIGHT', migration_gate='BLOCKED', execution_gate='NOT_RUN', scientific_gate='NOT_RUN',
                      run_id=run_id, created=now(), blockers=blockers, source_audit=evidence,
                      source_version_metadata=row['version_metadata'].get(job['source_version'], {}), registry_issues=row['issues'],
                      scope='Preflight only; no migration, no numerical execution, no scientific certification')
        report = state / 'runs' / run_id
        report.mkdir(parents=True, exist_ok=False)
        atomic(report / 'result.json', result)
        # Immutable result is the durable journal. Queue update follows publication;
        # interrupted updates may cause another preflight but never a scientific run.
        job.update({k: result[k] for k in ['status', 'migration_gate', 'execution_gate', 'scientific_gate', 'run_id', 'blockers']})
        job['result'] = str((report / 'result.json').relative_to(state))
        atomic(state / 'queue.json', queue)
        return {'id': job['id'], 'status': job['status'], 'result': job['result']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'preflight-next', 'status'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'init':
        result = initialize(args.root.resolve(), args.state.resolve())
    elif args.command == 'preflight-next':
        result = next_item(args.root.resolve(), args.state.resolve())
    else:
        q = read(args.state / 'queue.json')
        result = {'scheduling_enabled': q['scheduling_enabled'], 'pilot_validated': q['pilot_validated'], 'statuses': dict(Counter(j['status'] for j in q['jobs']))}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
