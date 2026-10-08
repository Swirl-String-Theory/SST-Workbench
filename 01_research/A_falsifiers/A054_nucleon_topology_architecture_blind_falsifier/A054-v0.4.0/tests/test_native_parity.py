import numpy as np, pytest
from experiment.mechanisms import elastic_raw
from experiment import native
def test_elastic_native_reference():
 if not native.available(): pytest.skip('native not built')
 t=np.linspace(0,2*np.pi,64,endpoint=False);c=np.c_[np.cos(t),np.sin(t),.1*np.sin(3*t)];a=elastic_raw([c])[0];b=native.elastic_raw_native(c); assert np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-15)<1e-10
