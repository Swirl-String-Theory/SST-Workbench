#!/usr/bin/env python3
"""Create a non-destructive E010 PKLSA multi-seed active selection.

Never changes the source atlas, historical verdicts, or admission registry.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

# Logical document key -> authoritative v0.3.1 production-output path.
# The preflight registration files are NOT at the output root.
REQUIRED = {
    'TOPOLOGY_SET.json': 'preflight/TOPOLOGY_SET.json',
    'CAMPAIGN_INDEX.json': 'CAMPAIGN_INDEX.json',
    'FAILED_TOPOLOGIES.json': 'FAILED_TOPOLOGIES.json',
    'IDENTITY_DATABASE_LEDGER.json': 'IDENTITY_DATABASE_LEDGER.json',
    'TOPOLOGY_IDENTITY_ADMISSION.json': 'preflight/TOPOLOGY_IDENTITY_ADMISSION.json',
}

SAFE_ID = re.compile(r'^[A-Za-z0-9_]+$')
VIEW_VERSION = 'v0.3.4'


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def dump_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def need(cond: bool, error: str):
    if not cond:
        raise RuntimeError(error)


def inventory(source: Path, min_seeds: int, min_independent: int):
    docs = {}
    for key, relative_path in REQUIRED.items():
        p = source / relative_path
        need(p.is_file(), f'Missing authoritative file: {p}')
        docs[key] = load_json(p)
    admitted = docs['TOPOLOGY_SET.json']
    campaign = docs['CAMPAIGN_INDEX.json']
    failed_rows = docs['FAILED_TOPOLOGIES.json']
    identity_rows = docs['IDENTITY_DATABASE_LEDGER.json']
    identity_admission = docs['TOPOLOGY_IDENTITY_ADMISSION.json']

    all_ids = admitted['topologies']
    need(len(all_ids) == len(set(all_ids)) == int(admitted['count']), 'Invalid topology set count/duplicates')
    need(all(SAFE_ID.fullmatch(t) for t in all_ids), 'Unsafe topology name in source')
    full_set = set(all_ids)
    passed = campaign['passed']
    failed = campaign['failed']
    need(set(passed).isdisjoint(failed), 'Overlapping historical PASS and FAIL')
    need(set(passed) | set(failed) == full_set, 'Historical campaign does not match admitted set')
    need(int(campaign['passed_count']) == len(passed) and int(campaign['failed_count']) == len(failed), 'Historical campaign counters mismatch')
    need(int(campaign['topology_count']) == len(all_ids), 'Historical campaign topology count mismatch')
    failed_by_id = {row['topology_id']: row for row in failed_rows}
    need(len(failed_by_id) == len(failed_rows) and set(failed_by_id) == set(failed), 'FAILED_TOPOLOGIES mismatch')
    identity_by_id = {r['topology_id']: r for r in identity_rows}
    need(len(identity_by_id) == len(identity_rows) and set(identity_by_id) == full_set, 'Identity ledger mismatch')
    mapped = {r['topology_id']: r for r in identity_admission['mapped']}
    need(set(mapped) == full_set, 'Canonical identity admission mismatch')
    need(int(identity_admission['admitted_count']) == len(all_ids), 'Identity count mismatch')

    rows, active, excluded = [], [], []
    for topo in all_ids:
        folder = source / 'atlas' / topo
        p = folder / 'qualification' / 'summary.json'
        need(p.is_file(), f'Missing qualification summary for {topo}: {p}')
        q = load_json(p)
        need(q.get('topology_id') in (None, topo), f'Topology ID mismatch: {topo}')
        count = q.get('discovered_carriers')
        groups = q.get('independent_group_count')
        need(type(count) is int and count >= 0, f'Invalid seed count for {topo}: {count!r}')
        need(type(groups) is int and 0 <= groups <= count, f'Invalid independent group count for {topo}: {groups!r}')
        need(folder.is_dir(), f'Missing atlas folder: {folder}')
        status = 'PASS' if topo in passed else 'FAIL'
        catalogs = sorted({str(s.get('catalog_ids', '')) for s in q.get('source_matrix', [])
                           if int(s.get('discovered', 0)) > 0 and s.get('catalog_ids')})
        reason = ('NO_SEED' if count == 0 else 'SINGLE_SEED' if count < min_seeds
                  else 'TOO_FEW_SEEDS' if count < min_seeds else
                  'INSUFFICIENT_INDEPENDENT_GROUPS' if groups < min_independent else 'ACTIVE')
        # The independent-group check is a separate, optional stricter criterion.
        keep = count >= min_seeds and groups >= min_independent
        if keep:
            reason = 'ACTIVE'
        entry = {
            'topology_id': topo,
            'discovered_carriers': count,
            'independent_group_count': groups,
            'historical_status': status,
            'source_catalogs': catalogs,
            'selection': 'INCLUDE' if keep else 'EXCLUDE',
            'selection_reason': reason,
            'source_atlas_path': str(folder),
        }
        rows.append(entry)
        (active if keep else excluded).append(entry)
    return docs, rows, active, excluded


def emit(source: Path, target: Path, docs, rows, active, excluded, min_seeds: int, min_independent: int,
         copy_atlas: bool):
    orig_set = docs['TOPOLOGY_SET.json']
    orig_campaign = docs['CAMPAIGN_INDEX.json']
    active_ids = {row['topology_id'] for row in active}
    active_order = [t for t in orig_set['topologies'] if t in active_ids]
    admitted = docs['TOPOLOGY_IDENTITY_ADMISSION.json']

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=target.name + '.INCOMPLETE_', dir=target.parent))
    try:
        dump_json(temp / 'ACTIVE_TOPOLOGY_SET.json', {
            'schema': 'E010-ACTIVE-TOPOLOGY-SELECTION-1',
            'count': len(active_order), 'topologies': active_order,
            'min_discovered_carriers': min_seeds,
            'min_independent_groups': min_independent,
            'original_admitted_count': len(orig_set['topologies']),
            'unmapped_audit_only_count': orig_set.get('unmapped_audit_only_count', 0),
        })
        pass_active = [t for t in orig_campaign['passed'] if t in active_ids]
        fail_active = [t for t in orig_campaign['failed'] if t in active_ids]
        dump_json(temp / 'ACTIVE_CAMPAIGN_INDEX.json', {
            'topology_count': len(active_order),
            'passed_count': len(pass_active), 'failed_count': len(fail_active),
            'passed': pass_active, 'failed': fail_active,
            'note': 'Historical verdicts preserved. These counts concern the selected subset only.',
        })
        dump_json(temp / 'ACTIVE_FAILED_TOPOLOGIES.json', [r for r in docs['FAILED_TOPOLOGIES.json'] if r['topology_id'] in active_ids])
        dump_json(temp / 'ACTIVE_IDENTITY_DATABASE_LEDGER.json', [r for r in docs['IDENTITY_DATABASE_LEDGER.json'] if r['topology_id'] in active_ids])
        dump_json(temp / 'ACTIVE_TOPOLOGY_IDENTITY_ADMISSION.json', {
            **admitted,
            'admitted_count': len(active_order),
            'mapped': [r for r in admitted['mapped'] if r['topology_id'] in active_ids],
            'source_admitted_count': admitted['admitted_count'],
            'policy': 'FILTERED_ACTIVE_VIEW_NOT_CANONICAL_ADMISSION_REPLACEMENT',
        })
        dump_json(temp / 'EXCLUDED_SINGLE_SEED_AND_OTHER.json', excluded)
        dump_json(temp / 'ACTIVE_ATLAS_INDEX.json', {
            'schema': 'E010-ACTIVE-ATLAS-PATH-INDEX-1',
            'source_atlas_root': str(source / 'atlas'),
            'materialized': copy_atlas,
            'carriers': active,
            'warning': 'No source mutation. Consumers must use this index or the optional materialized atlas.',
        })
        with (temp / 'SEED_INVENTORY.csv').open('w', encoding='utf-8', newline='') as out:
            fields = ['topology_id','discovered_carriers','independent_group_count','historical_status',
                      'source_catalogs','selection','selection_reason','source_atlas_path']
            wr = csv.DictWriter(out, fieldnames=fields)
            wr.writeheader()
            for r in rows:
                wr.writerow({**r, 'source_catalogs': '|'.join(r['source_catalogs'])})
        sources = {relative_path: sha256(source / relative_path) for relative_path in REQUIRED.values()}
        dump_json(temp / 'SELECTION_RELEASE.json', {
            'schema': 'E010-MULTISEED-SELECTION-V1',
            'version': VIEW_VERSION,
            'filter_tool_patch': 'v0.3.4-hotfix1',
            'status': 'SELECTION_VIEW_NOT_SCIENCE_REQUALIFICATION',
            'source_output_root': str(source),
            'source_manifest_sha256': sources,
            'policy': f'discovered_carriers >= {min_seeds}, independent_group_count >= {min_independent}',
            'original_topology_count': len(rows),
            'active_topology_count': len(active),
            'excluded_topology_count': len(excluded),
            'excluded_single_seed_count': sum(x['discovered_carriers']==1 for x in excluded),
            'excluded_zero_seed_count': sum(x['discovered_carriers']==0 for x in excluded),
            'selected_historical_pass_count': len(pass_active),
            'selected_historical_fail_count': len(fail_active),
            'new_physical_validation': False,
            'source_mutated': False,
            'atlas_copied': copy_atlas,
        })
        if copy_atlas:
            atlas_target = temp / 'atlas'
            atlas_target.mkdir()
            for item in active:
                src_folder = source / 'atlas' / item['topology_id']
                need(not src_folder.is_symlink(), f'Unsafe symlink atlas: {src_folder}')
                shutil.copytree(src_folder, atlas_target / item['topology_id'])
        need(len(active) + len(excluded) == len(rows), 'Partition failure')
        need(len(pass_active) + len(fail_active) == len(active), 'Active campaign mismatch')
        need(not target.exists(), f'Refusing overwrite: {target}')
        temp.rename(target)
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main():
    ap = argparse.ArgumentParser(description='Non-destructive multi-seed PKLSA active view')
    ap.add_argument('--source', required=True, type=Path, help='E010 v0.3.1 output root (contains CAMPAIGN_INDEX.json)')
    ap.add_argument('--out', type=Path, help='A NEW sibling output folder; never overwritten')
    ap.add_argument('--min-seeds', type=int, default=2, help='Minimum discovered carrier count (default 2)')
    ap.add_argument('--min-independent-groups', type=int, default=0, help='Optional stricter minimum independence groups')
    ap.add_argument('--dry-run', action='store_true', help='Audit selection without writing')
    ap.add_argument('--copy-atlas', action='store_true', help='Materialize retained atlas subfolders (potentially large)')
    args = ap.parse_args()
    need(args.min_seeds >= 2 and args.min_independent_groups >= 0, 'Invalid thresholds')
    source = args.source.resolve(strict=True)
    target = (args.out or (source.parent / 'E010_PKLSA_Multiseed_View_v0.3.4-outputs')).resolve()
    need(source.is_dir(), f'Source directory does not exist: {source}')
    need(source != target and source not in target.parents, 'Output must be outside the source directory')
    need(not target.exists(), f'Refusing overwrite: {target}')

    docs, rows, active, excluded = inventory(source, args.min_seeds, args.min_independent_groups)
    print(f'Historical admitted: {len(rows)}')
    print(f'Active (>= {args.min_seeds} seeds): {len(active)}')
    print(f'Excluded: {len(excluded)}')
    print(f'  Single-seed: {sum(e["discovered_carriers"] == 1 for e in excluded)}')
    print(f'  Zero-seed: {sum(e["discovered_carriers"] == 0 for e in excluded)}')
    print(f'  Additional independence exclusions: {sum(e["discovered_carriers"] >= args.min_seeds for e in excluded)}')
    print('Historical PASS/FAIL among active:',
          sum(e['historical_status'] == 'PASS' for e in active), '/',
          sum(e['historical_status'] == 'FAIL' for e in active))
    if args.dry_run:
        print('DRY RUN: no files written.')
        return
    emit(source, target, docs, rows, active, excluded, args.min_seeds, args.min_independent_groups, args.copy_atlas)
    print(f'View written: {target}')
    print('Original atlas remains unchanged.')
    if not args.copy_atlas:
        print('This is a manifest/index view. Downstream readers must honor ACTIVE_ATLAS_INDEX.json.')


if __name__ == '__main__':
    main()
