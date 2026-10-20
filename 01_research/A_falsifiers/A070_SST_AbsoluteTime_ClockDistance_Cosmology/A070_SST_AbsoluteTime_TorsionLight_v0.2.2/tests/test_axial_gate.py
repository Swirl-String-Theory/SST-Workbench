import unittest,sys, numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.axial_gate import inertial_omega_group, axial_null_phase,check_axial,estimate_time_phase,classify,analyze,verify,C
class TestAxialGate(unittest.TestCase):
 def test_true_axial(self): self.assertTrue(check_axial([0,0,3])); self.assertFalse(check_axial([0.01,0,3]))
 def test_inertial_axial_group_is_zero(self):
  w,vg=inertial_omega_group([0,0,2],Omega=1.3)
  self.assertAlmostEqual(w,2.6);np.testing.assert_allclose(vg,np.zeros(3),atol=1e-14)
 def test_perpendicular_k_has_zero_inertial_frequency_but_axial_group(self):
  w,vg=inertial_omega_group([2,0,0],Omega=1.3)
  self.assertAlmostEqual(w,0.);np.testing.assert_allclose(vg,[0,0,1.3],atol=1e-14)
 def test_group_orthogonal_to_wavevector(self):
  for ang in [0,15,30,45,60,75,90]:
   v=np.array([np.sin(np.deg2rad(ang)),0,np.cos(np.deg2rad(ang))])
   w,g=inertial_omega_group(v)
   self.assertLess(abs(np.dot(v,g)),1e-12)
 def test_quiescent_azimuthal_not_propagating(self):
  t=np.linspace(0,10,100);z=np.linspace(0,2*np.pi,128,endpoint=False)
  data=axial_null_phase(z,t,2,U=0.)
  np.testing.assert_allclose(data[0],data[-1],atol=1e-14)
 def test_advection_no_intrinsic_propagation(self):
  t=np.linspace(0,7,120);z=np.linspace(0,2*np.pi,128,endpoint=False);U=.42
  s=np.array([axial_null_phase(z,t,int(k),U)[:,0] for k in [1,2,3,4]])
  w=estimate_time_phase(s,t)
  np.testing.assert_allclose(w/np.array([1,2,3,4]),U,atol=1e-12)
  self.assertEqual(classify([1,2,3,4],w,U)['classification'],'passive_advection')
 def test_positive_control_is_not_claimed_euler(self):
  w=.8*np.array([1,2,3,4]);r=classify([1,2,3,4],w,0.)
  self.assertEqual(r['classification'],'propagation_signature_unqualified')
 def test_fixed_axial_geometry(self):self.assertEqual(C['geometry']['theta_k_to_axis_degrees'],0)
 def test_no_canonical_in_axial_code(self):
  s=(ROOT/'src'/'axial_gate.py').read_text()
  for token in ('1.09384563','1.40897017','299792458','50 degree','v_swirl'):
   self.assertNotIn(token,s)
 def test_legacy_lock_preserved(self):
  from src.blind_engine import verify_lock
  self.assertEqual(verify_lock()['status'],'PASS')
 def test_axial_data_masked(self):self.assertEqual(len(analyze()['results']),4)
 def test_axial_lock(self):self.assertEqual(verify()['status'],'PASS')
