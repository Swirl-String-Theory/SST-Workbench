from __future__ import annotations
import json, math, pathlib, sys, types, unittest
from unittest.mock import patch
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from g5_crossing_tolerance_v027 import (scale_invariant_intersection,cutoff_report,
                                         scoped_pyknotid_crossing_fix)
from g5_extended import rotation_for_projection


def test_helper(px,py,dpx,dpy,qx,qy,dqx,dqy):
    # Matches the exact source check in the pinned 0.5.3 Python helper.
    def cross_product(a,b,c,d): return a*d-b*c
    if abs(cross_product(dpx,dpy,dqx,dqy)) < 0.00001:
        return (0, 0., 0.)
    cross=cross_product(dpx,dpy,dqx,dqy)
    t=cross_product(qx-px,qy-py,dqx,dqy)/cross
    if 0<t<1:
        u=cross_product(qx-px,qy-py,dpx,dpy)/cross
        if 0<u<1:return (1,t,u)
    return (0,-1.,-1.)

class TestScaledGuard(unittest.TestCase):
    def test_simple_crossing_all_scales(self):
        for scale in (1e-5,0.01,1,100):
            with self.subTest(scale=scale):
                s=scale
                ret=scale_invariant_intersection(0.,0.,s,s,0.,s,s,-s)
                self.assertEqual(ret[0],1)
                self.assertAlmostEqual(ret[1],.5)
                self.assertAlmostEqual(ret[2],.5)
    def test_parallel_and_degenerate_cases(self):
        self.assertEqual(scale_invariant_intersection(0,0,0,0,0,0,1,1)[0],0)
        self.assertEqual(scale_invariant_intersection(0,0,1,0,0,1,1,0)[0],0)
        with self.assertRaises(ValueError):scale_invariant_intersection(0,0,float('nan'),1,0,0,1,0)
    def test_frozen_F3_real_geometry_unchanged(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').exists():self.skipTest('full atlas absent')
        cases=[]
        for n,i,j in ((1200,65,1041),(2400,131,2083)):
            src=atlas/f'xyz/fibonacci_torus_F3_uniform_t_N{n}.xyz'
            pts=np.loadtxt(src,dtype=float)@rotation_for_projection(1).T
            p=pts[i];q=pts[j]
            u=pts[(i+1)%n,:2]-p[:2]
            v=pts[(j+1)%n,:2]-q[:2]
            metrics=cutoff_report(u,v)
            cases.append(metrics)
            self.assertEqual(scale_invariant_intersection(*p[:2],*u,*q[:2],*v)[0],1)
            self.assertFalse(metrics['corrected_guard_rejects'])
            self.assertGreater(metrics['normalized_abs_sin'],0.2)
        self.assertFalse(cases[0]['stock_guard_rejects'])
        self.assertTrue(cases[1]['stock_guard_rejects'])

class TestScopedPatch(unittest.TestCase):
    def fake_pkg(self):
        pkg=types.ModuleType('pyknotid');pkg.__path__=[]
        sp=types.ModuleType('pyknotid.spacecurves');sp.__path__=[]
        helpers=types.ModuleType('pyknotid.spacecurves.helpers')
        helpers.do_vectors_intersect=test_helper
        sc=types.ModuleType('pyknotid.spacecurves.spacecurve')
        class SpaceCurve:
            def raw_crossings(self,*args,try_cython=True,**kwargs):
                return {'cython_requested':try_cython,
                        'intersection':helpers.do_vectors_intersect(0,0,0.001,0.001,0,.001,.001,-.001)}
        sc.SpaceCurve=SpaceCurve
        sp.helpers=helpers;sp.spacecurve=sc
        return {'pyknotid':pkg,'pyknotid.spacecurves':sp,'pyknotid.spacecurves.helpers':helpers,
                'pyknotid.spacecurves.spacecurve':sc},SpaceCurve,helpers

    def test_patch_is_restored_even_after_exception(self):
        mods,sc,helpers=self.fake_pkg()
        orig_h=helpers.do_vectors_intersect;orig_r=sc.raw_crossings
        with patch.dict(sys.modules,mods),patch('importlib.metadata.version',return_value='0.5.3'):
            self.assertEqual(sc().raw_crossings()['intersection'][0],0)
            with self.assertRaisesRegex(RuntimeError,'inject-fail'):
                with scoped_pyknotid_crossing_fix() as meta:
                    self.assertEqual(meta['pyknotid_version'],'0.5.3')
                    got=sc().raw_crossings()
                    self.assertFalse(got['cython_requested'])
                    self.assertEqual(got['intersection'][0],1)
                    raise RuntimeError('inject-fail')
            self.assertIs(helpers.do_vectors_intersect,orig_h)
            self.assertIs(sc.raw_crossings,orig_r)
            self.assertEqual(sc().raw_crossings()['intersection'][0],0)

    def test_unknown_provider_version_fails_closed(self):
        mods,sc,helpers=self.fake_pkg()
        with patch.dict(sys.modules,mods),patch('importlib.metadata.version',return_value='0.5.4'):
            with self.assertRaisesRegex(RuntimeError,'Unsupported'):
                with scoped_pyknotid_crossing_fix():pass
            self.assertIs(helpers.do_vectors_intersect,test_helper)

if __name__=='__main__':unittest.main()
