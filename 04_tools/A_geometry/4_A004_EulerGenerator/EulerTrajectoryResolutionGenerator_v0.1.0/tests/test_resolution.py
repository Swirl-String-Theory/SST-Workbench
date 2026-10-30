from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from resolver.adapters import Adapter,PINS
from resolver.run import GRID_PROFILES,rk4_shared,estimate_gib,sha_payload

def test_profiles():assert GRID_PROFILES==(48,64,80,96)
def test_ordered_memory_warning():assert estimate_gib(96)>estimate_gib(48)
def test_sha_canonical():assert sha_payload({'a':1})==sha_payload({'a':1})

class Flow:
    def proj(self,x):return x
    def rhs(self,x):return 0*x
    def interp(self,uh,x):return np.tile(np.array([[1.,-2.,0.5]]),(len(x),1))

def test_constant_flow_rk4():
    f=Flow();uh=np.zeros(2);x=np.zeros((3,3));u,y=rk4_shared(f,uh,x,.1)
    np.testing.assert_allclose(y,np.tile([.1,-.2,.05],(3,1)),atol=1e-14)

def test_pinned_source_inventory():
    assert len(PINS['a075'])==len(PINS['a077'])==2

def test_trilinear_periodic_undwrap():
    class Fake:
        provider='a077';L=8.;dx=1.;sim=SimpleNamespace(n=8)
        def physical_velocity(self,uh):
            grid=np.zeros((8,8,8,3));grid[...,0]=3.0
            return grid
    pts=np.array([[0.,0.,0.],[13.,-42.,2.5]])
    np.testing.assert_allclose(Adapter.interp(Fake(),None,pts),np.array([[3.,0.,0.]]*2))
