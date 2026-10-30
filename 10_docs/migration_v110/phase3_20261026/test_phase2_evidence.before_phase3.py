"""Regression assertions for Phase 2 evidence and non-promotion boundaries."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from preflight import ROOT, read, sha

OUT = ROOT / '10_docs/migration_v110/phase2_20261026'


class Phase2EvidenceTests(unittest.TestCase):
    def test_sealed_rc2_archive_and_all_entries(self):
        doc = read(OUT / 'framework_integrity.json')
        self.assertEqual(doc['archive_expected_sha256'], doc['archive_actual_sha256'])
        self.assertTrue(doc['archive_internal_manifest_valid'])
        self.assertTrue(doc['difference_limited_to_math_delimiters_and_eof_newline'])
        self.assertEqual(doc['installed_byte_integrity'], 'FAIL')
        self.assertFalse(doc['historical_manifest_changed'])

    def test_every_carrier_hash_checked_without_science_promotion(self):
        rows = [json.loads(line) for line in (OUT / 'geometry_hashes.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 4497)
        self.assertTrue(all(r['status'] == r['raw_status'] == r['geometry_status'] == 'PASS' for r in rows))
        self.assertTrue(all(r['finite'] for r in rows))
        self.assertEqual(sum(r['active_view'] for r in rows), 2312)
        self.assertEqual(read(OUT / 'geometry_integrity.json')['scientific_qualification'], 'NOT_EVALUATED_NO_STATUS_PROMOTION')

    def test_registry_scope_and_unique_canonical_paths(self):
        h = read(ROOT / '10_docs/registry/family_hierarchy.json')
        c = read(ROOT / '10_docs/registry/catalog_index.json')
        oldh = read(OUT / 'registry_before/10_docs/registry/family_hierarchy.json')
        oldc = read(OUT / 'registry_before/10_docs/registry/catalog_index.json')
        for domain, letters in oldh['hierarchy'].items():
            for letter, nodes in letters.items():
                if (domain, letter) != ('01_research', 'A_falsifiers'):
                    self.assertEqual(h['hierarchy'][domain][letter], nodes)
        for domain, entries in oldc['by_domain'].items():
            for cid, entry in entries.items():
                if entry.get('letter') != 'A_falsifiers':
                    self.assertEqual(c['by_domain'][domain][cid], entry)
        families = h['hierarchy']['01_research']['A_falsifiers']
        self.assertEqual(len(families), 73)
        for cid, node in families.items():
            self.assertEqual(c['by_domain']['01_research'][cid]['path'], node['path'])
            self.assertTrue((ROOT / node['path'] / 'FAMILY.yaml').is_file())
            self.assertEqual(c['by_domain']['01_research'][cid]['versions'], node['declared_versions'])
            self.assertTrue(all('directory' in row for row in node['declared_versions']))

    def test_seals_and_provider_bindings(self):
        seals = read(OUT / 'a065_seals.json')
        self.assertTrue(all(row['status'] == 'PASS' for row in seals['datasets']))
        self.assertFalse(seals['private_targets_opened'])
        self.assertFalse(seals['reveal_executed'])
        providers = read(OUT / 'a054_provider_dependencies.json')
        self.assertEqual(len(providers['anchor_results']), 47)
        self.assertTrue(all(x['payload_hashes_match_e010'] for x in providers['anchor_results']))
        self.assertTrue(all(x['binding_status'] == 'PASS' for x in providers['historical_e013_manifests']))
        self.assertFalse(providers['duplicate_enabled_versions'])

    def test_contracts_do_not_authorize_creation_or_physics(self):
        for cid in ['A011', 'A054', 'A065']:
            doc = read(OUT / (cid + '_DATASET_ADMISSION.json'))
            self.assertTrue(doc['no_scientific_promotion'])
            self.assertFalse(doc['new_version_creation_authorized_by_contract_alone'])
        queue = read(ROOT / '10_docs/migration_v110/pilot_20261026/queue.json')
        self.assertFalse(queue['scheduling_enabled'])
        self.assertFalse(queue['pilot_validated'])
        for job in queue['jobs']:
            if job['pilot']:
                self.assertEqual(job['execution_gate'], 'NOT_RUN')
                self.assertEqual(job['scientific_gate'], 'NOT_RUN')
                self.assertFalse((ROOT / job['family_path'] / job['proposed_version']).exists())


if __name__ == '__main__':
    unittest.main()
