from __future__ import annotations
import hashlib,json,math,sys,tempfile,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from build_ruban_family import (components,sample_ruban,pushforward_affine_shear,
                                min_intercomponent_sampled_distance,count_summary,b_grid,build,sha)
CFG=json.loads((ROOT/'configs/ruban_family.json').read_text())

def gauss_pair(a,b):
    aa=np.roll(a,-1,axis=0);bb=np.roll(b,-1,axis=0)
    da=aa-a;db=bb-b
    r=(a+aa)[:,None,:]/2-(b+bb)[None,:,:]/2
    return float(np.sum(np.einsum('ijk,ijk->ij',r,np.cross(da[:,None,:],db[None,:,:])) /
                     np.linalg.norm(r,axis=-1)**3)/(4*np.pi))

class TestGeometry(unittest.TestCase):
    def test_family_counts(self):
        s=count_summary(CFG,'fine')
        self.assertEqual((s['knot_family_count'],s['link_family_count'],s['family_count']), (24,6,30))
        self.assertEqual(s['geometry_count'],3630)
        self.assertEqual(s['coordinate_files_nominal'],5082)
        self.assertEqual(s['scenario_count'],54450)
        self.assertEqual(s['point_count_per_component'],1024)
    def test_B0_endpoints_and_no_duplicates(self):
        a=b_grid(CFG,'fine');self.assertEqual(len(a),121)
        self.assertAlmostEqual(a[0],.02);self.assertAlmostEqual(a[-1],.32)
        self.assertAlmostEqual(a[1]-a[0],.0025)
    def test_pilot_options(self):
        self.assertEqual(len(b_grid(CFG,'pilot')),16)
        self.assertTrue(all(0<x<1 for x in b_grid(CFG,'pilot')))
    def test_expected_link_components(self):
        for p,q in [(3,3),(3,6),(3,9),(6,15),(6,21),(6,9)]:
            pts=components(p,q,.16,256)
            self.assertEqual(len(pts),3)
            self.assertTrue(all(v.shape==(256,3) for v in pts))
            self.assertGreater(min_intercomponent_sampled_distance(pts),.02)
    def test_gauss_linking_references(self):
        for p,q in [(3,3),(3,6),(3,9),(6,15),(6,21),(6,9)]:
            a,b,*_=components(p,q,.16,512)
            self.assertAlmostEqual(gauss_pair(a,b),p*q/9,delta=.02)
    def test_distinct_component_point_sets(self):
        a,b,c=components(6,15,.08,256)
        self.assertFalse(np.allclose(a,b));self.assertFalse(np.allclose(b,c));self.assertFalse(np.allclose(c,a))
    def test_old_knot_formula_compatibility(self):
        p,q,b=2,3,.16
        t=np.arange(1024)*2*np.pi/1024
        expected=np.column_stack(((1+b*np.sin(q*t))*np.cos(p*t),(1+b*np.sin(q*t))*np.sin(p*t),b*np.cos(q*t)))
        np.testing.assert_allclose(sample_ruban(p,q,b,1024),expected,atol=1e-14)
    def test_link_rejected_by_single_knot_interface(self):
        with self.assertRaises(ValueError):sample_ruban(3,3,.16,1024)
    def test_global_shear_preserves_volume(self):
        pts=components(2,3,.16,256)[0];v=pushforward_affine_shear(pts,1.,.01,.005,2)
        s=1.01
        np.testing.assert_allclose(v[:,0],s*pts[:,0],rtol=0,atol=1e-15)
        np.testing.assert_allclose(v[:,1],pts[:,1]/s,rtol=0,atol=1e-15)
        jac=np.array([[s,0,0],[0,1/s,0],[.005*2*np.cos(2*pts[12,0]),0,1]])
        self.assertAlmostEqual(np.linalg.det(jac),1.,delta=1e-14)
    def test_perturbed_link_still_separated_sample(self):
        c=components(6,9,.16,512)
        d=[pushforward_affine_shear(v,1.,.01,.005,6) for v in c]
        self.assertGreater(min_intercomponent_sampled_distance(d),.10)
    def test_no_dynamics_claims(self):
        self.assertEqual(CFG['dynamics_run'],'NOT_EXECUTED')
        self.assertIn('KnotPlot',CFG['knotplot_source_status'])
    def test_duplicate_families_fail(self):
        c={**CFG,'families':CFG['families'][:1]*2}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):build(c,Path(d)/'x','pilot',dry_run=True)
    def test_smoke_build_and_manifest(self):
        c={**CFG,'families':[CFG['families'][0],CFG['families'][-1]],'pilot_B0':[.12,.16],
           'Lambda':[4.0],'delta_over_R0':[.025],'point_count':128}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new-output'
            s=build(c,p,'pilot')
            self.assertEqual(s['geometry_count'],4)
            idx=json.loads((p/'FAMILY_INDEX.json').read_text())
            self.assertEqual(idx['seed_count'],4)
            self.assertEqual([x['component_count'] for x in idx['seeds']],[1,1,3,3])
            for e in idx['seeds']:
                for comp in e['components']:
                    for key,hkey in [('xyz_path','sha256'),('perturbed_xyz_path','perturbed_sha256')]:
                        self.assertEqual(hashlib.sha256((p/comp[key]).read_bytes()).hexdigest(),comp[hkey])
            for ln in (p/'MANIFEST_SHA256.txt').read_text().splitlines():
                h,f=ln.split('  ',1)
                self.assertEqual(hashlib.sha256((p/f).read_bytes()).hexdigest(),h)
            with self.assertRaises(FileExistsError):build(c,p,'pilot')
    def test_source_not_counted_independent(self):
        self.assertEqual(count_summary(CFG,'fine')['independent_source_groups'],1)
    def test_params_not_physical_certifications(self):
        self.assertEqual(CFG['geometry_R0'],1)
        self.assertIn('NOT',CFG['dynamics_run'])
        self.assertFalse('ACCEPT' in CFG.get('catalog_policy',''))

if __name__=='__main__':unittest.main()
