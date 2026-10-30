"""Reconcile inventory metadata without asserting scientific qualification.

Uses existing catalog parser and hierarchy artifact scanner. Does not renumber,
move or modify research versions, datasets, results, or historical manifests.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, atomic
sys.path.insert(0, str(ROOT / '07_scripts'))
import build_catalog_index as bci
import build_family_hierarchy as bh

OUT = ROOT / '10_docs/migration_v110/phase2_20261026'
BACKUPS = OUT / 'registry_before'


def preserve(path):
    dest = BACKUPS / path.relative_to(ROOT)
    if dest.exists():
        return  # Preserve original baseline when resuming an interrupted audit.
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as stream:
        stream.write(path.read_bytes())


def versions(path, cid):
    found = []
    for p in sorted(path.iterdir()):
        if not p.is_dir() or p.is_symlink():
            continue
        # Keep non-standard legacy releases visible, but never confuse output,
        # report-only, work/plan folders with a software release.
        if p.name.startswith(cid + '-v'):
            found.append(p)
        elif re.search(r'_v\d+[._]\d+', p.name) and any((p / n).is_file() for n in ['README.md', 'project.json', 'run_all.cmd', 'pyproject.toml']):
            found.append(p)
    return found


def duplicate_evidence(canonical, alternate):
    rows = []
    for p in sorted(alternate.rglob('*')):
        if p.is_file():
            q = canonical / p.relative_to(alternate)
            rows.append({'path': p.relative_to(alternate).as_posix(), 'alternate_sha256': sha(p),
                         'canonical_sha256': sha(q) if q.is_file() else None,
                         'match': q.is_file() and sha(p) == sha(q)})
    return rows


def main():
    if (OUT / 'registry_reconciliation.json').exists():
        raise FileExistsError('Completed registry reconciliation is create-once')
    OUT.mkdir(parents=True, exist_ok=True)
    hp = ROOT / '10_docs/registry/family_hierarchy.json'
    cp = ROOT / '10_docs/registry/catalog_index.json'
    h, c = read(hp), read(cp)
    before_h, before_c = deepcopy(h), deepcopy(c)
    changes = []
    paths = sorted((ROOT / '01_research/A_falsifiers').glob('A[0-9][0-9][0-9]_*'))
    alternatives = {
        'A059_SST_Quantum_Number_Rosetta_Mega_Falsifier2': ('A059_SST_Quantum_Number_Rosetta_Mega_Falsifier', 'ARTIFACT_ONLY_LOCATION_WITH_DIFFERENT_PDF_RETAINED'),
        'A067_SwirlClock_BohrDelayAction_v0.1.0_BLIND': ('A067_SwirlClock_BohrDelayAction', 'BYTE_IDENTICAL_DUPLICATE_LOCATION'),
    }
    exceptions = []
    for path in paths:
        if path.name in alternatives:
            target, reason = alternatives[path.name]
            comparison = duplicate_evidence(path.parent / target, path)
            exceptions.append({'path': path.relative_to(ROOT).as_posix(), 'canonical_family_path': (path.parent / target).relative_to(ROOT).as_posix(),
                               'reason': reason, 'file_comparison': comparison, 'action': 'Preserve location and all artifacts; not a second catalog identity'})
            continue
        cid = path.name[:4]
        family = path / 'FAMILY.yaml'
        baseline = BACKUPS / family.relative_to(ROOT)
        old = baseline.read_text(encoding='utf-8-sig') if baseline.exists() else (family.read_text(encoding='utf-8-sig') if family.is_file() else None)
        if old is not None and 'reconciliation_note: "Phase 2 inventory only;' in old:
            old = None  # File created by this operation before an interruption.
        meta = bci.parse_family(family) if old is not None else {}
        if baseline.exists():
            # The parser needs a repository-relative source path; restore only our
            # interrupted metadata edit to its exact saved baseline before parsing.
            family.write_bytes(baseline.read_bytes())
            meta = bci.parse_family(family)
        normalized_old = old
        if old is not None:
            for entry in meta.get('versions', []):
                if not entry.get('directory') and (path / (cid + '-' + entry['id'])).is_dir():
                    entry['directory'] = cid + '-' + entry['id']
                    normalized_old = re.sub(r'^(  - id: ' + re.escape(entry['id']) + r')[ \t]*$',
                                            r'\1\n    directory: ' + json.dumps(entry['directory']), normalized_old, flags=re.M)
        disk = versions(path, cid)
        declared = {v.get('directory') for v in meta.get('versions', [])}
        additions = []
        conflicts = []
        for vp in disk:
            if vp.name in declared:
                continue
            match = re.search(r'v\d+[._]\d+[._]\d+(?:-alpha\.\d+)?(?:-r\d+)?$', vp.name)
            if not match:
                conflicts.append(vp.name)
                continue
            additions.append({'id': match[0], 'directory': vp.name, 'qualification': 'NOT_EVALUATED'})
        if old is None:
            name = path.name[5:].replace('_', ' ')
            # Empty latest deliberately avoids inventing canonical release authority
            # for an imported family. Pilot release pointer has explicit evidence.
            latest = 'v0.4.3' if cid == 'A065' else ''
            text = f'catalog_id: {cid}\ndomain: 01_research\nletter: A_falsifiers\nslug: {path.name[5:]}\nname: {json.dumps(name)}\nkind: falsifier\nstatus: inventoried_unqualified\nlatest: {json.dumps(latest)}\noutput_prefix: ""\n'
            text += 'versions:\n' if additions else 'versions: []\n'
            for row in additions:
                text += ''.join(['  - id: ' + row['id'] + '\n', '    directory: ' + json.dumps(row['directory']) + '\n', '    qualification: NOT_EVALUATED\n'])
            text += 'variants: []\nlegacy_paths: []\nreconciliation_note: "Phase 2 inventory only; no scientific qualification or production admission. Latest selection remains pending except explicitly documented pilot release."\n'
            mode = 'CREATED'
        else:
            text = normalized_old
            for key, value in [('domain', '01_research'), ('letter', 'A_falsifiers')]:
                if not re.search('^' + key + ':', text, re.M):
                    text += f'\n{key}: {value}\n'
            if cid == 'A054':
                # REGISTRY_INTEGRATION.md explicitly supersedes v0.5.0 for future
                # E013 runs. This is software release selection, not science status.
                text = re.sub(r'^latest:.*$', 'latest: v0.5.1', text, flags=re.M)
            if additions:
                lines = ['  - id: ' + row['id'] + '\n    directory: ' + json.dumps(row['directory']) + '\n    qualification: NOT_EVALUATED\n' for row in additions]
                match = re.search(r'^versions:\s*\[\]\s*$', text, re.M)
                if match:
                    text = text[:match.start()] + 'versions:\n' + ''.join(lines) + text[match.end():]
                elif re.search(r'^versions:\s*$', text, re.M):
                    start = re.search(r'^versions:\s*$', text, re.M).end()
                    end = re.search(r'^\S', text[start:], re.M)
                    insertion = start + end.start() if end else len(text)
                    text = text[:insertion].rstrip('\n') + '\n' + ''.join(lines) + text[insertion:]
                else:
                    text += '\nversions:\n' + ''.join(lines)
            mode = 'UPDATED'
        if text != old:
            if family.exists():
                preserve(family)
            family.write_text(text, encoding='utf-8', newline='\n')
            changes.append({'path': family.relative_to(ROOT).as_posix(), 'action': mode,
                            'before_sha256': None if old is None else sha(BACKUPS / family.relative_to(ROOT)),
                            'after_sha256': sha(family), 'new_inventory_entries': additions, 'unresolved_directory_names': conflicts})
        meta = bci.parse_family(family)
        # Preserve additional index metadata while refreshing the parser-supported
        # release list from the reconciled FAMILY record.
        catalog_entry = deepcopy(c['by_domain'].setdefault('01_research', {}).get(cid, {}))
        catalog_entry.update(meta)
        catalog_entry['reconciliation_scope'] = 'inventory_only_not_scientific_admission'
        if conflicts:
            catalog_entry['unresolved_directory_names'] = conflicts
        c['by_domain']['01_research'][cid] = catalog_entry
        node = deepcopy(h['hierarchy'].setdefault('01_research', {}).setdefault('A_falsifiers', {}).get(cid, {}))
        node.update({k: meta[k] for k in ['catalog_id', 'slug', 'name', 'kind', 'status', 'domain', 'letter', 'path', 'latest', 'output_prefix', 'legacy_paths']})
        node['declared_versions'] = meta['versions']
        declared_by_dir = {x['directory']: x for x in meta['versions']}
        on_disk = {}
        for vp in disk:
            if vp.name not in declared_by_dir:
                continue
            row = declared_by_dir[vp.name]
            token = vp.name[len(cid) + 1:] if vp.name.startswith(cid + '-') else vp.name
            on_disk[token] = {'directory': vp.name, 'path': vp.relative_to(ROOT).as_posix(), 'declared': True,
                              'expected_outputs_zip': bh.expected_outputs_zip(meta['output_prefix'], row['id']),
                              'expected_zip_present': False, **bh.collect_version_artifacts(vp)}
            expected = on_disk[token]['expected_outputs_zip']
            on_disk[token]['expected_zip_present'] = bool(expected and expected in on_disk[token]['outputs_zips'])
        node.update({'versions_on_disk': on_disk, 'missing_declared_versions': [v for v in meta['versions'] if not (path / v['directory']).is_dir()],
                     'undeclared_version_dirs': conflicts, 'other_dirs': sorted(p.name for p in path.iterdir() if p.is_dir() and p not in disk),
                     'reconciliation_scope': 'inventory_only_not_scientific_admission'})
        h['hierarchy']['01_research']['A_falsifiers'][cid] = node
        # by_catalog_id is historically a bare-ID map with cross-domain collisions.
        # Update only entries already pointing to this family or absent IDs.
        flat = h['by_catalog_id'].get(cid)
        if flat is None or flat.get('path') == meta['path']:
            h['by_catalog_id'][cid] = {'path': meta['path'], 'domain': '01_research', 'letter': 'A_falsifiers', 'latest': meta['latest'],
                                      'output_prefix': meta['output_prefix'], 'version_dirs': [v['directory'] for v in on_disk.values()],
                                      'outputs_zips': [z for v in on_disk.values() for z in v['outputs_zips']]}
    for doc in [h, c]:
        doc['phase2_reconciliation'] = {'scope': '01_research/A_falsifiers only; inventory metadata, not science status',
                                       'evidence': '10_docs/migration_v110/phase2_20261026/registry_reconciliation.json',
                                       'noncanonical_locations': exceptions}
    c['families'] = sum(len(d) for d in c['by_domain'].values())
    c['versions'] = sum(len(e.get('versions', [])) for d in c['by_domain'].values() for e in d.values())
    nodes = [n for d in h['hierarchy'].values() for letter in d.values() for n in letter.values()]
    h['family_count'] = len(nodes)
    h['version_count_declared'] = sum(len(n.get('declared_versions', [])) for n in nodes)
    h['version_count_on_disk'] = sum(len(n.get('versions_on_disk', {})) for n in nodes)
    h['next_catalog_ids']['A_falsifiers'] = 'A075'
    for path, doc in [(hp, h), (cp, c)]:
        preserve(path)
        atomic(path, doc)
    # Other domains and research letters must remain byte-equivalent in structure.
    for domain, entries in before_c['by_domain'].items():
        if domain != '01_research':
            assert c['by_domain'][domain] == entries
        else:
            for cid, entry in entries.items():
                if entry.get('letter') != 'A_falsifiers':
                    assert c['by_domain'][domain][cid] == entry
    for domain, letters in before_h['hierarchy'].items():
        for letter, entries in letters.items():
            if (domain, letter) != ('01_research', 'A_falsifiers'):
                assert h['hierarchy'][domain][letter] == entries
    atomic(OUT / 'registry_reconciliation.json', {'changes': changes, 'noncanonical_locations': exceptions,
           'canonical_a_families': len(h['hierarchy']['01_research']['A_falsifiers']),
           'created_family_files': sum(x['action'] == 'CREATED' for x in changes), 'updated_family_files': sum(x['action'] == 'UPDATED' for x in changes),
           'historical_results_modified': False, 'non_a_index_sections_preserved': True,
           'unreviewed_latest_policy': 'Empty latest retained for newly inventoried nonpilot families; no automatic latest-by-number promotion',
           'pilot_latest_evidence': {'A054': 'A054-v0.5.1/REGISTRY_INTEGRATION.md', 'A065': 'A065-v0.4.3/README_V043.md'}})
    print(json.dumps({'metadata_files_changed': len(changes), 'canonical_a_families': len(h['hierarchy']['01_research']['A_falsifiers'])}))


if __name__ == '__main__':
    main()
