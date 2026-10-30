"""Read-only final verification after report-contract publication/registration."""
import hashlib
import json
from pathlib import Path
import sys
import tomllib
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from restore_report_prepare import OUT, FAMILY
from phase3_prepare import snapshot


def main():
    result = read(OUT / 'RESTORATION_RESULT.json')
    before = read(OUT / 'PRESERVATION_BEFORE.json')
    for version in ['A011-v0.3.1', 'A011-v0.4.0']:
        assert snapshot(FAMILY / version) == before[version]
    root = FAMILY / 'A011-v0.4.1'
    pin = read(root / 'FRAMEWORK_SOURCE_PIN.json')
    assert len(pin['verification']) == pin['manifest_entries_verified'] == 112
    for row in pin['verification']:
        assert sha(ROOT / pin['selected_source'] / row['path']) == row['sha256']
    source = read(root / 'SOURCE_MANIFEST_v0.4.1.json')
    for row in source['files']:
        assert sha(root / row['path']) == row['sha256']
    for row in source['external_bindings']:
        assert sha(ROOT / row['path']) == row['sha256']
    archive = Path(result['source_archive'])
    assert sha(archive) == result['source_archive_sha256']
    assert archive.with_suffix('.zip.sha256').read_text().split()[0] == sha(archive)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for row in source['files']:
            assert hashlib.sha256(z.read('A011-v0.4.1/' + row['path'])).hexdigest() == row['sha256']
    for ref in before['references']:
        assert sha(ROOT / ref['pdf']) == ref['pdf_sha256']
        assert sha(ROOT / ref['tex']) == ref['tex_sha256']
    bp = OUT / 'before_registration'
    h = read(ROOT / '10_docs/registry/family_hierarchy.json')
    oldh = read(bp / '10_docs/registry/family_hierarchy.json')
    for domain, letters in oldh['hierarchy'].items():
        for letter, nodes in letters.items():
            for cid, node in nodes.items():
                if (domain, letter, cid) != ('01_research', 'A_falsifiers', 'A011'):
                    assert h['hierarchy'][domain][letter][cid] == node
    c = read(ROOT / '10_docs/registry/catalog_index.json')
    oldc = read(bp / '10_docs/registry/catalog_index.json')
    for domain, nodes in oldc['by_domain'].items():
        for cid, node in nodes.items():
            if (domain, cid) != ('01_research', 'A011'):
                assert c['by_domain'][domain][cid] == node
    assert c['by_domain']['01_research']['A011']['latest'] == 'v0.4.1'
    assert h['hierarchy']['01_research']['A_falsifiers']['A011']['latest'] == 'v0.4.1'
    qpath = ROOT / '10_docs/migration_v110/pilot_20261026/queue.json'
    q = read(qpath)
    queue_capture = bp / qpath.relative_to(ROOT)
    capture_bytes = queue_capture.read_bytes()
    audit_notes = []
    if capture_bytes and not capture_bytes.strip(b'\x00'):
        # Preserve the invalid capture; never reconstruct historical evidence.
        baseline = ROOT / '10_docs/migration_v110/scheduled_control/queue.before_schedule_registration.json'
        oldq = read(baseline)
        audit_notes.append({'issue': 'PRE_REGISTRATION_QUEUE_CAPTURE_CONTAINS_ONLY_NUL_BYTES',
                            'invalid_capture': str(queue_capture.relative_to(ROOT)),
                            'sha256': sha(queue_capture), 'bytes': len(capture_bytes),
                            'comparison_baseline': str(baseline.relative_to(ROOT)),
                            'limitation': 'Exact immediately preceding queue bytes cannot be verified from this capture; all other jobs and scientific axes match the earlier intact baseline.'})
    else:
        oldq = read(queue_capture)
    assert not q['scheduling_enabled'] and not q['pilot_validated']
    assert q['scheduled_control']['status'] == 'PAUSED'
    assert len(q['jobs']) == len(oldq['jobs'])
    for old, new in zip(oldq['jobs'], q['jobs']):
        if old['id'] != 'A011':
            assert old == new
        else:
            for axis in ['migration_gate', 'execution_gate', 'scientific_gate']:
                assert old[axis] == new[axis]
            assert new['reporting_gate'] == new['packaging_gate'] == 'PASS'
    config = Path.home() / '.codex/automations/sst-workbench-dagelijkse-migratiecontrole/automation.toml'
    automation = tomllib.loads(config.read_text(encoding='utf-8'))
    assert automation['status'] == 'PAUSED'
    checks = {'status': 'PASS_WITH_AUDIT_NOTE' if audit_notes else 'PASS', 'audit_notes': audit_notes,
              'framework_manifest_entries_verified': 112,
              'source_inventory_files_verified': len(source['files']),
              'historical_versions_preserved': True, 'reference_reports_preserved': True,
              'source_archive_verified': True, 'only_a011_registered': True,
              'other_queue_jobs_unchanged': True, 'scientific_axes_unchanged': True,
              'scheduled_status': automation['status'], 'queue_sha256': sha(qpath)}
    target = OUT / 'FINAL_REGISTRATION_VALIDATION.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump(checks, stream, indent=2)
        stream.write('\n')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
