"""Write-once framework source qualification, then an isolated A011 successor."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, checked_child, now

OUT = ROOT / '10_docs/migration_v110/phase3_20261026'
PHASE2 = ROOT / '10_docs/migration_v110/phase2_20261026'
FAMILY = ROOT / '01_research/A_falsifiers/A011_maxwell_1_kinetic_energy'


def create_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def qualify():
    OUT.mkdir(parents=True, exist_ok=True)
    history = read(PHASE2 / 'canonical_distribution_integrity.json')
    archive_path = ROOT / history['path']
    digest = sha(archive_path)
    if digest != history['sha256']:
        raise RuntimeError('Canonical distribution changed since Phase 2')
    selected = ROOT / '06_templates/SST_Falsifier_Framework/qualified_sources' / ('sha256-' + digest)
    selected.mkdir(parents=True, exist_ok=False)
    shutil.copy2(archive_path, selected / 'distribution.zip')
    with zipfile.ZipFile(archive_path) as archive:
        prefix = 'SST_Falsifier_Framework_v1.0.10/'
        manifest = json.loads(archive.read(prefix + 'PACKAGE_MANIFEST.json'))
        if len(manifest['files']) != 112:
            raise RuntimeError('Expected exactly 112 canonical manifest entries')
        verification = []
        for entry in manifest['files']:
            actual = hashlib.sha256(archive.read(prefix + entry['path'])).hexdigest()
            if actual != entry['sha256']:
                raise RuntimeError('Unexplained canonical archive drift: ' + entry['path'])
            verification.append({'path': entry['path'], 'sha256': actual, 'status': 'PASS'})
        for info in archive.infolist():
            dest = checked_child(selected, info.filename)
            if not info.filename.startswith(prefix):
                raise RuntimeError('Unexpected canonical archive prefix')
            if stat.S_ISLNK(info.external_attr >> 16):
                raise RuntimeError('Archive links not admitted')
            if info.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open('xb') as stream:
                    stream.write(archive.read(info))
    framework = selected / prefix.rstrip('/')
    for entry in manifest['files']:
        if sha(checked_child(framework, entry['path'])) != entry['sha256']:
            raise RuntimeError('Extraction drift: ' + entry['path'])
    captured = OUT / 'preserved_local_framework_variant'
    captured.mkdir(exist_ok=False)
    installed = ROOT / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10'
    for name in ['docs/DD32_FP32X2.md', 'PACKAGE_MANIFEST.json', 'MANIFEST_SHA256.txt', 'CANONICAL_FREEZE.json']:
        dst = captured / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(installed / name, dst)
    pins = snapshot(framework)
    tree_sha = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    qualification = {'schema': 'SST-FRAMEWORK-SOURCE-QUALIFICATION-1', 'created_utc': now(), 'status': 'PASS',
                     'selected_source': framework.relative_to(ROOT).as_posix(), 'distribution_sha256': digest,
                     'manifest_sha256': sha(framework / 'PACKAGE_MANIFEST.json'), 'source_tree_sha256': tree_sha,
                     'manifest_entries_verified': 112, 'verification': verification, 'all_files_sha256': pins,
                     'installed_legacy_source_modified': False, 'local_variant_sha256': sha(captured / 'docs/DD32_FP32X2.md'),
                     'qualified_variant_sha256': sha(framework / 'docs/DD32_FP32X2.md'),
                     'immutability': 'Create-once, content-addressed distribution and complete byte inventory; files read-only, reverified on every adapter invocation. OS administrators can still change filesystem permissions.',
                     'no_physical_certification': True}
    create_json(selected / 'QUALIFICATION.json', qualification)
    create_json(OUT / 'framework_source_qualification.json', qualification)
    for p in selected.rglob('*'):
        if p.is_file():
            os.chmod(p, stat.S_IREAD)
    os.chmod(OUT / 'framework_source_qualification.json', stat.S_IREAD)
    print(json.dumps({k: qualification[k] for k in ['status', 'selected_source', 'distribution_sha256', 'manifest_sha256', 'source_tree_sha256', 'manifest_entries_verified']}, indent=2))


def clone():
    qualified = read(OUT / 'framework_source_qualification.json')
    framework = ROOT / qualified['selected_source']
    if qualified['status'] != 'PASS' or qualified['manifest_entries_verified'] != 112:
        raise RuntimeError('3A is not qualified')
    for name, digest in qualified['all_files_sha256'].items():
        if sha(checked_child(framework, name)) != digest:
            raise RuntimeError('Qualified source drift before clone: ' + name)
    source, destination = FAMILY / 'A011-v0.3.1', FAMILY / 'A011-v0.4.0'
    if destination.exists():
        raise FileExistsError(destination)
    before = {'A011-v0.3.1': snapshot(source)}
    # Protect the explicitly excluded pilot source packages and their FAMILY metadata.
    for cid, family, version in [('A054', 'A054_nucleon_topology_architecture_blind_falsifier', 'A054-v0.5.1'),
                                  ('A065', 'A065_Triadic_Casimir_Blind', 'A065-v0.4.3')]:
        path = ROOT / '01_research/A_falsifiers' / family
        # Complete code/data/metadata snapshot, excluding bulky historical run/output
        # copies and private escrow contents. Those locations are never written here.
        pins = {}
        for p in sorted((path / version).rglob('*')):
            rel = p.relative_to(path / version)
            if any(x in {'.venv', '__pycache__', '.pytest_cache', 'runs', 'exports', 'private', 'private_reveal'} or x.endswith('-outputs') for x in rel.parts):
                continue
            if p.is_file():
                pins[rel.as_posix()] = sha(p)
        before[cid] = {'path': (path / version).relative_to(ROOT).as_posix(), 'files': pins, 'family_sha256': sha(path / 'FAMILY.yaml')}
    create_json(OUT / 'preservation_before.json', before)
    excluded = {'.venv', '.git', '__pycache__', '.pytest_cache', 'build', 'outputs', 'runs', 'exports', 'MANIFEST.sha256', 'BUILD_INFO.json'}
    def ignore(folder, names):
        return [n for n in names if n in excluded or n.endswith(('.pyc', '.zip', '.zip.sha256', '.pdf')) or n.endswith('.egg-info')]
    shutil.copytree(source, destination, ignore=ignore)
    provenance = destination / 'provenance'
    provenance.mkdir()
    for name in ['MANIFEST.sha256', 'BUILD_INFO.json', 'README.md']:
        shutil.copy2(source / name, provenance / ('PARENT_' + name))
    create_json(provenance / 'PARENT_SOURCE.json', {'catalog_id': 'A011', 'version': 'v0.3.1', 'source': source.relative_to(ROOT).as_posix(),
                'all_parent_files_sha256': before['A011-v0.3.1'], 'scope': 'Parent preserved; only geometry/native routines inherited, no old outputs imported as scientific evidence'})
    for name in ['A011_DATASET_ADMISSION.json', 'a011_geometry_admission.jsonl', 'geometry_hashes.jsonl']:
        shutil.copy2(PHASE2 / name, provenance / name)
    create_json(destination / 'FRAMEWORK_SOURCE_PIN.json', qualified)
    (destination / '.sst_framework_root').write_text(os.path.relpath(framework, destination) + '\n', encoding='utf-8')
    project = read(destination / 'project.json')
    project['version'] = 'v0.4.0'
    project['migration_scope'] = 'Qualified Framework v1.0.10 geometry diagnostic adapter; no physical certification'
    (destination / 'project.json').write_text(json.dumps(project, indent=2) + '\n', encoding='utf-8')
    p = destination / 'pyproject.toml'
    p.write_text(p.read_text(encoding='utf-8').replace('version = "0.3.1"', 'version = "0.4.0"'), encoding='utf-8')
    p = destination / 'src/maxwell_sst_falsifier/__init__.py'
    p.write_text(p.read_text(encoding='utf-8').replace('__version__="0.3.1"', '__version__="0.4.0"'), encoding='utf-8')
    p = destination / 'src/maxwell_sst_falsifier/cli.py'
    p.write_text(p.read_text(encoding='utf-8').replace('Falsifier v0.3.1', 'Falsifier v0.4.0'), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['qualify', 'clone'])
    globals()[p.parse_args().command]()
