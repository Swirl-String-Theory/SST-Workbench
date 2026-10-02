import numpy as np
from helmholtz_sst.metrics import total_velocity,relative_equilibrium,orientation_symmetry,mirror_symmetry

def circle(n=128,R=2.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[R*np.cos(t),R*np.sin(t),np.zeros(n)]
def perturb(n=128,R=2.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);r=R*(1+.2*np.cos(3*t));return np.c_[r*np.cos(t),r*np.sin(t),.15*np.sin(2*t)]
def test_ring_is_relative_equilibrium_better_than_perturbation():
    a=.15;p=circle();q=perturb();rp=relative_equilibrium([p],total_velocity([p],a,'softcore',0))['normal_nrmse'];rq=relative_equilibrium([q],total_velocity([q],a,'softcore',0))['normal_nrmse'];assert rp<0.08;assert rq>rp+0.02
def test_orientation_and_mirror_symmetry_python():
    p=circle(96);assert orientation_symmetry([p],.15,'softcore',0)<1e-11;assert mirror_symmetry([p],.15,'softcore',0)<1e-11
