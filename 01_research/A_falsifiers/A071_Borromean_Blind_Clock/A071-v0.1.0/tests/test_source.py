import sys,unittest,zipfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from runner import ROOT,SOURCE_DEFAULT,CONTRACT,readjson,filehash

class TestSource(unittest.TestCase):
    def test_contract_refers_to_original(self):
        self.assertTrue(readjson(CONTRACT)['no_physical_SST_constants'])
    def test_zip_integrity_if_bundled(self):
        if not SOURCE_DEFAULT.exists():self.skipTest('source external')
        self.assertEqual(filehash(SOURCE_DEFAULT),readjson(CONTRACT)['source_archive_sha256'])
    def test_has_own_twist_knots_if_bundled(self):
        if not SOURCE_DEFAULT.exists():self.skipTest('source external')
        with zipfile.ZipFile(SOURCE_DEFAULT) as z:
            for k in ('5_2','6_1'):
                n='A006-v0.5.0/Output/v050/geometry/KNOT_'+k+'_N0512_ORIG.xyz'
                self.assertIn(n,z.namelist())

class TestBlindPrep(unittest.TestCase):
    def test_prepared_no_identity_leak_and_correct_holdouts(self):
        if not SOURCE_DEFAULT.exists():self.skipTest('source external')
        import tempfile
        from runner import prepare
        with tempfile.TemporaryDirectory() as dest:
            prepare(SOURCE_DEFAULT,dest)
            index=json.loads((Path(dest)/'BLIND_INDEX.json').read_text())['seeds']
            self.assertEqual(len(index),64)
            self.assertEqual(sum(1 for x in index if x['split']=='HOLDOUT'),16)
            self.assertEqual(sum(1 for x in index if x.get('scout_primary')),2)
            self.assertNotIn('5_2',str(index))
            self.assertNotIn('6_1',str(index))
            self.assertNotIn('BALANCED',str(index))
            self.assertTrue((Path(dest)/'SEALED_SOURCE_MAP.json').exists())
    def test_bad_source_rejected_before_acceptance(self):
        import tempfile
        from runner import prepare
        with tempfile.TemporaryDirectory() as dest:
            p=Path(dest)/'tampered.zip';p.write_bytes(b'not the frozen A006 source')
            with self.assertRaises(RuntimeError):prepare(p,Path(dest)/'out')
