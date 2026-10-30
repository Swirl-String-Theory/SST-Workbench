"""Seal the tested A011 successor source and fixed pre-report result evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from phase3_prepare import OUT, FAMILY, create_json


def source_files(root):
    result = []
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        if any(x in {'build', '__pycache__', '.pytest_cache', '.venv'} or x.endswith('-outputs') for x in rel.parts):
            continue
        if p.is_file() and p.name != 'SOURCE_MANIFEST_v0.4.0.json':
            result.append(p)
    return result


def main():
    root = FAMILY / 'A011-v0.4.0'
    result = root / '1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs'
    for check in ['framework_targeted_tests', 'a011_tests', 'a011_geometry_smoke']:
        if read(OUT / (check + '.json'))['exit_code'] != 0:
            raise RuntimeError('Required successful check missing: ' + check)
    sys.path.insert(0, str(root / 'src'))
    from maxwell_sst_falsifier.framework_v110 import qualified_framework, verify_protocol
    qualified_framework(root)
    verify_protocol(root)
    files = source_files(root)
    entries = [{'path': p.relative_to(root).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files]
    core = {e['path']: e['sha256'] for e in entries}
    bundle = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    manifest = root / 'SOURCE_MANIFEST_v0.4.0.json'
    create_json(manifest, {'schema': 'A011-V040-SOURCE-MANIFEST-1', 'version': 'v0.4.0', 'source_tree_sha256': bundle, 'files': entries,
                         'scope': 'Tested controlled geometry adapter; predecessor results and private data excluded', 'scientific_authority': 'NO_NEW_PHYSICAL_CERTIFICATION'})
    archive = FAMILY / 'A011-v0.4.0_SOURCE.zip'
    with archive.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in files + [manifest]:
                z.write(p, 'A011-v0.4.0/' + p.relative_to(root).as_posix())
    with archive.with_suffix('.zip.sha256').open('x', encoding='ascii') as stream:
        stream.write(sha(archive) + '  ' + archive.name + '\n')
    with zipfile.ZipFile(archive) as z:
        for entry in entries:
            if hashlib.sha256(z.read('A011-v0.4.0/' + entry['path'])).hexdigest() != entry['sha256']:
                raise RuntimeError('Source archive verification failed')
    logs = result / 'logs'
    logs.mkdir(exist_ok=False)
    counts = {}
    for check in ['framework_targeted_tests', 'a011_tests', 'a011_geometry_smoke']:
        shutil.copy2(OUT / (check + '.json'), logs / (check + '.json'))
        shutil.copy2(OUT / (check + '.log'), logs / (check + '.log'))
        if check.endswith('tests'):
            counts[check] = sum(s.startswith('PASSED ') for s in (OUT / (check + '.log')).read_text().splitlines())
    create_json(result / 'TEST_RESULTS.json', {'counts_passed': counts, 'all_exit_codes_zero': True, 'test_order': ['framework_targeted_tests', 'a011_tests', 'a011_geometry_smoke'],
                                            'test_scope': 'Inherited synthetic/reference regressions and adapter rejection/parity tests; no physical campaign'})
    shutil.copy2(manifest, result / 'SOURCE_MANIFEST.json')
    provenance = {'source_tree_sha256': bundle, 'source_manifest_sha256': sha(manifest), 'source_archive': archive.relative_to(ROOT).as_posix(),
                  'source_archive_sha256': sha(archive), 'source_manifest_entries': len(entries),
                  'framework_source': read(OUT / 'framework_source_qualification.json'),
                  'protocol_bundle_sha256': read(root / 'preregistration/GEOMETRY_PROTOCOL.json')['bundle_sha256'],
                  'predecessor_modified': False, 'native_kernel_rebuilt': False}
    create_json(result / 'SOURCE_PROVENANCE.json', provenance)
    evidence = [{'path': p.relative_to(result).as_posix(), 'sha256': sha(p)} for p in sorted(result.rglob('*')) if p.is_file()]
    create_json(result / 'RESULT_EVIDENCE_MANIFEST.json', {'scope': 'Immutable pre-report machine-readable evidence; excludes later PDF/output manifest/archive to avoid circular hashes', 'files': evidence})
    create_json(OUT / 'a011_source_publication.json', {k: v for k, v in provenance.items() if k != 'framework_source'})
    print(json.dumps({'source_tree_sha256': bundle, 'source_zip_sha256': sha(archive), 'source_entries': len(entries), 'tests_passed': counts}, indent=2))


if __name__ == '__main__':
    main()
