"""Verify and publish A011 artifacts, register only A011, atomically update queue."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, atomic, locked, now
from phase3_prepare import OUT, FAMILY, snapshot, create_json
sys.path.insert(0, str(ROOT / '07_scripts'))
import build_catalog_index as bci
import build_family_hierarchy as bh


def preserve_before(path):
    dst = OUT / 'before_publication' / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('xb') as stream:
        stream.write(path.read_bytes())


def main():
    root = FAMILY / 'A011-v0.4.0'
    output = root / '1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs'
    summary = read(output / 'RUN_SUMMARY.json')
    if summary['execution_gate'] != 'PASS_BOUNDED_GEOMETRY_SMOKE' or summary['scientific_status_promoted']:
        raise RuntimeError('Publication gate not satisfied')
    for row in read(root / 'SOURCE_MANIFEST_v0.4.0.json')['files']:
        if sha(root / row['path']) != row['sha256']:
            raise RuntimeError('Source changed after successful tests')
    for row in read(output / 'RESULT_EVIDENCE_MANIFEST.json')['files']:
        if sha(output / row['path']) != row['sha256']:
            raise RuntimeError('Machine evidence changed during reporting')
    before = read(OUT / 'preservation_before.json')
    if snapshot(FAMILY / 'A011-v0.3.1') != before['A011-v0.3.1']:
        raise RuntimeError('Predecessor tree changed')
    protected = {}
    for cid in ['A054', 'A065']:
        data = before[cid]
        changed = [p for p, digest in data['files'].items() if sha(ROOT / data['path'] / p) != digest]
        family = (ROOT / data['path']).parent
        if changed or sha(family / 'FAMILY.yaml') != data['family_sha256']:
            raise RuntimeError('Excluded pilot changed: ' + cid)
        protected[cid] = {'status': 'UNCHANGED', 'source_files_verified': len(data['files']), 'family_metadata_unchanged': True}
    preservation = {'A011-v0.3.1': {'status': 'UNCHANGED', 'all_files_verified': len(before['A011-v0.3.1'])},
                    'excluded_pilots': protected, 'old_framework_document_unchanged': sha(ROOT / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/docs/DD32_FP32X2.md') == read(OUT / 'framework_source_qualification.json')['local_variant_sha256']}
    create_json(output / 'PRESERVATION_VERIFICATION.json', preservation)
    report = output / 'A011_v0.4.0_Framework_v1.0.10_FALSIFIER_REPORT.pdf'
    if not report.is_file():
        raise RuntimeError('Required standalone PDF is missing')
    entries = [{'path': p.relative_to(output).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(output.rglob('*')) if p.is_file()]
    create_json(output / 'OUTPUT_MANIFEST.json', {'schema': 'A011-V040-OUTPUT-MANIFEST-1', 'files': entries})
    archive = FAMILY / '1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs.zip'
    with archive.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(output.rglob('*')):
                if p.is_file():
                    z.write(p, output.name + '/' + p.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as z:
        for entry in entries:
            if hashlib.sha256(z.read(output.name + '/' + entry['path'])).hexdigest() != entry['sha256']:
                raise RuntimeError('Archive payload verification failed')
        if z.testzip() is not None:
            raise RuntimeError('ZIP CRC verification failed')
    with archive.with_suffix('.zip.sha256').open('x', encoding='ascii') as stream:
        stream.write(sha(archive) + '  ' + archive.name + '\n')
    decision = {'decision': 'NO_GO_IMMEDIATE_A054_MIGRATION',
                'framework_prerequisite': 'PASS_SHARED_QUALIFIED_SOURCE_AVAILABLE',
                'reasons': ['P02 A054 source ZIP selection/admission is not yet performed', 'P04 successor must pin v1.0.10 and enforce runtime E013 self-hash/E011 bindings and loader pins', 'L2a1 remains single-provider; physical/cross-provider claims cannot be promoted'],
                'scope': 'No A054 source, metadata, queue job, execution or scientific status changed in this tranche. No automatic A054 start.',
                'next_permitted_preparation': 'A separately authorized controlled A054 source/admission tranche; full physical campaign remains excluded'}
    publication = {'schema': 'SST-PHASE3-PUBLICATION-1', 'created_utc': now(),
                   'framework_gate': 'PASS_112_MANIFEST_ENTRIES', 'migration_gate': summary['migration_gate'], 'execution_gate': summary['execution_gate'],
                   'scientific_gate': summary['scientific_gate'], 'scientific_status_promoted': False,
                   'output_archive': archive.relative_to(ROOT).as_posix(), 'output_archive_sha256': sha(archive),
                   'output_manifest_sha256': sha(output / 'OUTPUT_MANIFEST.json'), 'report_path': report.relative_to(ROOT).as_posix(), 'report_sha256': sha(report),
                   'source': read(OUT / 'a011_source_publication.json'), 'preservation': preservation, 'a054_next_tranche': decision,
                   'scheduling_enabled': False}
    # Registry update is scoped to A011 only; old scientific/reproducibility fields
    # and every other family stay structurally identical.
    hp = ROOT / '10_docs/registry/family_hierarchy.json'
    cp = ROOT / '10_docs/registry/catalog_index.json'
    fy = FAMILY / 'FAMILY.yaml'
    h, c = read(hp), read(cp)
    oldh, oldc = deepcopy(h), deepcopy(c)
    for p in [hp, cp, fy]:
        preserve_before(p)
    text = fy.read_text(encoding='utf-8')
    if 'directory: "A011-v0.4.0"' in text:
        raise RuntimeError('Release already registered')
    text = text.replace('latest: v0.3.1', 'latest: v0.4.0', 1)
    needle = '    directory: "A011-v0.3.1"'
    if text.count(needle) != 1:
        raise RuntimeError('Unexpected A011 FAMILY layout')
    text = text.replace(needle, needle + '\n  - id: v0.4.0\n    directory: "A011-v0.4.0"\n    qualification: GEOMETRY_ADAPTER_ONLY', 1)
    fy.write_text(text, encoding='utf-8')
    meta = bci.parse_family(fy)
    entry = c['by_domain']['01_research']['A011']
    entry.update({'latest': meta['latest'], 'versions': meta['versions']})
    node = h['hierarchy']['01_research']['A_falsifiers']['A011']
    node['latest'], node['declared_versions'] = meta['latest'], meta['versions']
    node['versions_on_disk']['v0.4.0'] = {'directory': 'A011-v0.4.0', 'path': root.relative_to(ROOT).as_posix(), 'declared': True,
                                        'expected_outputs_zip': archive.name, 'expected_zip_present': True,
                                        **bh.collect_version_artifacts(root), 'controlled_output_archive': archive.relative_to(ROOT).as_posix(),
                                        'controlled_output_archive_sha256': sha(archive), 'qualification': 'GEOMETRY_ADAPTER_ONLY'}
    node['other_dirs'] = [x for x in node.get('other_dirs', []) if x != 'A011-v0.4.0']
    if h['by_catalog_id'].get('A011', {}).get('path') == meta['path']:
        h['by_catalog_id']['A011']['latest'] = 'v0.4.0'
        h['by_catalog_id']['A011']['version_dirs'].append('A011-v0.4.0')
    c['versions'] += 1
    h['version_count_declared'] += 1
    h['version_count_on_disk'] += 1
    h['generated_at'] = now()
    # Check only A011 changed, before writing derived indices.
    expected_h = deepcopy(h)
    expected_h['hierarchy']['01_research']['A_falsifiers']['A011'] = oldh['hierarchy']['01_research']['A_falsifiers']['A011']
    expected_h['by_catalog_id'] = oldh['by_catalog_id']
    for key in ['version_count_declared', 'version_count_on_disk', 'generated_at']:
        expected_h[key] = oldh[key]
    if expected_h != oldh:
        raise RuntimeError('Unexpected unrelated hierarchy mutation')
    expected_c = deepcopy(c)
    expected_c['by_domain']['01_research']['A011'] = oldc['by_domain']['01_research']['A011']
    expected_c['versions'] = oldc['versions']
    if expected_c != oldc:
        raise RuntimeError('Unexpected unrelated catalog mutation')
    atomic(hp, h)
    atomic(cp, c)
    state = ROOT / '10_docs/migration_v110/pilot_20261026'
    with locked(state):
        queue_path = state / 'queue.json'
        preserve_before(queue_path)
        queue = read(queue_path)
        old_jobs = deepcopy(queue['jobs'])
        if queue['scheduling_enabled'] or queue['pilot_validated']:
            raise RuntimeError('Scheduling/pilot batch unexpectedly enabled')
        job = next(j for j in queue['jobs'] if j['id'] == 'A011')
        job['previous_preflight_run_id'] = job['run_id']
        job.update({'run_id': summary['run_id'], 'completed_version': 'A011-v0.4.0', 'status': 'CONTROLLED_GEOMETRY_MIGRATED',
                    'migration_gate': summary['migration_gate'], 'execution_gate': summary['execution_gate'], 'scientific_gate': summary['scientific_gate'],
                    'latest_result': (output / 'RUN_SUMMARY.json').relative_to(ROOT).as_posix(),
                    'blockers': ['PHYSICAL_INPUT_ADMISSION_UNRESOLVED'], 'phase3': publication})
        for original, current in zip(old_jobs, queue['jobs']):
            if original['id'] != 'A011' and original != current:
                raise RuntimeError('Excluded queue job changed')
        queue['phase3'] = {'at_utc': publication['created_utc'], 'framework_qualified': True, 'completed': ['A011-v0.4.0'],
                           'all_pilots_validated': False, 'a054_next_tranche_decision': decision['decision']}
        atomic(queue_path, queue)
    publication['queue_sha256_after'] = sha(state / 'queue.json')
    publication['registry_sha256_after'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in [hp, cp, fy]}
    create_json(OUT / 'gate_overview.json', publication)
    print(json.dumps({k: publication[k] for k in ['migration_gate', 'execution_gate', 'scientific_gate', 'output_archive_sha256', 'report_sha256', 'scheduling_enabled']}, indent=2))


if __name__ == '__main__':
    main()
