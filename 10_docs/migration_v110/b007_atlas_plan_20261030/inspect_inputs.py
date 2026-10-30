"""Read-only source inspection for a B007 integration proposal; no evaluator."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(r'C:\workspace\projects\SST-Workbench')
OUT = Path(__file__).resolve().parent
B007 = ROOT/'01_research/B_closures/B007_/B007_Gate2_Ruban_Familywise_Coupled_Falsifier_v0.2.3'
E010 = ROOT/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.4.0'
PAYLOAD = E010/'SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs'
PINS = {}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def pin(path, expected=None):
    path = Path(path)
    actual = sha(path)
    assert expected is None or actual == expected, str(path)
    PINS[path.relative_to(ROOT).as_posix()] = {'sha256': actual, 'bytes': path.stat().st_size}
    return actual


def read(path):
    pin(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def create(name, value):
    with (OUT/name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def main():
    publication = read(E010/'PUBLICATION.json')
    for relative, expected in publication['source_files'].items():
        pin(E010/relative, expected)
    for item in publication['artifacts']:
        pin(E010.parent/item['name'], item['sha256'])
    pin(PAYLOAD/'COMBINED_INDEX.json', publication['index_sha256'])
    manifest = read(PAYLOAD/'FILE_MANIFEST.json')
    for relative in ['sst_pklsa/combined_atlas.py', 'sst_pklsa/__init__.py',
                     'pklsa_builder/models.py', 'pklsa_builder/io_geometry.py',
                     'pklsa_builder/fseries.py', 'pklsa_builder/gilbert.py',
                     'pklsa_builder/hashing.py', 'pklsa_builder/__init__.py',
                     'DUPLICATES.json', 'VALIDATION.json']:
        pin(PAYLOAD/relative, manifest['files'][relative])
    sys.path.insert(0, str(PAYLOAD))
    from sst_pklsa.combined_atlas import CombinedSeedAtlas
    atlas = CombinedSeedAtlas(PAYLOAD)
    assert len(atlas.list_ids(include_research=True)) == 11757
    assert len(atlas.list_ids()) == 4497
    ids = ['RUBAN_v036_T_2_3_B2000_N1024_nominal',
           'RUBAN_v036_T_2_3_B2000_N1024_perturbed',
           'CAR_31cb4dd7832f3462', 'CAR_212795fc5320f974',
           'CAR_a7c802004bcfe26f']
    selected = []
    for identity in ids:
        record = atlas.describe(identity)
        parts = atlas.load(identity, allow_research=True)
        if record['collection'] == 'historical_v031':
            pin(PAYLOAD/record['raw_path'], record['raw_sha256'])
        else:
            for comp in record['components']:
                pin(PAYLOAD/comp['path'], comp['sha256'])
        pin(PAYLOAD/record['source_document'], manifest['files'][record['source_document']])
        selected.append({'id': identity, 'record_snapshot': record,
                         'loaded_component_points': [len(p) for p in parts],
                         'load_result': 'PASS_RAW_AND_ORDERED_GEOMETRY_HASH',
                         'proposed_role': 'EXACT_DUPLICATE_CONTROL' if identity == ids[-1] else
                                          'PAIRED_PERTURBATION_CONTROL' if identity == ids[1] else
                                          'PRIMARY_EMBEDDING_REFERENCE',
                         'consumer_admission': 'DIAGNOSTIC_CANDIDATE_ONLY',
                         'scientific_qualification_changed': False})
    assert selected[2]['record_snapshot']['geometry_sha256'] == selected[4]['record_snapshot']['geometry_sha256']
    assert selected[1]['record_snapshot']['parent_id'] == ids[0]
    duplicates = read(PAYLOAD/'DUPLICATES.json')
    assert len(duplicates['exact_geometry_groups']) == 303
    trefoils = [atlas.describe(i) for i in atlas.list_ids(include_research=True)
                if atlas._records[i].get('topology_id') == '3_1']
    historical = [r for r in trefoils if r['collection'] == 'historical_v031']
    for folder in ['src', 'configs', 'tests', 'docs']:
        for path in sorted((B007/folder).rglob('*')):
            if path.is_file() and path.suffix in ('.py', '.json', '.md'):
                pin(path)
    for name in ['run_all.cmd', 'FAMILY.yaml', 'README.md', 'README_HOTFIX.md', 'HOTFIX_MANIFEST.json']:
        pin(B007/name)
    hierarchy = read(ROOT/'10_docs/registry/family_hierarchy.json')
    catalog = read(ROOT/'10_docs/registry/catalog_index.json')
    assert 'B007' not in json.dumps(catalog)
    assert hierarchy['next_catalog_ids']['B_closures'] == 'B007'
    example = atlas.describe('CAR_9d70839a95573877')
    pin(PAYLOAD/example['raw_path'], example['raw_sha256'])
    assert '/logfiles/' in example['carrier']['metadata']['relative_path']
    inspection = {
        'schema': 'B007-ATLAS-PLANNING-INSPECTION-1',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'timezone': 'Europe/Amsterdam',
        'status': 'PASS_INPUT_INTEGRITY_WITH_ADMISSION_AND_REGISTRY_LIMITS',
        'baseline': B007.relative_to(ROOT).as_posix(),
        'existing_version': 'v0.2.3', 'proposed_successor': 'v0.2.4',
        'new_version_created': False, 'implementation_performed': False,
        'scientific_evaluators_executed': False, 'scientific_status_promoted': False,
        'atlas_record_count': 11757, 'exact_duplicate_groups': 303,
        'selected_records_loaded': len(selected), 'primary_embedding_references': 3,
        'trefoil_label_records': len(trefoils),
        'historical_trefoil_records': len(historical),
        'historical_trefoil_aggregate_status_counts': dict(collections.Counter(r['historical_topology_status'] for r in historical)),
        'historical_status_interpretation': 'Preserved aggregate FAIL is not a newly proven wrong topology; do not promote or silently discard it.',
        'registry': {'catalog_contains_B007': False, 'hierarchy_next_id': 'B007',
                     'local_family_identity': 'UNASSIGNED_REQUIRES_CURRENT_INDEX'},
        'semantic_exclusion_example': {'id': example['id'], 'raw_path': example['raw_path'],
             'original_relative_path': example['carrier']['metadata']['relative_path'],
             'reason': 'KnotPlot logfile tabulation is indexed as XYZ; byte integrity alone does not establish geometry semantics. Exclude from B007 allowlist; retain historical record.'},
        'source_admission': 'user-authorized local source; no independent publisher authentication inferred',
        'gate_axes': {'source_integrity': 'PASS', 'selected_geometry_import': 'PASS',
                      'b007_registry': 'UNRESOLVED', 'adapter': 'PLANNED_NOT_IMPLEMENTED',
                      'spatial_convergence': 'NOT_RUN', 'temporal_convergence': 'NOT_RUN',
                      'embedding_sensitivity': 'NOT_RUN', 'scientific': 'NOT_RUN_NO_PROMOTION'},
        'python': sys.version, 'workspace': str(ROOT),
        'notes': ['Source snapshots and exact IDs are a sealed proposal, not an operational production admission.',
                  'Existing v0.2.3 validation reports were read; its 57-test historical claim was not rerun here.']}
    create('INSPECTION.json', inspection)
    create('SOURCE_SELECTION.json', {'schema': 'B007-ATLAS-SOURCE-SELECTION-PROPOSAL-1',
          'status': 'PINNED_DIAGNOSTIC_PROPOSAL_NOT_EXECUTION_RELEASE',
          'atlas_root': PAYLOAD.relative_to(ROOT).as_posix(),
          'atlas_index_sha256': publication['index_sha256'], 'atlas_zip_sha256': publication['zip_sha256'],
          'source_admission': 'user-authorized', 'production_admission': False,
          'records': selected})
    create('INPUT_HASHES.json', PINS)
    assert all(sha(ROOT/p) == v['sha256'] for p, v in PINS.items())
    print(json.dumps({'status': inspection['status'], 'selected_records_loaded': len(selected),
                     'pinned_inputs': len(PINS), 'registry': inspection['registry']}))


if __name__ == '__main__':
    main()
