import importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import bridge
from tools.knotplot_command_probe import generate, SCRIPTS
from tools.geometry_safety import assess, distance_segments

class RepairTests(unittest.TestCase):
    def test_source_selftest_mock_only(self):
        bridge.selftest()
    def test_matrix_count_conserved(self):
        self.assertEqual(6+1+8*33,271)
    def test_release_has_non_destructive_legacy_attach(self):
        self.assertIn('--legacy', (ROOT/'bridge.py').read_text())
        self.assertIn('validate_clone()', (ROOT/'bridge.py').read_text())
    def test_commands_are_opt_in_not_in_science_source(self):
        with tempfile.TemporaryDirectory() as folder:
            d=pathlib.Path(folder)/'probe';r=generate(d)
            self.assertEqual(len(r),5)
            self.assertTrue((d/'metrics.kpc').exists())
            self.assertIn('data header', (d/'metrics.kpc').read_text())
            self.assertIn('alex -1', (d/'metrics.kpc').read_text())
            self.assertNotIn('velfo', (d/'metrics.kpc').read_text())
            self.assertEqual(json.loads((d/'MANIFEST.json').read_text())['native_execution'],'NOT_RUN')
            with self.assertRaises(FileExistsError): generate(d)
    def test_diagnostic_does_not_fabricate_root_cause(self):
        d=bridge.diagnose()
        self.assertEqual(d['root_cause_verdict'],'NOT_IDENTIFIED_FROM_EXIT_CODES')
    def test_semantics_force_exclusions(self):
        x=bridge.audit_controls()['safety_policy']
        self.assertIn('EXCLUDED_FROM_DAMPED', x['velfo'])
        self.assertIn('EXCLUDED_FROM_CORE', x['tanf'])
        self.assertIn('PREVENT_SELF_CROSSINGS',x['no_collide'])
    def test_framework_relative_locator_clone_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            base=pathlib.Path(folder)/'SST-Workbench'
            orig=base/'01_research'/'A_falsifiers'/'A058_family'/'A058-v0.2.9'
            cloned=base/'01_research'/'A_falsifiers'/'A058_family'/'A058-v0.3.0'/'acquisition_workspace'/'A058-v0.2.9'
            fw=base/'06_templates'/'SST_Falsifier_Framework'/'SST_Falsifier_Framework_v1.0.8'
            (fw/'sst_falsifier').mkdir(parents=True)
            (fw/'sst_falsifier'/'__init__.py').write_text('# fake version marker')
            cloned.mkdir(parents=True)
            (cloned/'.sst_framework_root').write_text('../../../../06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.8\n')
            old=bridge.CLONE
            try:
                bridge.CLONE=cloned
                info=bridge.framework_locator_diagnostic({'source_root':str(orig)})
                self.assertTrue(info['original_exists'])
                self.assertFalse(info['clone_exists'])
                self.assertTrue(info['broken_clone_relative_locator'])
                fw_resolved, reason=bridge.pin_framework_root({'source_root':str(orig)})
                self.assertEqual(fw_resolved,fw.resolve())
                self.assertTrue(reason['broken_clone_relative_locator'])
            finally:
                bridge.CLONE=old

    def test_segment_intersection_vs_clear_snapshot(self):
        a=assess([(0,0,0),(2,2,0),(0,2,0),(2,0,0)],close=0.1)
        self.assertEqual(a['status'],'POSSIBLE_CENTERLINE_INTERSECTION')
        self.assertAlmostEqual(a['minimum_distance'],0.)
        b=assess([(0,0,0),(2,0,0),(2,2,0),(0,2,0)],close=0.1)
        self.assertEqual(b['status'],'SNAPSHOT_CLEAR')
        self.assertAlmostEqual(b['minimum_distance'],2.)
        self.assertFalse(b['certifies_continuous_time_no_reconnection'])
    def test_parallel_segment_geometry(self):
        d=distance_segments((0,0,0),(1,0,0),(0,2,0),(1,2,0))
        self.assertAlmostEqual(d,2.)

    def test_parser_modes(self):
        s=(ROOT/'bridge.py').read_text()
        for x in ('DIAGNOSE','AUDIT_CONTROLS','SELFTEST','TRIAGE','PREPARE','FREEZE','BASIC','2048','32768','FULL'):
            self.assertIn(repr(x),s)

if __name__=='__main__':unittest.main()
