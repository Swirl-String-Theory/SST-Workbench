import numpy as np
from src.topology3d import knot_signature,gauss_link,min_curve_distance,min_nonlocal_self_distance

def rings(n=160):
 t=np.linspace(0,2*np.pi,n,endpoint=False)
 a=np.array([np.cos(t),np.sin(t),0*t]).T
 b=np.array([0.5+0*t,0.6+0.7*np.cos(t),0.7*np.sin(t)]).T
 return a,b

def test_knot_determinants():
 t=np.linspace(0,2*np.pi,160,endpoint=False)
 circle=rings()[0]
 trefoil=np.array([(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]).T
 figure8=np.array([(2+np.cos(2*t))*np.cos(3*t),(2+np.cos(2*t))*np.sin(3*t),np.sin(4*t)]).T
 for curve,expected in ((circle,1),(trefoil,3),(figure8,5)):
  s=knot_signature(curve)
  assert s['status']=='QUALIFIED'
  assert s['alexander_det_at_minus_one']==expected

def test_gauss_link_and_disjointness():
 a,b=rings()
 assert abs(gauss_link(a,b,3)+1)<0.0001
 assert abs(gauss_link(a,b+np.array([2,0,0]),3))<0.001
 assert min_curve_distance(a,b)>0.05
 assert min_nonlocal_self_distance(a)>0.01

def test_orientation_reverses_link():
 a,b=rings()
 assert abs(gauss_link(a,b,3)+gauss_link(a,b[::-1],3))<1e-7
