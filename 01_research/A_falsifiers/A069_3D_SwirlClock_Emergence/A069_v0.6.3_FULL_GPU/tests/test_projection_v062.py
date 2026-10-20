import numpy as np
from a069_v061.projection_topology_v062 import numerical_projection_audit,determinant

def test_torus_T23_static_projection():
    t=np.linspace(0,2*np.pi,320,endpoint=False)
    pts=np.stack([(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)],axis=1)
    z=numerical_projection_audit(pts)
    assert z['common_determinant']==3
    assert z['one_projection_three_crossing_trefoil']
    assert not z['topology_certified']

def test_unknot_circle():
    t=np.linspace(0,2*np.pi,120,endpoint=False)
    pts=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])
    z=numerical_projection_audit(pts)
    assert z['common_determinant']==1
    assert not z['topology_certified']

def test_empty_fails():
    assert numerical_projection_audit(None)['status']=='UNRESOLVED_NO_VALID_POLYGON'
