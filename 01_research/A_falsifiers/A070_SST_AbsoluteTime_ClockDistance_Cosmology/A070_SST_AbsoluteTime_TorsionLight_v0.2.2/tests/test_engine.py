import unittest, sys, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.blind_engine import classify,analyze,verify_lock,C,freeze_digest
class TestBlind(unittest.TestCase):
 def setUp(self):
  self.k=np.array(C['k_dimensionless']); self.a=np.array(C['angles_deg']); self.cos=np.abs(np.cos(np.deg2rad(self.a)))[:,None]
 def test_zero(self): self.assertEqual(classify(self.k,self.a,np.zeros((7,5)))['label'],'stationary')
 def test_reference_advection(self): self.assertEqual(classify(self.k,self.a,0.77*self.cos*self.k[None,:])['label'],'advective_reference')
 def test_reference_inertial(self): self.assertEqual(classify(self.k,self.a,1.1*np.broadcast_to(self.cos,(7,5)))['label'],'inertial_reference')
 def test_synthetic_positive_control(self): self.assertEqual(classify(self.k,self.a,0.9*np.broadcast_to(self.k[None,:],(7,5)))['label'],'synthetic_isotropic_linear')
 def test_mixed_unknown(self): self.assertEqual(classify(self.k,self.a,(0.42+0.31*self.k[None,:])*self.cos)['label'],'unknown')
 def test_all_angles_fixed(self): self.assertEqual(C['angles_deg'],[0,15,30,45,60,75,90])
 def test_k_grid_fixed(self): self.assertEqual(C['k_dimensionless'],[.25,.5,1,2,4])
 def test_zero_inertial_at_90(self): self.assertLess(abs(np.cos(np.deg2rad(90))),1e-12)
 def test_group_orthogonal(self):
  for theta in [15,30,45,60,75]:
   k=np.array([np.sin(np.deg2rad(theta)),0,np.cos(np.deg2rad(theta))]);Om=np.array([0,0,1.]);vg=2*(Om-(Om@k)*k)
   self.assertLess(abs(k@vg),1e-12)
 def test_truth_file_absent(self): self.assertFalse((ROOT/'reveal_truth.json').exists())
 def test_no_canonical_constants_in_code(self):
  code=(ROOT/'src'/'blind_engine.py').read_text().lower()
  for forbidden in ('1.09384563','1.40897017','299792458','theta=50','v_swirl'):
   self.assertNotIn(forbidden,code)
 def test_actual_blind_inputs(self): self.assertEqual(len(analyze()['outputs']),5)
 def test_freeze(self): self.assertEqual(verify_lock()['status'],'PASS')
if __name__=='__main__':unittest.main()
