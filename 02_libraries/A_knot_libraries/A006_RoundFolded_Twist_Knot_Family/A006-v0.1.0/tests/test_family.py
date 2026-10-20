import json
from pathlib import Path
import sys
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import build
import braid_backend as b

class FamilyTests(unittest.TestCase):
    def test_family_names_and_invariant_targets(self):
        targets={3:'5_2',4:'6_1',5:'7_2',6:'8_1'}
        for m,n in targets.items():
            self.assertEqual(build.NAMES[m],n)
            self.assertEqual(2*m+1,dict(zip(targets,[7,9,11,13]))[m])
    def test_source_snapshots_are_readable(self):
        for m in range(3,7):
            p,h,n=build.load_source(m)
            self.assertEqual(p.shape,(300,3))
            self.assertEqual(len(h),64)
    def test_source_closed_resampling(self):
        p,_,_=build.load_source(3)
        q=build.resample_closed(p,256)
        self.assertEqual(q.shape,(256,3))
        self.assertGreater(np.min(np.linalg.norm(q-np.roll(q,-1,axis=0),axis=1)),0)
    def test_circle_is_closed_nontrivial_polygon(self):
        p=build.circle(128,10)
        self.assertLess(np.max(np.abs(np.linalg.norm(p[:,:2],axis=1)-10)),1e-12)
    def test_kpt_roundtrip_case(self):
        case='Tm3_5_2_N0256'
        d=ROOT/'output'/'individual'/case
        p=b.decode_kpt((d/(case+'.kpt')).read_bytes())
        self.assertEqual(len(p),1)
        self.assertEqual(len(p[0]),512)
    def test_pairwise_borromean_linking(self):
        case='Borromean_5_2_5_2_6_1_N0256'
        d=json.loads((ROOT/'output'/'borromean'/case/'REPORT.json').read_text())
        self.assertEqual(d['component_count'],3)
        self.assertLess(max(abs(x) for x in d['pairwise_gauss_linking_numerical']),0.01)
        self.assertGreater(min(d['intercomponent_clearances'].values()),0.12)
    def test_self_clearance_for_all_cases(self):
        for f in (ROOT/'output').glob('*/*/REPORT.json'):
            data=json.loads(f.read_text())
            for c in data['components']:
                self.assertGreater(c['geometry']['min_nonlocal_self_segment_distance'],0.12)
                self.assertLess(c['geometry']['edge_ratio'],1.7)
                self.assertLess(c['geometry']['max_turn_degrees'],110)
    def test_gate_does_not_promote_topology(self):
        for f in (ROOT/'output').glob('*/*/REPORT.json'):
            g=json.loads(f.read_text())['gates']
            self.assertEqual(g['knot_polynomial_and_isotopy'],'UNRESOLVED')
            self.assertEqual(g['finite_core_Euler'],'NOT_TESTED')
    def test_zero_if_missing_higher_m_source(self):
        with self.assertRaises(FileNotFoundError):build.load_source(11)

if __name__=='__main__':unittest.main()
