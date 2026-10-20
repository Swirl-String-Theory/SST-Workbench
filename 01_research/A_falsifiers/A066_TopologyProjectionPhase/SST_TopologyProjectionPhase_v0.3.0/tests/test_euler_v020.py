import numpy as np
from src.euler import diagnose_velocity_grid,diagnose_vertex_transport

def grids():
 return (np.linspace(0,1,5),)+(tuple(np.linspace(-1,1,7) for _ in range(3)))

def test_rotation_exact_steady_euler():
 t,x,y,z=grids();u=np.zeros((len(t),len(x),len(y),len(z),3))
 u[...,0]=-y[None,None,:,None]
 u[...,1]=x[None,:,None,None]
 r=diagnose_velocity_grid(t,x,y,z,u)
 assert r['pass_screen']
 assert r['omega_rms_per_s']>1
 assert r['divergence_rms_per_s']<1e-12
 assert r['euler_vorticity_residual_rms_per_s2']<1e-12

def test_divergent_field_rejected():
 t,x,y,z=grids();u=np.zeros((len(t),len(x),len(y),len(z),3))
 u[...,0]=x[None,:,None,None]
 u[...,1]=y[None,None,:,None]
 u[...,2]=z[None,None,None,:]
 r=diagnose_velocity_grid(t,x,y,z,u)
 assert not r['pass_screen']
 assert abs(r['divergence_rms_per_s']-3)<1e-11

def test_material_identifier_requirement():
 t=np.arange(5,dtype=float);p=np.zeros((5,1,16,3));a=np.ones((5,1),dtype=bool)
 u=np.zeros_like(p)
 assert diagnose_vertex_transport(t,p,a,u)['status']=='UNRESOLVED_NO_MATERIAL_IDENTITIES'
 assert diagnose_vertex_transport(t,p,a,u,['id0'])['relative_residual']==0
