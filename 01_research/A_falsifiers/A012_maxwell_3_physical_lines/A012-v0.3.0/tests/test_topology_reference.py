import numpy as np
from sst_maxwell3_blind.pklsa_adapter import linking_number_exact_python
from sst_maxwell3_blind.native import circulation_from_centerlines, mutual_helicity_from_components

def circle_xy(n=400,r=1.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False); return np.c_[r*np.cos(t),r*np.sin(t),np.zeros_like(t)]

def hopf_pair(n=400):
    a=circle_xy(n,1.0); t=np.linspace(0,2*np.pi,n,endpoint=False)
    b=np.c_[1.0+0.35*np.cos(t),np.zeros_like(t),0.35*np.sin(t)]
    return a,b

def test_exact_hopf_linking():
    a,b=hopf_pair(240); lk=linking_number_exact_python(a,b)
    assert abs(abs(lk)-1.0)<2e-6

def test_biot_savart_circulation_matches_linking_python():
    a,b=hopf_pair(320); lk=linking_number_exact_python(a,b)
    q,_=circulation_from_centerlines([a],b,1.0,0.0,threads=1,force_python=True)
    assert abs(q-lk)<0.03

def test_mutual_helicity_matches_2lk_python():
    a,b=hopf_pair(280); lk=linking_number_exact_python(a,b)
    h,_=mutual_helicity_from_components([a,b],[1.0,1.0],threads=1,force_python=True)
    assert abs(h-2*lk)<0.05
