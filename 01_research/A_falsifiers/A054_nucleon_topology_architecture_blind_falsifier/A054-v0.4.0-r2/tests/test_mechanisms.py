import numpy as np
from experiment.mechanisms import core_shell_raw, elastic_raw, make_context, injected_velocity

def circles(n=48):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return [np.c_[np.cos(t)+dx,np.sin(t),0*t] for dx in (-3,0,3)]
def test_fields_finite_and_context():
 cs=circles();cfg={'sigma_rep_core':1.5,'sigma_attr_core':4.0,'attraction_fraction':0.35};
 for fs in (core_shell_raw(cs,.04,cfg),elastic_raw(cs)): assert np.isfinite(np.vstack(fs)).all()
 ctx=make_context(cs,[1,1,1],.04,'CORE_ELASTIC',.5,cfg);v=injected_velocity(cs,[1,1,1],.04,ctx);assert np.isfinite(np.vstack(v)).all();assert ctx['scales']['CORE']>0 and ctx['scales']['ELASTIC']>0
