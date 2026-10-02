import numpy as np
from sst_modal_clock.geometry import synthetic_trefoil,resample_closed,normalize,broadband_probe,kabsch_align,tangential_redistribution_velocity
from sst_modal_clock.modal import recurrence_metrics,learn_modes,project

def test_probe_normalized():
 x,_=normalize(resample_closed(synthetic_trefoil(),64));p=broadband_probe(x);assert abs(np.sqrt(np.mean(np.sum(p*p,axis=1)))-1)<1e-12

def test_kabsch():
 x,_=normalize(resample_closed(synthetic_trefoil(),64)); R=np.array([[0,-1,0],[1,0,0],[0,0,1.]]);y=kabsch_align(x@R,x);assert np.mean((x-y)**2)<1e-20

def test_modal_multi_return_recurrence():
 t=np.linspace(0,16*np.pi,401);phi=np.zeros((32,3));phi[:,0]=np.cos(2*np.pi*np.arange(32)/32);phi/=np.linalg.norm(phi);resp=np.sin(.91*t)[:,None,None]*phi[None];m,e,c=learn_modes(resp,80,2);a=project(resp,m,c)[:,0];r=recurrence_metrics(t[80:],a[80:],4);assert r['cycles']>5 and r['harmonic_r2']>.9 and r['multi_return_closure_median']<.25 and r['n_return_closures']>=3

def test_mode_discovery_energy():
 t=np.linspace(0,4*np.pi,100);phi=np.zeros((16,3));phi[:,1]=1/4;resp=np.sin(t)[:,None,None]*phi[None];m,e,c=learn_modes(resp,40,2);assert e[0]>.99

def test_redistribution_is_tangent_only():
 th=np.linspace(0,2*np.pi,64,endpoint=False); ph=th+.25*np.sin(th); x=np.c_[np.cos(ph),np.sin(ph),np.zeros_like(ph)]; v=tangential_redistribution_velocity(x,2.0); t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]; leak=np.linalg.norm(v-(v*t).sum(1)[:,None]*t)/max(np.linalg.norm(v),1e-15);assert leak<1e-12
