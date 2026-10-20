"""v0.3.1 provider, preregistration, native and DAG contract regressions."""
import copy,hashlib,json,pathlib,shutil,tempfile,unittest
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1]
from triadic.provider_manifest import resolve,write_new,verify
from triadic.dynamics import run
from triadic.security import verify_all
from framework_bridge.install import patch_cpu_gate_plan

class QualificationTests(unittest.TestCase):
    def test_fixed_parameters_and_ladder(self):
        r=run(R)
        self.assertEqual(r['resolution_ladder'],[75,150,300])
        self.assertEqual((r['regularization'],r['gamma'],r['t_final']),(.12,1.0,.04))
        self.assertEqual(r['spatial_pairs']['75_vs_150']['gate'],'FAIL')
        self.assertEqual(r['spatial_pairs']['150_vs_300']['gate'],'PASS')
        self.assertEqual(r['spatial_pairs']['75_vs_300']['gate'],'FAIL')
    def test_provider_frozen_same_in_both_modes_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td);raw=p/'fremlin_test.short'
            raw.write_text(''.join(f'{i/13:.6f} {i*i/137:.6f} {i*i*i/1739:.6f}\n' for i in range(19)))
            shutil.copytree(R/'data',p/'data')
            c=p/'data/D01_EULER/pklsa/fremlin_provider_contract.json'
            rec=json.loads(c.read_text());rec['expected_raw_sha256']=hashlib.sha256(raw.read_bytes()).hexdigest()
            c.write_text(json.dumps(rec))
            with patch.dict('os.environ',{'SST_A065_FREMLIN_PATH':str(raw)}):
                first=write_new(p)
            self.assertEqual(first['status'],'PASS_RAW_HASH_AND_XYZ_PARSER_ONLY')
            self.assertEqual(verify(p)['manifest_sha256'],first['manifest_sha256'])
            framework=p/'framework';(framework/'outputs').mkdir(parents=True)
            shutil.copytree(p/'data',framework/'data')
            shutil.copy2(p/'outputs/PROVIDER_MANIFEST.json',framework/'outputs/PROVIDER_MANIFEST.json')
            self.assertEqual(verify(framework)['manifest_sha256'],first['manifest_sha256'])
            raw.write_bytes(raw.read_bytes()+b'altered')
            with self.assertRaisesRegex(RuntimeError,'PROVIDER_MANIFEST_SOURCE_CHANGED'):
                verify(p)
            with self.assertRaisesRegex(RuntimeError,'PROVIDER_MANIFEST_SOURCE_CHANGED'):
                verify(framework)
    def test_original_three_seals_unchanged(self):
        self.assertEqual(len(verify_all(R)),3)
        import zipfile
        legacy=pathlib.Path('/mnt/data/A065-v0.3.0-r1_FULL_SELFCONTAINED.zip')
        if legacy.is_file():
            with zipfile.ZipFile(legacy) as z:
                for name in ('D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE'):
                    p=f'A065-v0.3.0-r1/seals/{name}.seal.json'
                    self.assertEqual(z.read(p),(R/'seals'/f'{name}.seal.json').read_bytes())
    def test_cpu_gate_dag_nonblocking(self):
        prior={'gates':[{'gate_id':k,'requires':v,'question':k} for k,v in {
            'G0':[], 'G1':['G0'],'G2':['G1'],'G3':['G2'],'G4':['G3'],
            'G5':['G4'],'G6':['G5'],'G7':['G6'],'G8':['G7'],'G9':['G8']}.items()]}
        orig=copy.deepcopy(prior);new=patch_cpu_gate_plan(prior)
        d={x['gate_id']:x for x in new['gates']}
        self.assertEqual(d['G5']['requires'],['G1'])
        self.assertEqual(d['G8']['requires'],['G3','G5'])
        self.assertNotIn('G7',d['G8']['requires'])
        self.assertEqual(orig['gates'][5]['requires'],['G4'])

if __name__=='__main__':unittest.main()
