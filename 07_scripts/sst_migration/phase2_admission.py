"""Evidence-linked admission contracts; never promotes science or launches runs."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, E010, PRODUCTION, VIEW, read, sha, atomic, locked

OUT = ROOT / '10_docs/migration_v110/phase2_20261026'
E011 = Path('01_research/E_pipelines/E011_sklsa_selected_knot_link_seed_atlas/E011-v0.3.0/E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs')
E013 = Path('01_research/E_pipelines/E013_PKLSA_Cross_Falsifier_Campaign')
A054 = Path('01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1')
A065 = Path('01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3')


def jsonlines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def manifest_entries(root, path):
    doc = read(path)
    entries = doc.get('files', [])
    if isinstance(entries, dict):
        entries = [{'path': p, 'sha256': digest} for p, digest in entries.items()]
    checked = []
    for row in entries:
        p = (root / row['path']).resolve()
        if not p.is_relative_to(root.resolve()):
            raise ValueError('Manifest escape')
        digest = sha(p) if p.is_file() else None
        checked.append({'path': row['path'], 'expected': row['sha256'], 'actual': digest, 'match': digest == row['sha256']})
    return {'manifest_sha256': sha(path), 'entries': len(checked), 'failures': [r for r in checked if not r['match']]}


def providers(geometry):
    by_id = {(r['topology_id'], r['carrier_id']): r for r in geometry}
    index_digest = sha(ROOT / E011 / 'STATIC_READY_INDEX.json')
    anchor_digest = sha(ROOT / E011 / 'STATIC_READY_PROVIDER_ANCHORS.jsonl')
    anchors = jsonlines(ROOT / E011 / 'STATIC_READY_PROVIDER_ANCHORS.jsonl')
    anchor_results = []
    anchor_by_key = {}
    for row in anchors:
        key = (row['topology_id'], row['carrier_id'])
        source = by_id.get(key, {})
        loc = row['source_locator']
        verified = source.get('status') == 'PASS' and loc.get('geometry_sha256') == source.get('geometry_actual_sha256') and loc.get('raw_sha256') == source.get('raw_actual_sha256')
        anchor_results.append({'topology_id': row['topology_id'], 'carrier_id': row['carrier_id'], 'static_seed_id': row.get('static_seed_id'), 'provider_group': row.get('provider_group'),
                               'static_ready': row.get('static_ready'), 'provider_anchor': row.get('provider_anchor'), 'payload_hashes_match_e010': verified})
        anchor_by_key[(row['topology_id'], row.get('static_seed_id'), row['carrier_id'], row.get('provider_group'))] = row
    manifests = []
    for path in sorted((ROOT / E013 / 'runtime/campaigns').glob('*/CROSS_CARRIER_MANIFEST.json')):
        doc = read(path)
        core = {k: v for k, v in doc.items() if k != 'content_sha256_without_self_field'}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        errors = []
        if digest != doc.get('content_sha256_without_self_field'):
            errors.append('SELF_HASH_MISMATCH')
        if doc.get('schema') != 'E013-COMMON-CARRIER-MANIFEST-1':
            errors.append('WRONG_SCHEMA')
        if doc.get('sklsa_release_id') != 'E011-v0.3.0' or doc.get('sklsa_static_index_sha256') != index_digest or doc.get('sklsa_provider_anchors_sha256') != anchor_digest:
            errors.append('CURRENT_E011_BINDING_MISMATCH')
        if doc.get('legacy_falsifier_outputs_used_as_evidence') is not False:
            errors.append('LEGACY_EVIDENCE_OR_MISSING_PROHIBITION')
        groups = defaultdict(set)
        for row in doc.get('carriers', []):
            key = (row['topology_id'], row.get('static_seed_id'), row['carrier_id'], row.get('provider_group'))
            anchor = anchor_by_key.get(key)
            if anchor is None or row.get('geometry_sha256') != anchor.get('source_locator', {}).get('geometry_sha256') or row.get('source_locator') != anchor.get('source_locator'):
                errors.append('ANCHOR_JOIN_MISMATCH:' + row['carrier_id'])
            source = by_id.get((row['topology_id'], row['carrier_id']), {})
            if source.get('status') != 'PASS' or row.get('geometry_sha256') != source.get('geometry_actual_sha256') or row.get('raw_sha256') != source.get('raw_actual_sha256'):
                errors.append('SOURCE_HASH_JOIN_MISMATCH:' + row['carrier_id'])
            groups[row['topology_id']].add(row['provider_group'])
        if len(doc.get('carriers', [])) != doc.get('selected_carrier_count'):
            errors.append('CARRIER_COUNT_MISMATCH')
        manifests.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'profile': doc.get('profile'),
                          'campaign_version': doc.get('campaign_version'), 'selected_carriers': len(doc.get('carriers', [])),
                          'provider_counts': {k: len(v) for k, v in groups.items()},
                          'minimum_two_providers_all_selected_topologies': bool(groups) and all(len(v) >= 2 for v in groups.values()),
                          'binding_status': 'PASS' if not errors else 'FAIL', 'errors': errors,
                          'historical_artifact_only': True})
    member_paths = list((ROOT / '01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier').glob('*/cross_falsifier_contract.json'))
    enabled = []
    for path in member_paths:
        doc = read(path)
        if doc.get('enabled'):
            enabled.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'version': doc.get('version')})
    result = {'e011_pins': {'STATIC_READY_INDEX.json': index_digest, 'STATIC_READY_PROVIDER_ANCHORS.jsonl': anchor_digest},
              'anchor_results': anchor_results, 'historical_e013_manifests': manifests,
              'enabled_a054_member_contracts': enabled, 'duplicate_enabled_versions': len(enabled) > 1,
              'a054_package_integrity': manifest_entries(ROOT / A054, ROOT / A054 / 'PACKAGE_MANIFEST.json'),
              'boundary': 'STATIC_READY geometry/provider authority only; no dynamics or SST claim certification'}
    atomic(OUT / 'a054_provider_dependencies.json', result)
    return result


def contracts(geometry, dependencies):
    by_id = {(r['topology_id'], r['carrier_id']): r for r in geometry}
    active = read(ROOT / VIEW / 'ACTIVE_ATLAS_INDEX.json')['carriers']
    decisions = []
    # Admission thresholds are capability/status predicates, not new numerical
    # scientific tolerances. Existing frozen metric tolerances remain unchanged.
    required = ['L', 'Wr', 'kappa_rms']
    for top in active:
        path = ROOT / PRODUCTION / 'atlas' / top['topology_id'] / 'qualification/geometry_metrics.json'
        for row in read(path)['carriers']:
            key = (top['topology_id'], row['carrier_id'])
            reasons = []
            if by_id.get(key, {}).get('status') != 'PASS':
                reasons.append('PAYLOAD_HASHES_NOT_VERIFIED')
            if row.get('literature_hard_gate_pass') is not True:
                reasons.append('EXISTING_LITERATURE_HARD_GATE_NOT_PASS')
            for metric in required:
                if row.get('observable_status', {}).get(metric) != 'RESOLVED':
                    reasons.append(metric + '_NOT_RESOLVED')
            decisions.append({'topology_id': key[0], 'carrier_id': key[1], 'admit_geometry_diagnostic': not reasons, 'reject_reasons': reasons,
                              'qualification_evidence': path.relative_to(ROOT).as_posix(), 'qualification_evidence_sha256': sha(path)})
    with (OUT / 'a011_geometry_admission.jsonl').open('w', encoding='utf-8') as stream:
        for row in decisions:
            stream.write(json.dumps(row, sort_keys=True) + '\n')
    common = {'schema': 'SST-PILOT-DATASET-ADMISSION-1', 'phase': 'INTEGRITY_AND_ADMISSION_ONLY',
              'no_scientific_promotion': True, 'new_version_creation_authorized_by_contract_alone': False,
              'source_change_policy': 'Rehash before use; any drift blocks. No fallback, synthetic substitution, or historical manifest repair.',
              'framework_requirement': 'Exact admitted source pin and clean instance contract; installed source remains byte-mismatched',
              'failure_treatment': 'Missing inputs NOT_RUN_PREREQUISITE, unresolved physics UNRESOLVED; preserve qualified negative findings',
              'geometry_audit_sha256': sha(OUT / 'geometry_hashes.jsonl')}
    a011 = dict(common, pilot='A011', source_version='v0.3.1',
                permitted_lane='GEOMETRY_AND_IMPLEMENTATION_DIAGNOSTIC_ONLY',
                dataset_pins={str(VIEW / 'ACTIVE_ATLAS_INDEX.json'): sha(ROOT / VIEW / 'ACTIVE_ATLAS_INDEX.json'), str(VIEW / 'SELECTION_RELEASE.json'): sha(ROOT / VIEW / 'SELECTION_RELEASE.json')},
                predicate={'raw_sha256': 'MATCH', 'geometry_sha256': 'MATCH', 'finite_coordinates': True, 'literature_hard_gate_pass': True, 'required_observables': {m: 'RESOLVED' for m in required}},
                normalization='Preserve source coordinate units; A011 declared resampling/centering only. No physical SI length inferred from normalized curves.',
                native_parity={'python': '3.14.3', 'tests_passed': 4, 'backend': '0.3.1-cpp17', 'tolerance_source': 'tests/test_native_parity_v02.py',
                               'velocity_rtol': 1e-11, 'velocity_atol': 1e-12, 'writhe_abs': 1e-11, 'distance_abs': 1e-11},
                decision_ledger='a011_geometry_admission.jsonl', admitted_geometry_records=sum(x['admit_geometry_diagnostic'] for x in decisions), rejected_geometry_records=sum(not x['admit_geometry_diagnostic'] for x in decisions),
                forbidden_claims=['Energy spectrum', 'Gravity', 'Physical thermodynamic closure from geometry alone'],
                additional_physical_inputs='Independently measured or solver-derived energies/gaps/relaxation/couplings and sampled state counts required by existing research_claims; not supplied by this atlas')
    a054 = dict(common, pilot='A054', source_version='v0.5.1', permitted_lane='E013_FROZEN_PROVIDER_STATE_SELECTION',
                input_schema='E013-COMMON-CARRIER-MANIFEST-1', accepted_release='E011-v0.3.0', stage=30,
                dataset_pins=dependencies['e011_pins'], join_keys=['topology_id', 'static_seed_id', 'carrier_id', 'provider_group', 'source_geometry_sha256'],
                predicate={'manifest_self_hash': 'MATCH', 'e011_index_and_anchor_hashes': 'MATCH', 'raw_and_geometry_hashes': 'MATCH', 'legacy_evidence': False, 'independent_provider_groups_min': 2},
                manifest_designation='Historical manifests audited; no historical manifest is automatically selected for a fresh migrated run. Create and freeze a new current binding after member-version selection is fixed.',
                smoke_exception='BASIC uses one provider per topology in E013 config; can qualify execution only, cannot close cross-provider science.',
                enabled_member_version_check={'enabled_versions': [x['version'] for x in dependencies['enabled_a054_member_contracts']], 'duplicate_enabled_versions': dependencies['duplicate_enabled_versions']},
                unresolved=['Framework locator still pins v1.0.6', 'Runtime manifest loader does not validate E013 self-hash and current E011 index/anchor bindings', 'Current source manifest has two documentation byte mismatches', 'L2a1 has one provider in historical FULL/CERTIFY manifests; cross-provider closure remains unavailable there', 'Per-observable stationarity/Hessian/ringdown gates still require a future isolated run'],
                forbidden_claims=['STATIC_READY implies DYNAMICS_READY', 'Variational selection is physical dissipation'])
    seals = read(OUT / 'a065_seals.json')
    fremlin = next(r for r in geometry if r['carrier_id'] == 'CAR_d8a316361e0941af')
    a065 = dict(common, pilot='A065', source_version='v0.4.3', permitted_lanes=['SEALED_HISTORICAL_FILAMENT_DIAGNOSTIC', 'SYNTHETIC_NUMERICAL_METHOD_CONTROLS'],
                dataset_pins={str(A065 / 'seals' / (x['dataset'] + '.seal.json')): x['seal_sha256'] for x in seals['datasets']},
                global_commitment_sha256=seals['global_commitment_sha256'],
                predicate={'dataset_file_sets_and_hashes': 'EXACT_MATCH', 'seal_self_hashes': 'MATCH', 'global_seal_bindings': 'MATCH', 'private_reveal_material_read': False, 'blind_results_immutable': True},
                fremlin_geometry={'carrier_id': fremlin['carrier_id'], 'raw_sha256': fremlin['raw_actual_sha256'], 'geometry_sha256': fremlin['geometry_actual_sha256'], 'status': fremlin['status'], 'authority': 'GEOMETRY_ONLY'},
                scientific_boundary='One sourced lineage plus filament/synthetic controls. A003 Gaussian initial data and GPU diagnostics remain DEVELOPMENT; not physical Euler/PKLSA/Casimir certification.',
                existing_framework_bridge={'pin': '1.0.10', 'static_regressions_passed': 3, 'legacy_commitment_retained': True},
                blocked_by=['Current v0.4.3 source manifest has three byte mismatches', 'Physical source and independent field evidence absent', 'Fresh successor instance and commitment review not performed; existing v0.4.3 bridge already pins v1.0.10'],
                reveal_policy='No reveal in Phase 2. Future reveal reads fixed blind outputs only; no target access or post-reveal threshold tuning.')
    for doc in [a011, a054, a065]:
        atomic(OUT / (doc['pilot'] + '_DATASET_ADMISSION.json'), doc)
    return [a011, a054, a065]


def main():
    geometry = jsonlines(OUT / 'geometry_hashes.jsonl')
    dependencies = providers(geometry)
    docs = contracts(geometry, dependencies)
    print(json.dumps({'admission_contracts': [d['pilot'] for d in docs], 'a011_eligible_geometry': docs[0]['admitted_geometry_records'],
                      'e011_anchors': len(dependencies['anchor_results']), 'e013_binding_statuses': dict(Counter(m['binding_status'] for m in dependencies['historical_e013_manifests'])),
                      'a054_enabled_members': len(dependencies['enabled_a054_member_contracts'])}, indent=2))


if __name__ == '__main__':
    main()
