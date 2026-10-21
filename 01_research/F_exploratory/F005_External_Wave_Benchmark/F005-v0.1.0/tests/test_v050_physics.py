import importlib.util, unittest, math, json, tempfile
from pathlib import Path
import numpy as np
path=Path(__file__).resolve().parents[1]/'data'/'f005_euler_v050.py'
spec=importlib.util.spec_from_file_location('v050',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Physics(unittest.TestCase):
 def setUp(self):
  self.L=.12;self.h=.025;self.g=9.80665;self.rho=998.;self.dt=.004
 def co(self,n=1,x=None,sigma=0):return m.coefficients(self.L,self.h,self.L/2 if x is None else x,self.rho,sigma,self.g,n)
 def test_shallow(self):
  k,w,_,_=self.co();self.assertAlmostEqual(w[0]**2,self.g*k[0]*np.tanh(k[0]*self.h),places=12)
  kk=m.coefficients(.12,1e-5,0,998,0,self.g,1)[1][0]
  self.assertAlmostEqual(kk**2,self.g*(math.pi/.12)**2*1e-5,delta=1e-5)
 def test_deep(self):
  k,w,_,_=m.coefficients(self.L,1.,0,self.rho,0,self.g,1)
  self.assertAlmostEqual(w[0]**2,self.g*k[0],places=10)
 def test_surface_tension_increases(self):self.assertGreater(self.co(sigma=.072)[1][0],self.co()[1][0])
 def test_centre_anti_symmetry(self):
  self.assertTrue(np.allclose(self.co(n=4,x=0)[2],0,atol=1e-15))
  self.assertTrue(np.allclose(self.co(n=4,x=.035)[2],-self.co(n=4,x=-.035)[2]))
 def test_zero_forcing_zero_initial(self):
  a=np.zeros((2,31));self.assertTrue(np.allclose(m.simulate(a,self.dt,self.co(3)),0))
 def test_exact_constant_step(self):
  co=self.co(1);a=np.full((1,501),.2);y=m.simulate(a,self.dt,co)[0];w=co[1][0];F=co[3][0]*.2;shape=co[2][0]
  pred=(F/w**2)*(1-np.cos(w*np.arange(501)*self.dt))*shape
  self.assertLess(np.max(abs(y-pred)),1e-12)
 def test_static_tilt(self):
  co=self.co(101);w=co[1];shape=co[2];F=co[3];qeq=F/w**2
  approx=np.sum(qeq*shape);exact=-self.L/2/self.g
  self.assertAlmostEqual(approx,exact,delta=abs(exact)*.005)
 def test_later_height_not_used(self):
  a=np.zeros((1,100));co=self.co(1)
  y1=np.zeros((1,100));y2=y1.copy();y2[0,50]=90
  # The forward solution depends only on forcing and declared initial state.
  self.assertTrue(np.array_equal(m.simulate(a,self.dt,co),m.simulate(a,self.dt,co)))
 def test_condition_only_two_heights(self):
  co=self.co(1);q,v=m.initial_condition_one_mode(np.array([2.]),np.array([3.]),self.dt,co[2],1)
  self.assertAlmostEqual(float(q[0,0]),.003);self.assertAlmostEqual(float(v[0,0]),.25)
  with self.assertRaises(ValueError):m.initial_condition_one_mode(np.array([2.]),np.array([3.]),self.dt,self.co(2)[2],1)
 def test_geo_fail_closed(self):
  p=path.parent.parent/'config'/'EULER_GEOMETRY_REQUIRED.json';g=json.loads(p.read_text())
  with self.assertRaisesRegex(ValueError,'GEOMETRY_UNVERIFIED'):m.validate_geometry(g)
 def test_split_exact_lock(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'split.csv';p.write_text('row_id_zero_based,partition,proxy_component_id\n0,DEV_VALIDATION,x\n')
   with self.assertRaisesRegex(ValueError,'LOCKED_SPLIT_HASH_MISMATCH'):m.load_split(p)
 def test_blocked_real_without_source(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);st=m.run(p,p/'config_nonexistent.json',p/'o')
   self.assertIn('BLOCKED',st['scientific_status'])
   self.assertTrue((p/'o/v050_report.json').is_file())
   self.assertFalse((p/'o/euler_geometry_only_metrics.csv').exists())
 def test_demo_is_explicitly_not_experiment(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);st=m.run(p,p/'ignored',p/'demo',demo=True)
   self.assertEqual(st['scientific_status'],'DEMO_SYNTHETIC_NOT_EXPERIMENT')
   self.assertTrue((p/'demo/F005_v0.5.0_LINEAR_EULER_DEVELOPMENT.pdf').is_file())
 def test_dimensional_scaling_steady(self):
  co=self.co(1);tt=.006;a=np.array([[.2]*200]);
  y=m.simulate(a,tt,co)
  y2=m.simulate(a*2,tt,co)
  self.assertTrue(np.allclose(y2,2*y,atol=1e-13))

if __name__=='__main__':unittest.main()
