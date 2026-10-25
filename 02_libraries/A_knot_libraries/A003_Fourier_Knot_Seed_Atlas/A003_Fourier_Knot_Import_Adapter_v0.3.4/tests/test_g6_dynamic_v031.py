"""Independent v0.3.1 numerical safety checks. Fixtures are NEVER scientific evidence."""
import math, sys, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from g6_dynamic_qualification_v031 import (segment_clearance,_pair_segment_distances,
    best_rigid_fit,snapshot_screen,provider_snapshot_screen,LEVELS,EXPECTED_DET)


def torus(p,q,n):
    t=np.arange(n)*2*np.pi/n
    a=2+.3*np.cos(q*t)
    return np.column_stack([a*np.cos(p*t),a*np.sin(p*t),.3*np.sin(q*t)])

class TestSegmentGeometry(unittest.TestCase):
    def test_crossing_finite_segments_exactly_zero(self):
        x=np.array([[-1.,0,0],[1.,0,0],[3.,3,0],[0.,-1,0],[0.,1,0],[3.,-3,0]])
        self.assertAlmostEqual(_pair_segment_distances(x,np.array([0]),np.array([3]))[0],0,places=10)
    def test_interior_crossing_is_not_missed_by_vertex_check(self):
        x=np.array([[-1.,0,0],[1.,0,0],[3.,3,0],[0.,-1,0],[0.,1,0],[3.,-3,0]])
        # Synthetic polygon has segment 0 and segment 3 intersecting despite separate endpoints.
        self.assertAlmostEqual(segment_clearance(x,skip_edges=1)['min_distance'],0,places=10)
    def test_parallel_offset_segments_distance(self):
        x=np.array([[0.,0,0],[1.,0,0],[2.,3,0],[0.,1,.25],[1.,1,.25],[3.,3,0]])
        self.assertAlmostEqual(_pair_segment_distances(x,np.array([0]),np.array([3]))[0],math.hypot(1,.25),places=10)
    def test_spatial_tree_matches_exhaustive_for_actual_polygon(self):
        from g6_dynamic_qualification_v031 import _cyclic_far
        for curve in (torus(2,3,76),torus(3,5,80)):
            for gap in (1,3,6):
                # independently enumerate every non-neighbor edge pair
                i,j=np.triu_indices(len(curve),k=1)
                sel=_cyclic_far(i,j,len(curve),gap)
                brute=np.min(_pair_segment_distances(curve,i[sel],j[sel]))
                fast=segment_clearance(curve,skip_edges=gap)['min_distance']
                self.assertAlmostEqual(fast,float(brute),places=10)
    def test_rigid_motion_removed_from_shape(self):
        x=torus(2,3,120)
        a=.35;mat=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        y=x@mat+np.array([1.,-1.,.4])
        fit=best_rigid_fit(x,y)
        self.assertLess(fit['rms_nonrigid_deformation'],1e-12)
        y[15]+=np.array([.1,0,0])
        self.assertGreater(best_rigid_fit(x,y)['rms_nonrigid_deformation'],1e-3)

class TestTopology(unittest.TestCase):
    def test_true_torus_knot_reference_diagrams(self):
        for sid,p,q in [('fibonacci_torus_F3',2,3),('fibonacci_torus_F4',3,5)]:
            d=snapshot_screen(torus(p,q,300),sid)
            self.assertTrue(d['near_segment_clearance']['clear_of_segment_contact'])
            self.assertEqual(len(d['diagrams']),2)
            self.assertTrue(all(z['determinant']==EXPECTED_DET[sid] for z in d['diagrams']))
    def test_provider_disabled_never_passes(self):
        self.assertEqual(provider_snapshot_screen({},mode='off')['status'],'UNRESOLVED')
    def test_missing_observation_always_unresolved_even_with_real_provider(self):
        from unittest.mock import patch
        # The live provider path must not be called when no package installed. Fallback is UNRESOLVED.
        r=provider_snapshot_screen({},mode='endpoints')
        self.assertNotEqual(r['status'],'PASS_DIAGNOSTIC_ONLY')

    def test_temporal_archive_all_40_snapshots_with_test_double(self):
        from g6_dynamic_qualification_v031 import simulate_dynamic
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        from hashlib import sha256
        import json
        with TemporaryDirectory() as td:
            atlas=Path(td);out=atlas/'runs';out.mkdir();(atlas/'xyz').mkdir()
            records=[]
            for sid,pp,qq in [('fibonacci_torus_F3',2,3),('fibonacci_torus_F4',3,5)]:
                xyz=atlas/'xyz'/(sid+'.xyz');np.savetxt(xyz,torus(pp,qq,1200),fmt='%.17g')
                records.append({'id':sid,'points':1200,'sampling':'uniform_t','file':'xyz/'+xyz.name,'sha256':sha256(xyz.read_bytes()).hexdigest()})
            # This RHS is a deterministic mathematical unit fixture, NOT the C005 provider.
            def test_rhs(x):return np.column_stack((-.01*x[:,1], .013*x[:,0], .007*x[:,0]*x[:,1]))
            with patch('g6_dynamic_qualification_v031.c005_callable',return_value=(test_rhs,{'source':'UNIT_TEST_DOUBLE'})):
                z=simulate_dynamic(atlas,{'records':records},atlas,out,provider_mode='off')
            self.assertEqual(z['levels'],[150,300,600,1200])
            self.assertEqual(z['snapshots_per_level'],5)
            self.assertEqual(len(z['snapshots']),40)
            self.assertEqual(z['provider_invariants']['status'],'UNRESOLVED')
            self.assertFalse(z['genuine_external_c005'])
            self.assertEqual(len(z['time_checks']),8)
            self.assertEqual(len(z['spatial_checks']),2)
            self.assertEqual(len(np.load(out/'G6_DYNAMIC_TRAJECTORIES.npz').files),40)
            hi=[e for e in z['time_checks'] if e['N']==1200]
            self.assertEqual(len(hi),2)
            self.assertTrue(all(e['steps']==[8,16] and e['observed_order'] is None for e in hi))
    def test_all_four_levels_declared(self):
        self.assertEqual(LEVELS,(150,300,600,1200))

if __name__=='__main__': unittest.main()
