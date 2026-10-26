"""Small regression suite (does not require the full canonical Workbench)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name('build_multiseed_view.py')


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pklsa_filter_test_')
        self.addCleanup(self.tmp.cleanup)
        self.src = Path(self.tmp.name) / 'source'
        self.src.mkdir()
        topologies = ['0_1', '3_1', '5_2', 'L2a1']
        def save(name, obj):
            (self.src / name).write_text(json.dumps(obj))
        (self.src / 'preflight').mkdir()
        (self.src / 'preflight' / 'TOPOLOGY_SET.json').write_text(json.dumps({'count': 4, 'topologies': topologies, 'unmapped_audit_only_count': 2}))
        save('CAMPAIGN_INDEX.json', {'passed':['0_1', '3_1', 'L2a1'], 'failed':['5_2'], 'topology_count':4,
                                     'passed_count':3, 'failed_count':1})
        save('FAILED_TOPOLOGIES.json', [{'topology_id':'5_2','summary':{}}])
        save('IDENTITY_DATABASE_LEDGER.json', [{'topology_id':x} for x in topologies])
        (self.src / 'preflight' / 'TOPOLOGY_IDENTITY_ADMISSION.json').write_text(json.dumps({'admitted_count':4,
             'mapped':[{'topology_id':x} for x in topologies],
             'unmapped_audit_only':[{'topology_id':'1_1'},{'topology_id':'10_166'}],
             'unmapped_audit_only_count':2}))
        for topology, count, groups in [('0_1', 1,1), ('3_1',3,2), ('5_2',2,1), ('L2a1',1,1)]:
            q = self.src / 'atlas' / topology / 'qualification'
            q.mkdir(parents=True)
            (q/'summary.json').write_text(json.dumps({'topology_id':topology,
                     'discovered_carriers':count,'independent_group_count':groups,'source_matrix':[]}))

    def call(self, *extra):
        return subprocess.run([sys.executable,str(TOOL),'--source',str(self.src),*extra],
                              capture_output=True,text=True)

    def test_dry_run_no_mutation(self):
        r=self.call('--dry-run')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('Active (>= 2 seeds): 2',r.stdout)
        self.assertEqual([x.name for x in self.src.parent.iterdir()],['source'])

    def test_filter_preserves_history(self):
        r=self.call()
        self.assertEqual(r.returncode,0,r.stderr)
        out=self.src.parent/'E010_PKLSA_Multiseed_View_v0.3.4-outputs'
        active=json.loads((out/'ACTIVE_TOPOLOGY_SET.json').read_text())
        self.assertEqual(active['topologies'],['3_1','5_2'])
        history=json.loads((out/'ACTIVE_CAMPAIGN_INDEX.json').read_text())
        self.assertEqual((history['passed'],history['failed']),(['3_1'],['5_2']))
        report=json.loads((out/'SELECTION_RELEASE.json').read_text())
        self.assertEqual(report['excluded_single_seed_count'],2)
        self.assertEqual(report['selected_historical_pass_count'],1)
        self.assertEqual(report['selected_historical_fail_count'],1)
        self.assertEqual(report['filter_tool_patch'], 'v0.3.4-hotfix1')
        self.assertIn('preflight/TOPOLOGY_SET.json', report['source_manifest_sha256'])
        self.assertIn('preflight/TOPOLOGY_IDENTITY_ADMISSION.json', report['source_manifest_sha256'])
        self.assertTrue((self.src/'atlas'/'0_1').exists())
        self.assertEqual(self.call().returncode,1)

    def test_independence_filter_is_optional(self):
        r=self.call('--min-independent-groups','2')
        self.assertEqual(r.returncode,0,r.stderr)
        out=self.src.parent/'E010_PKLSA_Multiseed_View_v0.3.4-outputs'
        active=json.loads((out/'ACTIVE_TOPOLOGY_SET.json').read_text())
        self.assertEqual(active['topologies'],['3_1'])

    def test_missing_preflight_registry_fails_closed(self):
        (self.src/'preflight'/'TOPOLOGY_SET.json').unlink()
        r=self.call('--dry-run')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('preflight', r.stderr)

    def test_no_root_level_topology_fallback(self):
        # Fail closed, even if a stale/misplaced root-level topology set exists.
        (self.src/'TOPOLOGY_SET.json').write_text((self.src/'preflight'/'TOPOLOGY_SET.json').read_text())
        (self.src/'preflight'/'TOPOLOGY_SET.json').unlink()
        r=self.call('--dry-run')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('preflight', r.stderr)

    def test_missing_summary_fails_closed(self):
        (self.src/'atlas'/'3_1'/'qualification'/'summary.json').unlink()
        r=self.call()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('Missing qualification summary',r.stderr)
        self.assertFalse((self.src.parent/'E010_PKLSA_Multiseed_View_v0.3.4-outputs').exists())

if __name__ == '__main__':
    unittest.main()
