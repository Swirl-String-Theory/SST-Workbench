import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
import numpy as np

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import fourier_atlas_adapter as a
import gates_g4_g5 as gates

ATLAS=Path(os.environ.get('SST_ATLAS_ROOT',HERE.parent/'A003-v0.1.2'))
OLD=ATLAS.parent/'A003-v0.1.1'
LEGACY_HASHES=HERE/'legacy_v0.1.1_sha256.json'

class TestFibonacciExtension(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,_=a.load_manifest(ATLAS)
        cls.by_id={}
        for rec in cls.manifest['records']:
            cls.by_id.setdefault(rec['id'],[]).append(rec)

    def test_count_and_grouping(self):
        self.assertEqual(len(self.manifest['records']),384)
        self.assertEqual(len(self.by_id),48)
        self.assertEqual(sum(k.startswith('fibonacci_F') for k in self.by_id),6)
        self.assertEqual(sum(k.startswith('fibonacci_torus_F') for k in self.by_id),6)
        self.assertEqual(sum(k.startswith('nonfibonacci_torus_control_F') for k in self.by_id),6)
        for rows in self.by_id.values():
            self.assertEqual({(r['profile'],r['points'],r['sampling']) for r in rows},
                {(pr,n,s) for pr,ns in a.PROFILES.items() for n in ns for s in a.SAMPLINGS})

    def test_original_240_sha256_preserved(self):
        old=json.loads(LEGACY_HASHES.read_text())['records']
        new={r['file']:r for r in self.manifest['records']}
        self.assertEqual(len(old),240)
        for file,source_hash in old.items():
            self.assertEqual(new[file]['sha256'],source_hash)
            self.assertEqual(hashlib.sha256((ATLAS/file).read_bytes()).hexdigest(),source_hash)
        if (OLD/'manifest.json').is_file():
            self.assertEqual(hashlib.sha256((OLD/'manifest.json').read_bytes()).hexdigest(),
                             json.loads(LEGACY_HASHES.read_text())['source_manifest_sha256'])

    def test_fibonacci_mode_identity_and_paper_example(self):
        fib={3:(2,3,5),4:(3,5,8),5:(5,8,13),6:(8,13,21),7:(13,21,34),8:(21,34,55)}
        for n,(u,v,w) in fib.items():
            row=self.by_id[f'fibonacci_F{n}'][0]
            self.assertEqual((row['mode_x'],row['mode_y'],row['mode_z']),(u,v,w))
            self.assertEqual(u+v,w)
            self.assertEqual(row['knot'],'3_1' if n==3 else f'F({n})_UNCLASSIFIED')
        r=next(x for x in self.by_id['fibonacci_F6'] if x['points']==1200 and x['sampling']=='uniform_t')
        pts=np.loadtxt(ATLAS/r['file'])
        i=100;t=2*np.pi*i/1200
        expected=np.array([np.cos(8*t),np.cos(13*t+.5),
                   .5*np.cos(21*t+.5)+.5*np.sin(13*t+.5)])
        np.testing.assert_allclose(pts[i],expected,rtol=0,atol=2e-14)

    def test_kauffman_F3_reproduces_old_trefoil_analytic_values(self):
        for n in (1200,2400,4800,9600):
            a1=next(x for x in self.by_id['fibonacci_F3'] if x['points']==n and x['sampling']=='uniform_t')
            a2=next(x for x in self.by_id['kauffman_3_1'] if x['points']==n and x['sampling']=='uniform_t')
            self.assertEqual(a1['sha256'],a2['sha256'])

    def test_reference_invariants_do_not_invent_classifications(self):
        self.assertEqual(gates.expected_determinant(a.expected_catalog()['fibonacci_F3']),3)
        self.assertIsNone(gates.expected_determinant(a.expected_catalog()['fibonacci_F6']))
        self.assertEqual(gates.expected_determinant(a.expected_catalog()['fibonacci_torus_F6']),13)
        self.assertEqual(gates.expected_determinant(a.expected_catalog()['nonfibonacci_torus_control_F6']),15)

    def test_control_pairs_are_coprime_nonadjacent(self):
        pairs={(2,3),(3,5),(5,8),(8,13),(13,21),(21,34)}
        import math
        for n in range(3,9):
            row=self.by_id[f'nonfibonacci_torus_control_F{n}'][0]
            self.assertNotIn((row['p'],row['q']),pairs)
            self.assertEqual(math.gcd(row['p'],row['q']),1)
            self.assertEqual(row['control_limitation'],'NOT_TOPOLOGY_MATCHED')

if __name__=='__main__':unittest.main()
