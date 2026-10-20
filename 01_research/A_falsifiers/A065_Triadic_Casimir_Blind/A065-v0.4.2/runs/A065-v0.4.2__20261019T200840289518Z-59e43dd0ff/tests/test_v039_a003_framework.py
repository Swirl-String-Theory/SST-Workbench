"""v0.3.9: original Fourier adapter SHA and 1.0.10 diagnostic-gate regression."""
import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from framework_bridge.install import patch_cpu_gate_plan
from triadic.a003_v039 import (evaluate,_load_original_adapter,SourceIntegrityError,ADAPTER_SOURCE_SHA256)

ROOT=Path(__file__).resolve().parents[1]
class A003V039(unittest.TestCase):
    def test_v039_precommit_locked(self):
        x=json.loads((ROOT/'preregistration/A003_V039.json').read_text())
        self.assertEqual(x['release'],'v0.3.9')
        self.assertEqual(x['source_status'],'GEOMETRIC_SEEDS_ONLY')
        self.assertEqual(x['atlas_manifest_sha256'],'01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d')
        self.assertTrue(x['no_fitted_parameters'])
    def test_framework_gate_graph_correct(self):
        fr=ROOT.parent/'SST_Falsifier_Framework_v1.0.10/instance_template/gate_plan.json'
        if fr.is_file():g=json.loads(fr.read_text())
        else:g={'gates':[{'gate_id':'G'+str(i),'question':'g'+str(i),'requires':[],'enabled':True} for i in range(10)]}
        by={x['gate_id']:x for x in patch_cpu_gate_plan(g)['gates']}
        self.assertEqual(by['G34']['requires'],['G33'])
        self.assertEqual(by['G35']['requires'],['G34'])
        self.assertEqual(by['G36']['requires'],['G1'])
        self.assertNotIn('G2',by['G35']['requires'])
    def test_real_adapter_source_hash(self):
        p=os.environ.get('SST_A003_ADAPTER_ROOT')
        if not p:self.skipTest('External A003 adapter not supplied to test environment')
        adapter=_load_original_adapter(Path(p));self.assertEqual(adapter.ADAPTER_VERSION,'0.2.3')
        self.assertEqual(hashlib.sha256((Path(p)/'fourier_atlas_adapter.py').read_bytes()).hexdigest(),ADAPTER_SOURCE_SHA256)
    def test_missing_atlas_is_not_promoted(self):
        p=os.environ.get('SST_A003_ADAPTER_ROOT')
        if not p:self.skipTest('External A003 adapter not supplied to test environment')
        with patch.dict(os.environ,{'SST_A003_ADAPTER_ROOT':p,'SST_ATLAS_ROOT':''}):
            # Atlas is absent in uploaded adapter ZIP; if locally installed, do not assume it is absent.
            if (Path(p).parent/'A003-v0.1.2').exists():self.skipTest('Local atlas exists')
            r=evaluate(ROOT,compute_volume=False,persist=False)
        self.assertEqual(r['gates']['G33']['status'],'PASS')
        self.assertEqual(r['gates']['G34']['status'],'NOT_RUN_PREREQUISITE')
        self.assertEqual(r['gates']['G35']['status'],'NOT_RUN_PREREQUISITE')
        self.assertEqual(r['gates']['G36']['status'],'UNRESOLVED')
        self.assertEqual(r['gates']['G35']['execution_status'],'NOT_EXECUTED')
    def test_modified_adapter_fails_closed(self):
        p=os.environ.get('SST_A003_ADAPTER_ROOT')
        if not p:self.skipTest('External A003 adapter not supplied to test environment')
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)
            for n in ('fourier_atlas_adapter.py','gates_g4_g5.py','RELEASE.json'):
                shutil.copy2(Path(p)/n,dst/n)
            with (dst/'fourier_atlas_adapter.py').open('a') as f:f.write('\n# tamper\n')
            with self.assertRaisesRegex(SourceIntegrityError,'hash|SHA256'):_load_original_adapter(dst)
    def test_external_explicit_nonexistent_path_is_fatal(self):
        with patch.dict(os.environ,{'SST_A003_ADAPTER_ROOT':'/absolute/intentionally/missing/adapter'}):
            with self.assertRaises(SourceIntegrityError):evaluate(ROOT,compute_volume=False,persist=False)
    def test_framework_version_is_pinned(self):
        s=(ROOT/'framework_bridge/install.py').read_text()
        self.assertIn('SST_Falsifier_Framework_v1.0.10',s)
        self.assertIn("'1.0.10'",s)
if __name__=='__main__':unittest.main()
