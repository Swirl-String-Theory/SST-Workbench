"""Read-only verification of the controlled Phase 3 publication boundary."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parent))
from preflight import ROOT, read, sha
from phase3_prepare import snapshot, OUT, FAMILY


class Phase3PublicationTests(unittest.TestCase):
    def test_framework_and_a011_source_exact_hashes(self):
        pin = read(OUT / 'framework_source_qualification.json')
        root = ROOT / pin['selected_source']
        self.assertEqual(pin['manifest_entries_verified'], 112)
        for relative, digest in pin['all_files_sha256'].items():
            self.assertEqual(sha(root / relative), digest)
        a011 = FAMILY / 'A011-v0.4.0'
        for row in read(a011 / 'SOURCE_MANIFEST_v0.4.0.json')['files']:
            self.assertEqual(sha(a011 / row['path']), row['sha256'])

    def test_result_archive_and_sidecar_are_complete(self):
        publication = read(OUT / 'gate_overview.json')
        path = ROOT / publication['output_archive']
        self.assertEqual(sha(path), publication['output_archive_sha256'])
        self.assertEqual(path.with_suffix('.zip.sha256').read_text().split()[0], sha(path))
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            manifest_path = next(n for n in z.namelist() if n.endswith('/OUTPUT_MANIFEST.json'))
            prefix = manifest_path[:-len('OUTPUT_MANIFEST.json')]
            for entry in json.loads(z.read(manifest_path))['files']:
                self.assertEqual(hashlib.sha256(z.read(prefix + entry['path'])).hexdigest(), entry['sha256'])
            self.assertTrue(any(n.endswith('_FALSIFIER_REPORT.pdf') for n in z.namelist()))

    def test_queue_transition_only_a011_and_no_scientific_promotion(self):
        current = read(ROOT / '10_docs/migration_v110/pilot_20261026/queue.json')
        before = read(OUT / 'before_publication/10_docs/migration_v110/pilot_20261026/queue.json')
        for old, new in zip(before['jobs'], current['jobs']):
            if old['id'] != 'A011':
                self.assertEqual(old, new)
            else:
                self.assertEqual(new['migration_gate'], 'PASS_GEOMETRY_ADAPTER')
                self.assertEqual(new['execution_gate'], 'PASS_BOUNDED_GEOMETRY_SMOKE')
                self.assertEqual(new['scientific_gate'], 'UNRESOLVED_MISSING_PHYSICAL_INPUTS')
                self.assertFalse(new['phase3']['scientific_status_promoted'])
        self.assertFalse(current['scheduling_enabled'])
        self.assertFalse(current['pilot_validated'])

    def test_predecessor_and_excluded_pilots_preserved(self):
        before = read(OUT / 'preservation_before.json')
        self.assertEqual(snapshot(FAMILY / 'A011-v0.3.1'), before['A011-v0.3.1'])
        for cid in ['A054', 'A065']:
            record = before[cid]
            for relative, digest in record['files'].items():
                self.assertEqual(sha(ROOT / record['path'] / relative), digest)
            self.assertEqual(sha((ROOT / record['path']).parent / 'FAMILY.yaml'), record['family_sha256'])

    def test_only_a011_registry_node_changes(self):
        h = read(ROOT / '10_docs/registry/family_hierarchy.json')
        c = read(ROOT / '10_docs/registry/catalog_index.json')
        oldh = read(OUT / 'before_publication/10_docs/registry/family_hierarchy.json')
        oldc = read(OUT / 'before_publication/10_docs/registry/catalog_index.json')
        self.assertEqual(h['hierarchy']['01_research']['A_falsifiers']['A011']['latest'], 'v0.4.0')
        self.assertEqual(c['by_domain']['01_research']['A011']['latest'], 'v0.4.0')
        for domain, letters in oldh['hierarchy'].items():
            for letter, nodes in letters.items():
                for cid, node in nodes.items():
                    if (domain, letter, cid) != ('01_research', 'A_falsifiers', 'A011'):
                        self.assertEqual(h['hierarchy'][domain][letter][cid], node)
        for domain, nodes in oldc['by_domain'].items():
            for cid, node in nodes.items():
                if (domain, cid) != ('01_research', 'A011'):
                    self.assertEqual(c['by_domain'][domain][cid], node)


if __name__ == '__main__':
    unittest.main()
