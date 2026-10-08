import numpy as np, pytest
from experiment.mechanisms import elastic_raw, _core_force_one
from experiment import native

def test_elastic_native_reference():
    if not native.available(): pytest.skip("native not built")
    t=np.linspace(0,2*np.pi,64,endpoint=False)
    c=np.c_[np.cos(t),np.sin(t),.1*np.sin(3*t)]
    a=elastic_raw([c])[0]
    b=native.elastic_raw_native(c)
    assert np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-15)<1e-10

def test_core_native_reference():
    if not native.available(): pytest.skip("native not built")
    t=np.linspace(0,2*np.pi,48,endpoint=False)
    a=np.c_[np.cos(t),np.sin(t),0*t]
    b=np.c_[1.7+0.7*np.cos(t),0.7*np.sin(t),0.08*np.sin(2*t)]
    comps=[a,b]
    core=0.04; sr=1.5; sa=4.0; chi=0.35
    ref=_core_force_one(0,comps,core,sigma_rep_core=sr,sigma_attr_core=sa,attraction_fraction=chi)
    got=native.core_force_native(a,[b],core,sr,sa,chi)
    assert np.linalg.norm(ref-got)/max(np.linalg.norm(ref),1e-15)<1e-10
