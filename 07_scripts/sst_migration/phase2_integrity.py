"""Phase 2 read-only integrity checks. Outputs never rewrite historical inputs."""
from __future__ import annotations
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, FRAMEWORK, E010, PRODUCTION, VIEW, read, sha, atomic, checked_child


def framework(root, out):
    freeze = read(root / FRAMEWORK / 'CANONICAL_FREEZE.json')
    expected_zip = freeze['source_artifact_sha256']
    path = root / '06_templates' / freeze['source_artifact']
    actual_zip = sha(path)
    if actual_zip != expected_zip:
        raise ValueError('RC2 archive does not match frozen digest')
    evidence = out / 'framework'
    evidence.mkdir(exist_ok=False)
    prefix = 'SST_Falsifier_Framework_v1.0.10/'
    with zipfile.ZipFile(path) as archive:
        manifest_bytes = archive.read(prefix + 'PACKAGE_MANIFEST.json')
        manifest = json.loads(manifest_bytes)
        entries = manifest['files']
        if isinstance(entries, dict):
            entries = [{'path': k, 'sha256': v} for k, v in entries.items()]
        results = []
        for entry in entries:
            data = archive.read(prefix + entry['path'])
            digest = hashlib.sha256(data).hexdigest()
            results.append({'path': entry['path'], 'expected': entry['sha256'], 'actual': digest, 'match': digest == entry['sha256']})
        local_checks = []
        for entry in entries:
            local = checked_child(root / FRAMEWORK, entry['path'])
            digest = sha(local) if local.is_file() else None
            local_checks.append({'path': entry['path'], 'expected': entry['sha256'], 'actual': digest, 'match': digest == entry['sha256']})
        sealed = archive.read(prefix + 'docs/DD32_FP32X2.md')
        installed = (root / FRAMEWORK / 'docs/DD32_FP32X2.md').read_bytes()
        (evidence / 'DD32_FP32X2.sealed_RC2.md').write_bytes(sealed)
        (evidence / 'DD32_FP32X2.installed.md').write_bytes(installed)
        (evidence / 'RC2_PACKAGE_MANIFEST.json').write_bytes(manifest_bytes)
        diff = ''.join(difflib.unified_diff(sealed.decode().splitlines(keepends=True), installed.decode().splitlines(keepends=True), fromfile='sealed_RC2/docs/DD32_FP32X2.md', tofile='installed/docs/DD32_FP32X2.md'))
        (evidence / 'DD32_FP32X2.diff').write_text(diff, encoding='utf-8')
        normalized = sealed.decode().replace('\\[', '$$').replace('\\]', '$$').rstrip('\r\n')
        formatting_only = normalized == installed.decode().rstrip('\r\n')
    canonical = root / '06_templates/SST_Falsifier_Framework_v1.0.10-CANONICAL_FROZEN.zip'
    result = {
        'authenticity_basis': 'Exact ZIP digest bound by existing CANONICAL_FREEZE.json; not an independent publisher signature',
        'freeze_path': str(FRAMEWORK / 'CANONICAL_FREEZE.json'), 'freeze_sha256': sha(root / FRAMEWORK / 'CANONICAL_FREEZE.json'),
        'archive_path': str(path.relative_to(root)), 'archive_expected_sha256': expected_zip, 'archive_actual_sha256': actual_zip,
        'canonical_archive_sha256': sha(canonical) if canonical.is_file() else None,
        'archive_entries': results, 'archive_internal_manifest_valid': all(x['match'] for x in results),
        'local_vs_sealed_entries': local_checks,
        'sealed_document_sha256': hashlib.sha256(sealed).hexdigest(), 'installed_document_sha256': hashlib.sha256(installed).hexdigest(),
        'difference_limited_to_math_delimiters_and_eof_newline': formatting_only,
        'source_authenticity': 'PASS' if all(x['match'] for x in results) else 'FAIL',
        'installed_byte_integrity': 'PASS' if all(x['match'] for x in local_checks) else 'FAIL',
        'historical_manifest_changed': False, 'installed_document_changed': False,
    }
    atomic(out / 'framework_integrity.json', result)
    return result


def geometry(root, out):
    import numpy as np
    source = root / E010 / 'E010-v0.3.1'
    sys.path.insert(0, str(source))
    from pklsa_builder.models import Carrier
    from pklsa_builder.campaign import load_carrier_geometry
    from pklsa_builder.hashing import geometry_sha256
    active = {x['topology_id'] for x in read(root / VIEW / 'ACTIVE_ATLAS_INDEX.json')['carriers']}
    raw_cache = {}
    rows = []
    tops = sorted((root / PRODUCTION / 'atlas').iterdir())
    for idx, top in enumerate(tops):
        for kind in ['sources', 'generated']:
            for path in sorted((top / kind).glob('*/*.json')):
                item = read(path)
                if 'carrier' not in item:
                    continue
                carrier = item['carrier']
                row = {'record': path.relative_to(root).as_posix(), 'record_sha256': sha(path),
                       'topology_id': top.name, 'active_view': top.name in active,
                       'carrier_id': carrier['carrier_id'], 'source_path': carrier.get('source_path'),
                       'raw_expected_sha256': carrier.get('raw_sha256'), 'geometry_expected_sha256': item.get('geometry_sha256')}
                p = Path(carrier['source_path']) if carrier.get('source_path') else None
                try:
                    if p is None or not p.is_file():
                        raise FileNotFoundError('Exact recorded source unavailable; no substitution permitted')
                    # Do not follow arbitrary recorded paths outside this checkout.
                    checked_child(root, p)
                    if str(p) not in raw_cache:
                        raw_cache[str(p)] = sha(p)
                    row['raw_actual_sha256'] = raw_cache[str(p)]
                    row['raw_status'] = ('UNPINNED' if not carrier.get('raw_sha256') else
                                         'PASS' if carrier['raw_sha256'] == row['raw_actual_sha256'] else 'FAIL')
                    comps = load_carrier_geometry(Carrier.from_dict(carrier))
                    row['component_shapes'] = [list(np.asarray(c).shape) for c in comps]
                    row['finite'] = bool(comps) and all(np.isfinite(c).all() for c in comps)
                    row['geometry_actual_sha256'] = geometry_sha256(comps)
                    row['geometry_status'] = 'PASS' if row['finite'] and row['geometry_actual_sha256'] == item.get('geometry_sha256') else 'FAIL'
                    row['status'] = 'PASS' if row['geometry_status'] == row['raw_status'] == 'PASS' else 'FAIL_OR_UNPINNED'
                except Exception as error:
                    row['status'] = 'UNRESOLVED'
                    row['error'] = type(error).__name__ + ': ' + str(error)
                rows.append(row)
        if idx % 250 == 0:
            print(f'Geometry audit: {idx + 1}/{len(tops)} topologies; {len(rows)} records', flush=True)
    with (out / 'geometry_hashes.jsonl').open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + '\n')
    summaries = {}
    for name, selected in [('entire_production_atlas', rows), ('active_multiseed_view', [r for r in rows if r['active_view']])]:
        summaries[name] = {'records': len(selected), 'statuses': dict(Counter(r['status'] for r in selected)),
                           'raw_statuses': dict(Counter(r.get('raw_status', 'NOT_CHECKED') for r in selected)),
                           'geometry_statuses': dict(Counter(r.get('geometry_status', 'NOT_CHECKED') for r in selected))}
    result = {'scope': 'All carrier descriptor JSON records in all 2227 production atlas topology directories, including active and excluded sources; no solver campaign',
              'topology_directories': len(tops), 'unique_raw_files_hashed': len(raw_cache), 'hash_definition': 'PKLSA-GEOMETRY-SHA256-v1, original source-native loader; no normalization or resampling except that defined by original representation',
              'loader_pins': {p.relative_to(root).as_posix(): sha(p) for p in sorted((source / 'pklsa_builder').glob('*.py'))},
              'numpy_version': np.__version__, 'summaries': summaries,
              'scientific_qualification': 'NOT_EVALUATED_NO_STATUS_PROMOTION'}
    atomic(out / 'geometry_integrity.json', result)
    return result


def seals(root, out):
    base = root / '01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3'
    results = []
    commitment = read(base / 'seals/GLOBAL_COMMITMENT.json')
    for dataset in ['D01_EULER', 'D02_CLOCK_LINK', 'D03_TWO_SURFACE']:
        path = base / 'seals' / (dataset + '.seal.json')
        seal = read(path)
        core = {k: v for k, v in seal.items() if k != 'self_sha256'}
        canonical = (json.dumps(core, sort_keys=True, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')
        actual = {p.relative_to(base).as_posix(): sha(p) for p in sorted((base / 'data' / dataset).rglob('*')) if p.is_file()}
        entries = [{'path': name, 'expected': digest, 'actual': actual.get(name), 'match': digest == actual.get(name)} for name, digest in seal['files'].items()]
        results.append({'dataset': dataset, 'seal_sha256': sha(path), 'self_hash_match': hashlib.sha256(canonical).hexdigest() == seal['self_sha256'],
                        'commitment_match': commitment['seals'].get(dataset) == seal['self_sha256'],
                        'entries': entries, 'extra_files': sorted(set(actual) - set(seal['files'])),
                        'status': 'PASS' if actual == seal['files'] and hashlib.sha256(canonical).hexdigest() == seal['self_sha256'] and commitment['seals'].get(dataset) == seal['self_sha256'] else 'FAIL'})
    manifests = []
    for path in sorted(base.glob('SOURCE_MANIFEST_V*.json')):
        doc = read(path)
        entries = []
        mapping = doc.get('files_sha256', doc.get('source_files', doc.get('files', {})))
        if isinstance(mapping, list):
            mapping = {item['path']: item['sha256'] for item in mapping}
        for relative, expected in mapping.items():
            p = checked_child(base, relative)
            actual = sha(p) if p.is_file() else None
            entries.append({'path': relative, 'expected': expected, 'actual': actual, 'match': expected == actual})
        manifests.append({'manifest': path.name, 'manifest_sha256': sha(path), 'entries': len(entries), 'failures': [x for x in entries if not x['match']],
                          'comparison_scope': 'Historical manifest compared with current v0.4.3 tree; differences in older manifests are not alone evidence of corruption',
                          'status': 'PASS' if entries and all(x['match'] for x in entries) else 'MISMATCH'})
    contract_path = base / 'data/D01_EULER/pklsa/fremlin_provider_contract.json'
    contract = read(contract_path)
    p = root / contract['workbench_relative_path']
    provider = {'contract_sha256': sha(contract_path), 'expected_raw_sha256': contract['expected_raw_sha256'], 'actual_raw_sha256': sha(p) if p.is_file() else None,
                'status': 'PASS_RAW_ONLY' if p.is_file() and sha(p) == contract['expected_raw_sha256'] else 'UNRESOLVED_MISSING_OR_MISMATCH', 'geometry_hash_required': contract['expected_geometry_sha256']}
    result = {'datasets': results, 'global_commitment_sha256': sha(base / 'seals/GLOBAL_COMMITMENT.json'),
              'source_manifests': manifests, 'fremlin_provider': provider,
              'private_targets_opened': False, 'reveal_executed': False,
              'boundary': 'Tamper-evident local seals, no external signature or physical science certification'}
    atomic(out / 'a065_seals.json', result)
    return result


def pilot_archives(root, out):
    results = []
    specifications = [
        ('A054', Path.home() / 'Downloads/A054_E013_State_Selection_Provider_Convergence_Falsifier_v0.5.1.zip',
         root / '01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1', 'PACKAGE_MANIFEST.json'),
        ('A065', Path.home() / 'Downloads/A065_Triadic_Casimir_v0.4.3_SOURCE.zip',
         root / '01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3', 'SOURCE_MANIFEST_V043.json')]
    for pilot, path, installed, manifest_name in specifications:
        dest = out / 'pilot_source_archives' / pilot
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            name = next(n for n in archive.namelist() if n.endswith('/' + manifest_name))
            prefix = name[:-len(manifest_name)]
            raw = archive.read(name)
            (dest / manifest_name).write_bytes(raw)
            doc = json.loads(raw)
            mapping = doc.get('files_sha256', doc.get('files'))
            if isinstance(mapping, list):
                mapping = {e['path']: e['sha256'] for e in mapping}
            failures, differences = [], []
            for relative, expected in mapping.items():
                archived = archive.read(prefix + relative)
                archive_digest = hashlib.sha256(archived).hexdigest()
                if archive_digest != expected:
                    failures.append({'path': relative, 'expected': expected, 'actual': archive_digest})
                target = checked_child(installed, relative)
                local = target.read_bytes() if target.is_file() else b''
                if local != archived:
                    slug = relative.replace('/', '__')
                    (dest / (slug + '.archive')).write_bytes(archived)
                    (dest / (slug + '.installed')).write_bytes(local)
                    diff = ''.join(difflib.unified_diff(archived.decode('utf-8').splitlines(True), local.decode('utf-8').splitlines(True), fromfile='archive/' + relative, tofile='installed/' + relative))
                    (dest / (slug + '.diff')).write_text(diff, encoding='utf-8')
                    differences.append({'path': relative, 'expected_sha256': expected, 'archive_sha256': archive_digest, 'installed_sha256': hashlib.sha256(local).hexdigest(), 'diff': (dest / (slug + '.diff')).relative_to(out).as_posix()})
        results.append({'pilot': pilot, 'archive_path': str(path), 'archive_sha256': sha(path), 'manifest_entries': len(mapping),
                        'archive_manifest_failures': failures, 'installed_differences': differences,
                        'provenance_limit': 'Local Downloads archive matches its internal manifest; no independent release signature or previously trusted ZIP digest was available'})
    atomic(out / 'pilot_source_archive_comparisons.json', results)
    return {'archives': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=['framework', 'geometry', 'seals', 'pilot_archives'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    result = globals()[args.check](ROOT, args.out)
    print(json.dumps({k: v for k, v in result.items() if k not in ['archive_entries', 'local_vs_sealed_entries', 'source_manifests', 'loader_pins', 'datasets']}, indent=2))


if __name__ == '__main__':
    main()
