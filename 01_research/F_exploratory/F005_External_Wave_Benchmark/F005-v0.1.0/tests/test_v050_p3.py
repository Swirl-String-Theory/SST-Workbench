import sys,unittest,math,tempfile,os
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'data'))
from f005_euler_v050 import coefficients,simulate
import f005_v050_p3 as p

class Tests(unittest.TestCase):
 def setUp(self):
  self.co=coefficients(.08,.043,.04,998.,0.,9.81,4)
 def test_four_frequencies_from_thesis(self):
  np.testing.assert_allclose(self.co[1],[18.9684,33.9944,43.8884,51.9294],rtol=1e-5)
 def test_dimension_of_state(self):
  self.assertEqual(len(self.co[1])*2,8)
 def test_thirteen_scenarios(self):
  self.assertEqual(len(list(p.scenarios(self.co))),13)
 def test_two_samples_reproduced_nonzero_forcing(self):
  a=np.array([1.0,-.25]);ya=np.array([.001,-.0004]);yp=np.array([.0008,.0002]);
  q,v=p.seed_modes_two_heights(yp,ya,a,self.co)
  np.testing.assert_allclose(q@self.co[2],ya,atol=1e-12,rtol=0)
  np.testing.assert_allclose(p.past_observed_height(q,v,a,self.co),yp,atol=1e-12,rtol=0)
 def test_nonunique_initial_state(self):
  a=np.array([.5]);ya=np.array([.001]);yp=np.array([.0007]);
  q1,v1=p.seed_modes_two_heights(yp,ya,a,self.co)
  q2,v2=p.seed_modes_two_heights(yp,ya,a,self.co,high_q=[.0002,0,0])
  self.assertGreater(np.max(abs(q1-q2)),1e-5)
  self.assertAlmostEqual(float((q2@self.co[2])[0]),float(ya[0]),places=11)
  self.assertAlmostEqual(float(p.past_observed_height(q2,v2,a,self.co)[0]),float(yp[0]),places=11)
 def test_seed_independence_forecast(self):
  a=np.zeros((1,1500));ya=np.array([.001]);yp=np.array([.0007]);pr=np.array([0.]);
  q,v=p.seed_modes_two_heights(yp,ya,pr,self.co)
  hi,vi=p.seed_modes_two_heights(yp,ya,pr,self.co,high_q=[.0002,0,0])
  t1=simulate(a,.004,self.co,q0=q,v0=v)[0]
  t2=simulate(a,.004,self.co,q0=hi,v0=vi)[0]
  self.assertAlmostEqual(t1[0],t2[0],places=12)
  self.assertGreater(abs(t1[250]-t2[250]),1e-6)
 def test_analytic_delta_equals_direct_forecast(self):
  a=np.zeros((1,1500));ya=np.array([0.]);yp=np.array([0.]);z=np.array([0.]);
  dq,dv=p.seed_modes_two_heights(yp,ya,z,self.co,high_q=[.00025/self.co[2][1],0,0])
  sim=simulate(a,.004,self.co,q0=dq,v0=dv)[0]
  analytic=p.homogeneous_delta(np.arange(1500)*.004,self.co,dq[0],dv[0])
  np.testing.assert_allclose(sim,analytic,atol=1e-12,rtol=0)
 def test_scoring(self):
  path,endpoint=p.score(np.array([[.001,.002]]),np.zeros((1,2)))
  self.assertAlmostEqual(path,math.sqrt(2.5),places=11);self.assertAlmostEqual(endpoint,2.0)
 def test_reject_bad_geometry(self):
  G={'tank_length_internal_m':.080,'tank_width_internal_m':.031,'fill_depth_m':.043,'sensor_x_from_center_m':.040,'liquid_density_kg_m3':998.,'surface_tension_N_m':0.,'gravity_m_s2':9.81,'n_modes':4,'assumption_2d_longitudinal':True,'provenance_confirmed':False,'initial_equilibrium_confirmed':False,'acceleration_axis_sign':None,'measurement_height_sign':None}
  p.geometry_development(G)
  G['fill_depth_m']=.044
  with self.assertRaises(ValueError):p.geometry_development(G)
 def test_p2_bounded(self):
  state={'status':'E0_P2_REVIEW_NOT_CERTIFIED','locked_split':{'status':'LOCKED_INPUT_ONLY_SPLIT_VERIFIED'},'gates':dict(p.P2_REQUIRED_GATES,**{'E0_MAIN_EULER_GATE':'BLOCKED','P2_HYDRODYNAMIC_REST':'BLOCKED_NOT_OBSERVABLE_FROM_SCALAR_TRACE'})}
  p.audit_p2(state)
  state['gates']['E0_MAIN_EULER_GATE']='PASS'
  with self.assertRaises(AssertionError):p.audit_p2(state)
 def test_fail_closed_no_real_data(self):
  with tempfile.TemporaryDirectory() as d:
   r=p.run(Path(d),Path(d)/'out')
   self.assertEqual(r['status'],'BLOCKED_FAIL_CLOSED')
   self.assertFalse(r['test_ood_water_height_read'])
 def test_synthetic_end_to_end(self):
  with tempfile.TemporaryDirectory() as d:
   r=p.run(Path(d),Path(d)/'out',demo=True)
   self.assertEqual(r['status'],'DEMO_SYNTHETIC_NO_EXPERIMENTAL_VALIDATION',r.get('blocker'))
   out=Path(d)/'out'
   with (out/'p3_conditional_metrics.csv').open() as f:
    self.assertEqual(len(list(__import__('csv').DictReader(f))),15)
   with (out/'p3_initial_state_sensitivity.csv').open() as f:
    self.assertEqual(len(list(__import__('csv').DictReader(f))),195)
   with (out/'p3_initial_state_envelopes.csv').open() as f:
    self.assertEqual(len(list(__import__('csv').DictReader(f))),15)
   self.assertTrue((out/'F005_v0.5.0-p3_LINEAR_EULER_DEVELOPMENT.pdf').is_file())

if __name__=='__main__':unittest.main()
