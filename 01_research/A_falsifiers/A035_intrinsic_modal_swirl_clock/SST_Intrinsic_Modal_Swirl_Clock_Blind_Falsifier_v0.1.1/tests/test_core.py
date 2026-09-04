import numpy as np
from sst_modal_clock.geometry import synthetic_trefoil,resample_closed,normalize,broadband_probe,kabsch_align
from sst_modal_clock.modal import recurrence_metrics,learn_modes,project

def test_probe_normalized():
 x,_=normalize(resample_closed(synthetic_trefoil(),64));p=broadband_probe(x);assert abs(np.sqrt(np.mean(np.sum(p*p,axis=1)))-1)<1e-12
def test_kabsch():
 x,_=normalize(resample_closed(synthetic_trefoil(),64)); R=np.array([[0,-1,0],[1,0,0],[0,0,1.]]);y=kabsch_align(x@R,x);assert np.mean((x-y)**2)<1e-20
def test_modal_recurrence():
 t=np.linspace(0,12*np.pi,241);phi=np.zeros((32,3));phi[:,0]=np.cos(2*np.pi*np.arange(32)/32);phi/=np.linalg.norm(phi);resp=np.sin(t)[:,None,None]*phi[None];m,e=learn_modes(resp,96,2);a=project(resp,m)[:,0];r=recurrence_metrics(t[96:],a[96:]);assert r['cycles']>2 and r['harmonic_r2']>.9
def test_mode_discovery_energy():
 t=np.linspace(0,4*np.pi,100);phi=np.zeros((16,3));phi[:,1]=1/4;resp=np.sin(t)[:,None,None]*phi[None];m,e=learn_modes(resp,40,2);assert e[0]>.99
