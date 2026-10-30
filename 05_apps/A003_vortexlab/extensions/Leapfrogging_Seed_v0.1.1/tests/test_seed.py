from __future__ import annotations
import unittest, tempfile, math, json, hashlib, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_leapfrogging_seed import ring_points,write_seed
from analyze_leapfrogging_trace import analyze

class SeedTests(unittest.TestCase):
    def test_ring_orientation_and_dimensions(self):
        p=ring_points(.07,-.015,144)
        self.assertEqual(len(p),144)
        self.assertTrue(all(abs(math.hypot(x,y)-.07)<1e-12 and abs(z+.015)<1e-12 for x,y,z in p))
        signedarea=sum(p[i][0]*p[(i+1)%144][1]-p[(i+1)%144][0]*p[i][1] for i in range(144))/2
        self.assertGreater(signedarea,0)
    def test_native_xyz_has_two_closed_components(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'output';m=write_seed(d,n=144)
            raw=(d/'leapfrog_two_rings_N144.xyz').read_text().strip().split('\n\n')
            self.assertEqual(len(raw),2)
            for c in raw:
                vals=[[float(q) for q in line.split()] for line in c.splitlines()[1:]]
                self.assertEqual(len(vals),144)
                self.assertNotEqual(vals[0],vals[-1])
            self.assertEqual(m['circulation_signs'],[1,1])
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'out';write_seed(d,n=72)
            f=d/'leapfrog_two_rings_N72.xyz'
            before=f.read_bytes()
            with self.assertRaises(FileExistsError):write_seed(d,n=72)
            self.assertEqual(f.read_bytes(),before)
    def test_hash_manifest(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'out';write_seed(d,n=72)
            for ln in (d/'SHA256SUMS.txt').read_text().splitlines():
                sha,name=ln.split('  ',1)
                self.assertEqual(hashlib.sha256((d/name).read_bytes()).hexdigest(),sha)
    def test_reject_colliding_or_impossible_parameters(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):write_seed(Path(t)/'bad',gap=.001,core=.0015)
            with self.assertRaises(ValueError):write_seed(Path(t)/'bad',n=3)
    def test_trace_detector(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'trace.csv'
            p.write_text('t,RA,RB,zA,zB\n0,.07,.07,-.02,.02\n1,.06,.08,.02,-.02\n2,.08,.06,-.02,.02\n')
            out=analyze(p)
            self.assertEqual(out['axial_order_swaps'],2)

if __name__=='__main__':unittest.main()
