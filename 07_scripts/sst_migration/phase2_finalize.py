"""Publish Phase 2 gate decisions and attach them to the existing paused queue."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha, atomic, locked

OUT = ROOT / '10_docs/migration_v110/phase2_20261026'
STATE = ROOT / '10_docs/migration_v110/pilot_20261026'


def main():
    if (OUT / 'gate_overview.json').exists():
        raise FileExistsError('Phase 2 final decisions already published')
    stamp = datetime.now(timezone.utc).isoformat()
    framework = read(OUT / 'framework_integrity.json')
    geo = read(OUT / 'geometry_integrity.json')
    registry = read(OUT / 'registry_reconciliation.json')
    providers = read(OUT / 'a054_provider_dependencies.json')
    seals = read(OUT / 'a065_seals.json')
    h = read(ROOT / '10_docs/registry/family_hierarchy.json')
    families = h['hierarchy']['01_research']['A_falsifiers']
    pending_latest = [k for k, v in families.items() if not v['latest']]
    conflict_dirs = [{'family': x['path'].split('/')[-2], 'directories': x['unresolved_directory_names']} for x in registry['changes'] if x['unresolved_directory_names']]
    patches = [
        {'id': 'P01', 'stage': 'BEFORE_PILOT_MIGRATION', 'kind': 'SOURCE_RESTORATION_OR_CLEAN_SOURCE_SELECTION',
         'targets': ['06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/docs/DD32_FP32X2.md'],
         'action': 'Use exact sealed RC2/canonical document bytes after retaining the captured local variant, or use a separately admitted clean distribution. Do not regenerate the historical manifest.',
         'acceptance': 'Installed framework PACKAGE_MANIFEST all 112 files match, or a clean admitted source pin is explicitly selected; preserved before/after hashes remain available.'},
        {'id': 'P02', 'stage': 'BEFORE_A054_MIGRATION', 'kind': 'PILOT_SOURCE_ADMISSION',
         'targets': ['01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1/FALSIFICATION_PLAN.md', '01_research/A_falsifiers/A054_nucleon_topology_architecture_blind_falsifier/A054-v0.5.1/README.md'],
         'action': 'Admit the pinned internally consistent source ZIP, preserving the local Markdown rendering variant; record source selection rather than changing its historical PACKAGE_MANIFEST.',
         'acceptance': '59/59 admitted source files match the chosen source manifest; Downloads provenance limit explicitly accepted or independently anchored.'},
        {'id': 'P03', 'stage': 'BEFORE_A065_MIGRATION', 'kind': 'PILOT_SOURCE_ADMISSION',
         'targets': ['01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/README_V043.md', '01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/docs/QUALIFICATION_V031.md', '01_research/A_falsifiers/A065_Triadic_Casimir_Blind/A065-v0.4.3/triadic/report_tex.py'],
         'action': 'Admit the pinned source ZIP or preserve exact source variants in a reviewed successor. The Python difference is CRLF/LF only; Markdown differences are math delimiters/EOF. Keep all historical manifests unchanged.',
         'acceptance': '159/159 admitted v0.4.3 source entries match; source ZIP provenance limitation documented; all three original dataset seals still verify.'},
        {'id': 'P04', 'stage': 'FUTURE_A054_SUCCESSOR_AFTER_SOURCE_GATES', 'kind': 'RUNTIME_ADMISSION_HARDENING',
         'targets': ['A054 successor/.sst_framework_root', 'A054 successor/a054_state/pklsa.py', 'A054 successor/source_contract.json', 'A054 successor/tests/test_e013_manifest.py'],
         'action': 'Pin qualified v1.0.10 instead of the current v1.0.6 locator; validate manifest self-hash, selected count, E011 index/anchor digests, source-locator joins, raw/geometry hashes, and the exact E010 loader version before source loading. Add tamper and drift rejection tests.',
         'acceptance': 'Each edited binding/hash is rejected in an isolated regression; unchanged valid manifest loads; stage 30 and no-legacy-evidence rules retained.'},
        {'id': 'P05', 'stage': 'FUTURE_A011_SUCCESSOR_AFTER_SOURCE_GATES', 'kind': 'FAMILY_ADAPTER',
         'targets': ['A011 successor/framework pipeline', 'A011 successor/source and science contracts', 'A011 successor/tests'],
         'action': 'Bind A011_DATASET_ADMISSION.json and the carrier decision ledger; port unchanged geometry definitions into v1.0.10 observed/execution/qualification outputs; preserve separate geometry/proxy and physical/thermodynamic lanes.',
         'acceptance': 'Admitted geometry smoke and Python/native parity pass with existing tolerances; missing physical inputs stay unresolved and cannot promote gravity or energy claims.'},
        {'id': 'P06', 'stage': 'FUTURE_A065_SUCCESSOR_AFTER_SOURCE_GATES', 'kind': 'BLIND_SUCCESSOR_QUALIFICATION',
         'targets': ['A065 successor/framework_bridge/install.py', 'A065 successor/framework_bridge/pipeline.py', 'A065 successor/preregistration', 'A065 successor/tests'],
         'action': 'Reuse the existing v1.0.10 bridge, remove stale version descriptions in the successor, bind the admitted source/adapter pins, and test unique run retention and negative-prerequisite qualification without target access or an expensive volume campaign.',
         'acceptance': 'Dataset seals and prior negatives remain unchanged; new commitment is separate; diagnostic PASS never closes physical G3/G4/G8; reveal remains separate.'},
        {'id': 'P07', 'stage': 'BEFORE_PHYSICAL_OR_CROSS_PROVIDER_CLAIMS', 'kind': 'MISSING_SCIENTIFIC_INPUTS_NOT_A_TOLERANCE_PATCH',
         'targets': ['A011 physical input contract', 'A054 L2a1 provider admission', 'A065 physical source/heldout contract'],
         'action': 'Supply independently qualified physical observables for A011/A065 and a second genuinely independent admitted L2a1 provider, or retain the affected claims/topology as unresolved. Never synthesize evidence or weaken minimum-provider rules.',
         'acceptance': 'Per-observable provenance, units, independence and convergence evidence exists; otherwise the scientific gate remains unresolved. Not necessary for a correctly labelled geometry-only software smoke.'},
        {'id': 'P08', 'stage': 'BEFORE_BULK_QUEUE_RELEASE', 'kind': 'REMAINING_REGISTRY_REVIEW',
         'targets': ['10_docs/registry/catalog_index.json', '10_docs/registry/family_hierarchy.json', 'Affected FAMILY.yaml files listed in registry_reconciliation.json'],
         'action': 'Review unresolved suffix/work/report directories and select canonical latest for imported nonpilot families from release evidence. Fix the generic hierarchy scanner duplicate-version-ID handling before relying on a full rebuild.',
         'acceptance': 'Each remaining location has an explicit disposition and each bulk job has an evidence-backed source version. Preserve all archive/report variants.',
         'pending_latest_ids': pending_latest, 'unresolved_directory_groups': conflict_dirs},
        {'id': 'P09', 'stage': 'AFTER_THREE_PILOTS_VALIDATED', 'kind': 'PRODUCTION_WORKER_AND_SCHEDULING',
         'targets': ['07_scripts/sst_migration production worker', 'Central durable queue/event store', 'Scheduled configuration'],
         'action': 'Implement reviewed per-family execution adapters, transactional claims/recovery, bounded smoke budgets, report-only PDF publication and retention tests. Configure scheduling only after pilot acceptance.',
         'acceptance': 'One falsifier per invocation; crash/retry cannot overwrite versions/results; three gate axes preserved; Scheduled stays disabled until actual acceptance.'},
    ]
    atomic(OUT / 'required_patches.json', {'schema': 'SST-PHASE2-PATCH-LIST-1', 'patches': patches})
    checks = [
        {'id': 'FRAMEWORK_RC2_AUTHENTICITY', 'status': 'PASS', 'evidence': 'framework_integrity.json', 'detail': f"Exact frozen ZIP digest; {len(framework['archive_entries'])} internal manifest entries verified."},
        {'id': 'FRAMEWORK_INSTALLED_BYTES', 'status': 'FAIL_EXPLAINED_FORMATTING_DRIFT', 'evidence': 'framework/DD32_FP32X2.diff', 'detail': 'Authentic source found; installed document still differs. Historical manifest unchanged.'},
        {'id': 'REGISTRY_CANONICAL_IDENTITIES', 'status': 'PASS_WITH_OPEN_NONPILOT_ITEMS', 'evidence': 'registry_reconciliation.json', 'detail': '73 canonical A families; 25 FAMILY files created, 7 updated; two preserved noncanonical locations.'},
        {'id': 'PKLSA_RAW_AND_GEOMETRY_HASHES', 'status': 'PASS', 'evidence': 'geometry_hashes.jsonl', 'detail': '4497/4497 records; 2282 distinct raw files; 2312 active-view records. All finite; source-stability rehash passed.'},
        {'id': 'A011_GEOMETRY_NATIVE_PARITY', 'status': 'PASS', 'evidence': 'a011_geometry_parity.log', 'detail': '4 targeted tests, Python 3.14.3 and existing C++17 backend; no automatic rebuild.'},
        {'id': 'A054_E011_E013_BINDINGS', 'status': 'PASS_INPUT_INTEGRITY_ONLY', 'evidence': 'a054_provider_dependencies.json', 'detail': '47/47 anchors and 13/13 historical manifests match; exactly one enabled A054 member.'},
        {'id': 'A054_RUNTIME_ADMISSION', 'status': 'BLOCKED_PATCH_REQUIRED', 'evidence': 'A054_DATASET_ADMISSION.json', 'detail': 'Current locator v1.0.6; runtime omits E013 self/E011-binding checks; L2a1 has one provider.'},
        {'id': 'A065_SEALS_AND_COMMITMENT', 'status': 'PASS_INTEGRITY_ONLY', 'evidence': 'a065_seals.json', 'detail': 'D01/D02/D03 seals, seven files and global bindings match; no private targets opened.'},
        {'id': 'A065_EXISTING_V110_BRIDGE', 'status': 'PASS_STATIC_CHECKS_ONLY', 'evidence': 'a065_framework_static_tests.log', 'detail': 'Existing bridge pins v1.0.10; three static regressions pass, no solver execution.'},
        {'id': 'PILOT_INSTALLED_SOURCE_BYTES', 'status': 'FAIL_EXPLAINED_FORMATTING_DRIFT', 'evidence': 'pilot_source_archive_comparisons.json', 'detail': 'A054: two Markdown files. A065: two Markdown files and CRLF/LF-only report_tex.py. Internally verified source ZIPs preserved as references.'},
        {'id': 'MIGRATED_EXECUTION', 'status': 'NOT_RUN', 'detail': 'No successor versions created or migrated.'},
        {'id': 'SCIENTIFIC_CERTIFICATION', 'status': 'NOT_RUN', 'detail': 'No scientific gate promoted; geometry integrity and software tests are not physical qualification.'},
        {'id': 'SCHEDULED', 'status': 'DISABLED', 'detail': 'No schedule created, activated or changed.'},
    ]
    pilots = {
        'A011': {'resolved': ['PKLSA raw/geometry hash audit', 'Explicit geometry-only admission contract', 'Targeted geometry and native parity'],
                 'remaining': ['FRAMEWORK_INSTALLED_BYTE_DRIFT', 'NEW_INSTANCE_AND_ADAPTER_NOT_QUALIFIED', 'PHYSICAL_INPUT_ADMISSION_UNRESOLVED'], 'patches': ['P01', 'P05', 'P07']},
        'A054': {'resolved': ['Canonical registry and latest source version', 'E011 anchor and E013 historical manifest integrity', 'Only one enabled member', 'Contract/implementation commitment regressions'],
                 'remaining': ['FRAMEWORK_INSTALLED_BYTE_DRIFT', 'A054_SOURCE_BYTE_DRIFT', 'FRAMEWORK_LOCATOR_V106', 'RUNTIME_E013_SELF_AND_E011_BINDING_CHECKS_MISSING', 'L2A1_ONE_PROVIDER', 'NEW_INSTANCE_NOT_QUALIFIED'], 'patches': ['P01', 'P02', 'P04', 'P07']},
        'A065': {'resolved': ['Canonical registry and latest source version', 'D01/D02/D03 seals and global commitment', 'Fremlin raw/geometry source hashes', 'Existing v1.0.10 bridge identified and static-tested'],
                 'remaining': ['FRAMEWORK_INSTALLED_BYTE_DRIFT', 'A065_SOURCE_BYTE_DRIFT', 'FRESH_SUCCESSOR_COMMITMENT_AND_SMOKE_NOT_QUALIFIED', 'PHYSICAL_HELDOUT_SOURCE_UNRESOLVED'], 'patches': ['P01', 'P03', 'P06', 'P07']},
    }
    for pilot, result in pilots.items():
        result.update({'migration_gate': 'BLOCKED', 'migrated_execution_gate': 'NOT_RUN', 'scientific_gate': 'NOT_RUN', 'new_version_allowed': False,
                       'admission_contract': pilot + '_DATASET_ADMISSION.json'})
    # Verify the Phase 1 immutable results before modifying only its mutable queue.
    before_checks = []
    for item in read(STATE / 'ARTIFACT_SHA256.json')['files']:
        path = STATE / item['path']
        before_checks.append({'path': item['path'], 'expected': item['sha256'], 'actual': sha(path) if path.is_file() else None})
    if any(x['expected'] != x['actual'] for x in before_checks):
        raise RuntimeError('Phase 1 snapshot drift requires review before queue update')
    atomic(OUT / 'phase1_preservation_before_queue_update.json', {'files': before_checks, 'all_match': True})
    with locked(STATE):
        queue_path = STATE / 'queue.json'
        snapshot = OUT / 'queue.before_phase2.json'
        with snapshot.open('xb') as stream:
            stream.write(queue_path.read_bytes())
        queue = read(queue_path)
        if queue['scheduling_enabled'] or queue['pilot_validated']:
            raise RuntimeError('Queue state unexpectedly enabled')
        for job in queue['jobs']:
            if job['pilot']:
                job['phase2'] = pilots[job['id']]
                job['blockers'] = pilots[job['id']]['remaining']
            if any(job['family_path'] == x['path'] for x in registry['noncanonical_locations']):
                job['phase2_location_status'] = 'PRESERVED_NONCANONICAL_LOCATION_EXCLUDED_FROM_FUTURE_CLAIM'
        queue['phase2'] = {'at_utc': stamp, 'gate_overview': '10_docs/migration_v110/phase2_20261026/gate_overview.json',
                           'previous_queue_sha256': sha(snapshot), 'scientific_status_promoted': False}
        atomic(queue_path, queue)
    decisions = {'schema': 'SST-PHASE2-GATE-OVERVIEW-1', 'created_utc': stamp, 'checks': checks, 'pilots': pilots,
                 'scheduling_enabled': False, 'new_falsifier_versions_created': [], 'scientific_status_promoted': False,
                 'queue_sha256': sha(STATE / 'queue.json'), 'registry_hashes': {p: sha(ROOT / p) for p in ['10_docs/registry/family_hierarchy.json', '10_docs/registry/catalog_index.json']}}
    atomic(OUT / 'gate_overview.json', decisions)
    lines = ['# Phase 2 - exact remaining patch list', '', 'No listed successor or production patch was applied. Current Phase 2 only records integrity/admission decisions.', '']
    for item in patches:
        lines += ['## ' + item['id'] + ' - ' + item['kind'], '', 'Stage: ' + item['stage'], '', item['action'], '', 'Targets:']
        lines += ['- `' + p + '`' for p in item['targets']]
        lines += ['', 'Acceptance: ' + item['acceptance'], '']
        if 'pending_latest_ids' in item:
            lines += ['Pending latest: ' + ', '.join(item['pending_latest_ids']), '', 'Unresolved locations:']
            for group in item['unresolved_directory_groups']:
                lines += ['- ' + group['family'] + ': ' + ', '.join(group['directories'])]
            lines += ['']
    (OUT / 'REQUIRED_PATCHES.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'gate_checks': len(checks), 'pilots_migration_ready': 0, 'patch_items': len(patches), 'scheduling_enabled': False}))


if __name__ == '__main__':
    main()
