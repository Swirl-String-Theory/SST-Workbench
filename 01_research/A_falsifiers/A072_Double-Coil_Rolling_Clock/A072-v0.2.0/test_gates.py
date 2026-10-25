#!/usr/bin/env python3
"""Non-invasive verification of standalone numerical kernel/gauge controls."""
import unittest
import numpy as np
from rolling_clock import sample_source,A006,velocity,torus_phase,invariance_tests,rigid_normal_fit

def numpy_vlab_reference(X, gamma, a):
    # Independent vectorized translation of VortexLab velocityCore LIA+nonlocal self.
    prev=np.roll(X,1,axis=0);nxt=np.roll(X,-1,axis=0)
    dm=X-prev;dp=nxt-X
    lm=np.linalg.norm(dm,axis=1);lp=np.linalg.norm(dp,axis=1)
    lf=(gamma/(4*np.pi))*(np.log(2*np.sqrt(lm*lp)/(np.exp(.25)*a))+.1395)*2/(lm*lp*(lm+lp))
    local=lf[:,None]*np.cross(dm,dp)
    mid=(X+nxt)/2;dl=nxt-X
    r=X[:,None,:]-mid[None,:,:]
    d2=np.sum(r*r,axis=-1);idx=np.arange(len(X));d2[(idx[:,None]==idx[None,:])|(((idx[:,None]-1)%len(X))==idx[None,:])]=np.inf
    return local+gamma/(4*np.pi)*np.sum(np.cross(dl[None,:,:],r)/np.power(d2,1.5)[:,:,None],axis=1)

class Gates(unittest.TestCase):
 def test_source_kernel_vectorized_parity(self):
  x=sample_source(A006,96);a=.002
  ref=numpy_vlab_reference(x,1,a); got=velocity(x,1,a)
  rel=np.max(np.linalg.norm(ref-got,axis=1))/np.max(np.linalg.norm(ref,axis=1))
  self.assertLess(rel,1e-12)
 def test_invariance_bundle(self):
  a=invariance_tests();self.assertTrue(all(v<1e-9 for v in a.values()))
 def test_rigid_phase_vs_body_fit(self):
  x=sample_source(A006,192); a=.12;ct=np.cos(a);st=np.sin(a)
  mat=np.array([[ct,-st,0],[st,ct,0],[0,0,1.]])
  ph,_=torus_phase(x);ph2,_=torus_phase(x@mat.T)
  self.assertLess(abs(np.angle(np.exp(1j*(ph2-ph+3*a)))),1e-12)
  v=velocity(x,1,.002);U,om,res,cond=rigid_normal_fit(x,v)
  self.assertTrue(np.isfinite([*U,*om,res,cond]).all())
 def test_gamma_scaling(self):
  x=sample_source(A006,96)
  self.assertLess(np.max(np.abs(velocity(x,1.2,.002)-1.2*velocity(x,1,.002))),1e-10)
 def test_seed_closed_curve(self):
  x=sample_source(A006,96)
  self.assertEqual(len(x),96)
  self.assertTrue(np.min(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))>0)

if __name__=='__main__':unittest.main(verbosity=2)
